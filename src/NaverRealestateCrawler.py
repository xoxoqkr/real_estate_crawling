# -*- coding: utf-8 -*-
"""
네이버 부동산(new.land.naver.com) 크롤러

기존 NaverRealestateCrawling.py(레거시)는 브라우저에서 수동으로 복사한
쿠키/Bearer 토큰을 코드에 박아두고 썼기 때문에 몇 시간 뒤면 만료되어 못 썼다.

이 모듈은 new.land.naver.com 홈페이지를 비로그인 상태로 방문할 때
서버가 응답 HTML에 직접 심어주는 게스트용 Bearer 토큰(`window.App.state.token.token`,
`isLogin: false`, 유효기간 약 3시간)을 매번 새로 추출해서 쓴다.
따라서 로그인/쿠키 하드코딩이 전혀 필요 없다.
"""
import re
import json
import time
import base64
import requests
import pandas as pd


class NaverRealestateCrawler:
    BASE = "https://new.land.naver.com"
    TOKEN_REFRESH_MARGIN_SEC = 60  # 만료 임박 시 미리 재발급

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })
        self._token = None
        self._token_exp = 0

    @staticmethod
    def _extract_balanced_json(text: str, marker: str):
        """`marker{...}` 형태로 임베드된 JSON을 중괄호 균형을 맞춰 추출 (정규식 non-greedy로는 중첩 구조를 못 자름)"""
        idx = text.find(marker)
        if idx == -1:
            return None
        start = text.find("{", idx)
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    def _refresh_token(self):
        """홈페이지 방문 시 발급되는 비로그인 게스트 토큰을 추출"""
        r = self.session.get(f"{self.BASE}/", timeout=10)
        r.raise_for_status()
        raw = self._extract_balanced_json(r.text, "window.App=")
        if not raw:
            raise RuntimeError("네이버 부동산 홈페이지에서 인증 토큰을 찾지 못함 (페이지 구조가 바뀌었을 수 있음)")

        app_state = json.loads(raw)
        token = app_state["state"]["token"]["token"]

        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        self._token = token
        self._token_exp = payload["exp"]

    def _headers(self, referer: str) -> dict:
        if self._token is None or time.time() > self._token_exp - self.TOKEN_REFRESH_MARGIN_SEC:
            self._refresh_token()
        return {"Authorization": f"Bearer {self._token}", "Referer": referer, "Accept": "*/*"}

    def _get(self, path: str, params: dict, referer: str) -> requests.Response:
        r = self.session.get(f"{self.BASE}{path}", params=params, headers=self._headers(referer), timeout=10)
        if r.status_code == 401:
            # 토큰이 그 사이 만료/무효화된 경우 1회 재발급 후 재시도
            self._refresh_token()
            r = self.session.get(f"{self.BASE}{path}", params=params, headers=self._headers(referer), timeout=10)
        r.raise_for_status()
        return r

    def search_complex(self, keyword: str) -> list:
        """단지명으로 검색해 단지 후보 목록 반환"""
        r = self._get("/api/search", {"keyword": keyword}, f"{self.BASE}/")
        return r.json().get("complexes", [])

    def get_complex_detail(self, complex_no) -> dict:
        return self._get(f"/api/complexes/{complex_no}", {"sameAddressGroup": "false"},
                          f"{self.BASE}/complexes/{complex_no}").json()

    def get_articles(self, complex_no, trade_type: str = "", max_pages: int = 20) -> pd.DataFrame:
        """
        단지 매물 목록 조회
        trade_type: ''(전체), 'A1'(매매), 'B1'(전세), 'B2'(월세)
        """
        referer = f"{self.BASE}/complexes/{complex_no}"
        all_articles = []
        for page in range(1, max_pages + 1):
            params = {
                "realEstateType": "APT:PRE:ABYG:JGC",
                "tradeType": trade_type,
                "page": page,
                "complexNo": complex_no,
                "order": "rank",
            }
            data = self._get(f"/api/articles/complex/{complex_no}", params, referer).json()
            articles = data.get("articleList", [])
            if not articles:
                break
            all_articles.extend(articles)
            if not data.get("isMoreData", False):
                break
            time.sleep(0.3)

        if not all_articles:
            return pd.DataFrame()

        df = pd.DataFrame(all_articles)
        df = df.rename(columns={
            "tradeTypeName": "naver_거래유형",
            "areaName": "naver_평형",
            "area1": "naver_공급면적",
            "area2": "naver_전용면적",
            "dealOrWarrantPrc": "naver_가격",
            "floorInfo": "naver_층",
            "buildingName": "naver_동",
            "articleFeatureDesc": "naver_특징",
            "realtorName": "naver_중개사",
        })
        keep_cols = ["articleNo", "naver_거래유형", "naver_평형", "naver_공급면적", "naver_전용면적",
                     "naver_가격", "naver_층", "naver_동", "naver_특징", "naver_중개사"]
        return df[[c for c in keep_cols if c in df.columns]]

    def close(self):
        self.session.close()


def compare_court_with_naver(crawler: "NaverRealestateCrawler", court_row: dict) -> dict:
    """법원경매 물건 1건을 네이버 부동산 단지 매물과 매칭해 시세 비교"""
    from ZigbangCrawler import parse_apt_name_from_court_address, parse_court_price

    address = court_row.get('물건주소', '')
    dong, apt_name = parse_apt_name_from_court_address(address)
    if not apt_name:
        raise ValueError(f"물건주소에서 단지명을 찾을 수 없음: {address}")

    candidates = crawler.search_complex(apt_name)
    if not candidates:
        raise ValueError(f"네이버 부동산에서 단지를 찾을 수 없음: {apt_name}")

    def _addr_text(c):
        return " ".join(str(c.get(k, "")) for k in ("address", "roadAddress", "jibunAddress", "cortarAddress"))

    complex_no = next((c['complexNo'] for c in candidates if dong and dong in _addr_text(c)),
                       candidates[0]['complexNo'])

    articles = crawler.get_articles(complex_no)

    return {
        'court_사건번호': court_row.get('사건번호'),
        'court_물건주소': address,
        'court_단지명': apt_name,
        'court_감정가_만원': parse_court_price(court_row.get('감정가')),
        'court_최저가_만원': parse_court_price(court_row.get('최저가')),
        'naver_complex_no': complex_no,
        'naver_articles': articles,
    }


if __name__ == "__main__":
    c = NaverRealestateCrawler()
    try:
        test_row = {
            '사건번호': '서울중앙지방법원 2022타경891 2022타경108054 (중복)',
            '물건주소': '서울특별시 동작구 상도로 346-1 106동 9층902호 (상도동,힐스테이트상도센트럴파크) '
                     '[집합건물 철근콘크리트구조 118.2086㎡]',
            '감정가': '1,920,000,000',
            '최저가': '1,536,000,000 (80%)',
        }
        result = compare_court_with_naver(c, test_row)
        print(f"단지명(네이버 complexNo={result['naver_complex_no']}): {result['court_단지명']}")
        print(f"최저가: {result['court_최저가_만원']:,.0f}만원")
        print()
        articles = result['naver_articles']
        if articles.empty:
            print("네이버 부동산에 매물 없음")
        else:
            for tt in articles['naver_거래유형'].unique():
                sub = articles[articles['naver_거래유형'] == tt]
                print(f"[{tt}] {len(sub)}건")
                print(sub[['naver_평형', 'naver_가격', 'naver_동', 'naver_층']].to_string(index=False))
    finally:
        c.close()
