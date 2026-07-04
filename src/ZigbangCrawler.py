# -*- coding: utf-8 -*-
"""
직방(Zigbang) 크롤러
- 아파트 단지 검색 및 현재 매매/전세/월세 매물 조회
- 법원경매 물건과 단지명/면적 기준 매칭 후 시세 비교
"""
import re
import json
import requests
import pandas as pd


class ZigbangCrawler:
    SEARCH_URL = "https://apis.zigbang.com/search"
    DANJI_DETAIL_URL = "https://www.zigbang.com/home/apt/danjis/{danji_id}"

    TRAN_TYPE_MAP = {"trade": "매매", "lease": "전세", "rent": "월세"}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    def search_complex(self, query: str) -> list:
        """단지명/주소로 검색해 아파트 단지 후보 목록 반환"""
        r = self.session.get(self.SEARCH_URL, params={
            "q": query, "serviceType": "zigbang", "page": 1, "size": 10,
        }, timeout=10)
        r.raise_for_status()
        data = r.json()

        results = []
        for item in data.get("items", []):
            if item.get("type") != "apartment":
                continue
            source = item.get("_source", {})
            results.append({
                "danji_id": item["id"],
                "danji_name": item.get("name"),
                "address": source.get("주소") or source.get("address2", ""),
                "lat": item.get("lat"),
                "lng": item.get("lng"),
                "household": source.get("household"),
            })
        return results

    def get_danji_items(self, danji_id) -> pd.DataFrame:
        """단지 상세페이지(SSR 데이터)에서 현재 매매/전세/월세 매물 목록을 추출"""
        r = self.session.get(self.DANJI_DETAIL_URL.format(danji_id=danji_id), timeout=10)
        r.raise_for_status()

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            return pd.DataFrame()

        next_data = json.loads(m.group(1))
        catalog = (next_data.get("props", {})
                            .get("pageProps", {})
                            .get("SSRData", {})
                            .get("itemCatalog", {}))
        items = catalog.get("list", [])
        if not items:
            return pd.DataFrame()

        df = pd.DataFrame(items)
        df = df.rename(columns={
            "tranType": "zigbang_거래유형",
            "areaDanjiName": "zigbang_단지명",
            "sizeM2": "zigbang_전용면적",
            "sizeContractM2": "zigbang_계약면적",
            "depositMin": "zigbang_가격_만원",
            "rentMin": "zigbang_월세_만원",
            "dong": "zigbang_동",
            "floor": "zigbang_층",
            "itemTitle": "zigbang_제목",
        })
        df["zigbang_거래유형"] = df["zigbang_거래유형"].map(self.TRAN_TYPE_MAP).fillna(df["zigbang_거래유형"])

        keep_cols = ["zigbang_거래유형", "zigbang_단지명", "zigbang_전용면적", "zigbang_계약면적",
                     "zigbang_가격_만원", "zigbang_월세_만원", "zigbang_동", "zigbang_층", "zigbang_제목"]
        return df[[c for c in keep_cols if c in df.columns]]

    def close(self):
        self.session.close()


def parse_apt_name_from_court_address(court_address: str):
    """법원경매 물건주소의 괄호 부분에서 (동명,단지명) 추출"""
    m = re.search(r'\(([^,()]+),\s*([^)]+)\)', court_address)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def parse_court_price(price_str) -> float:
    """'1,536,000,000 (80%)' 또는 '1,536,000,000' → 만원 단위 숫자"""
    if price_str is None:
        return None
    m = re.search(r'[\d,]+', str(price_str))
    if not m:
        return None
    return float(m.group().replace(',', '')) / 10000


def compare_court_with_zigbang(crawler: ZigbangCrawler, court_row: dict, area_tolerance_m2: float = 3.0) -> dict:
    """
    법원경매 물건 1건을 직방 단지 매물과 매칭해 시세 비교

    Args:
        crawler: ZigbangCrawler 인스턴스
        court_row: 법원경매 데이터 1행 (사건번호/물건주소/감정가/최저가 컬럼 필요)
        area_tolerance_m2: 전용면적 매칭 허용 오차(㎡)

    Returns:
        dict: 비교 결과 (court_*, zigbang_danji_id, zigbang_items(DataFrame))
    """
    address = court_row.get('물건주소', '')
    dong, apt_name = parse_apt_name_from_court_address(address)
    if not apt_name:
        raise ValueError(f"물건주소에서 단지명을 찾을 수 없음: {address}")

    area_m = re.search(r'\[.*?(\d+(?:\.\d+)?)\s*㎡', address)
    court_area = float(area_m.group(1)) if area_m else None

    candidates = crawler.search_complex(apt_name)
    if not candidates:
        raise ValueError(f"직방에서 단지를 찾을 수 없음: {apt_name}")
    danji = next((c for c in candidates if dong and dong in (c.get('address') or '')), candidates[0])

    items = crawler.get_danji_items(danji['danji_id'])
    if not items.empty and court_area is not None:
        items = items[(items['zigbang_전용면적'] - court_area).abs() <= area_tolerance_m2].reset_index(drop=True)

    return {
        'court_사건번호': court_row.get('사건번호'),
        'court_물건주소': address,
        'court_단지명': apt_name,
        'court_전용면적': court_area,
        'court_감정가_만원': parse_court_price(court_row.get('감정가')),
        'court_최저가_만원': parse_court_price(court_row.get('최저가')),
        'zigbang_danji_id': danji['danji_id'],
        'zigbang_items': items,
    }


def print_comparison(result: dict):
    print(f"사건번호: {result['court_사건번호']}")
    print(f"물건주소: {result['court_물건주소']}")
    print(f"단지명(직방 danji_id={result['zigbang_danji_id']}): {result['court_단지명']}")
    print(f"전용면적: {result['court_전용면적']}㎡")
    print(f"감정가: {result['court_감정가_만원']:,.0f}만원")
    print(f"최저가: {result['court_최저가_만원']:,.0f}만원")
    print()

    items = result['zigbang_items']
    if items.empty:
        print("직방에 매칭되는 현재 매물이 없습니다 (동일 면적대 매매/전세 매물 없음)")
        return

    for tran_type in ['매매', '전세', '월세']:
        sub = items[items['zigbang_거래유형'] == tran_type]
        if sub.empty:
            print(f"[{tran_type}] 현재 매물 없음")
            continue
        print(f"[{tran_type}] {len(sub)}건 - "
              f"{sub['zigbang_가격_만원'].min():,.0f} ~ {sub['zigbang_가격_만원'].max():,.0f}만원 "
              f"(평균 {sub['zigbang_가격_만원'].mean():,.0f}만원)")
        if tran_type == '매매' and result['court_최저가_만원']:
            avg = sub['zigbang_가격_만원'].mean()
            ratio = (result['court_최저가_만원'] - avg) / avg * 100
            print(f"  → 경매 최저가는 매매 평균 시세 대비 {ratio:+.1f}%")


if __name__ == "__main__":
    c = ZigbangCrawler()
    try:
        test_row = {
            '사건번호': '서울중앙지방법원 2022타경891 2022타경108054 (중복)',
            '물건주소': '서울특별시 동작구 상도로 346-1 106동 9층902호 (상도동,힐스테이트상도센트럴파크) '
                     '[집합건물 철근콘크리트구조 118.2086㎡]',
            '감정가': '1,920,000,000',
            '최저가': '1,536,000,000 (80%)',
        }
        result = compare_court_with_zigbang(c, test_row)
        print_comparison(result)
    finally:
        c.close()
