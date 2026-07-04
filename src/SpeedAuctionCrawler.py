# -*- coding: utf-8 -*-
"""
SpeedAuction (스피드옥션) 크롤러
- 법원경매 데이터의 추가 정보 수집 (조회수, 특수물건 등)
- 사건번호 기준 cross-check 용도
"""
import re, json, time, os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


class SpeedAuctionCrawler:
    BASE = "https://new.speedauction.co.kr"

    COLUMNS = [
        'speed_사건번호', 'speed_주소', 'speed_입찰',
        'speed_감정가최저가', 'speed_매각기일', 'speed_신고가매각가', 'speed_조회수',
    ]
    COL_사건번호 = 0
    COL_주소 = 1
    COL_조회수 = 6

    COURT_CODE_MAP = {
        'C01': '광주지방법원', 'C02': '광주지방법원(목포)', 'C03': '광주지방법원(순천)',
        'D01': '대구지방법원', 'D02': '대구지방법원(경주)',
        'J01': '전주지방법원', 'J02': '창원지방법원',
        'L01': '대전지방법원', 'L02': '대전지방법원(홍성)',
        'S01': '서울중앙지방법원', 'S02': '서울동부지방법원',
        'S03': '서울남부지방법원', 'S04': '서울북부지방법원', 'S05': '서울서부지방법원',
        'U01': '울산지방법원',
        'B01': '부산지방법원',
        'I01': '인천지방법원',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    def login(self, user_id, user_pw):
        self.session.get(self.BASE)
        r = self.session.post(self.BASE + "/member/ajax.member_login",
                              data={"id": user_id, "pw": user_pw})
        result = r.json()
        if result.get("result") == "success":
            print("SpeedAuction login OK")
            return True
        print("SpeedAuction login FAIL:", result.get("msg"))
        return False

    def fetch_listing_html(self, page=1):
        """기본 목록 (전체)"""
        return self.search_by_address("", page=page)

    def search_by_address(self, address: str, usage: str = "0", page: int = 1) -> str:
        """
        소재지 기반 검색
        address: 검색할 지역명 (예: '서울', '광주', '강남')
        usage: 용도코드 ('0'=전체, '1'=주거용, '2'=업무상업, '3'=공업, '4'=토지, '5'=기타)
        page: 페이지 번호
        """
        url = self.BASE + "/ajax?html&ajax.id=search@auction_result.ajax"
        data = {
            "page": str(page),
            "court_sub": "전체", "lastresultcode": "99",
            "courtNo_main": "00", "courtNo_sub": "00",
            "region_code1": "0", "region_code2": "0", "region_code3": "0",
            "quick_addr": address,
            "usagecode": usage,
        }
        # 주거용(1)이면 use1 체크박스 모두 활성화
        if usage == "1":
            data["p_usecode1_all"] = "Y"
        elif usage == "0":
            data["p_usecode1_all"] = "Y"
            data["p_usecode2_all"] = "Y"
            data["p_usecode3_all"] = "Y"
            data["p_usecode4_all"] = "Y"
            data["p_usecode5_all"] = "Y"

        r = self.session.post(url, data=data)
        return r.text

    def parse_listing(self, html) -> pd.DataFrame:
        soup = BeautifulSoup(html, "html.parser")
        rows = []
        table = soup.find("table")
        if not table:
            return pd.DataFrame()

        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue

            row = {}
            for i, td in enumerate(tds):
                col = self.COLUMNS[i] if i < len(self.COLUMNS) else f"col{i}"
                row[col] = td.get_text("\n", strip=True)

                # 아이콘/특수표시
                icons = []
                for img in td.find_all("img"):
                    alt = img.get("alt", "").strip()
                    if alt:
                        icons.append(alt)
                if icons:
                    row[col + "_icon"] = "|".join(icons)

            # onclick에서 토큰 추출 (td.number = tds[0])
            onclick = tds[0].get("onclick", "") if tds else ""
            m = re.search(r"view_product\('([^']+)','([^']+)','([^']+)','([^']+)'", onclick)
            if m:
                row["court_code"] = m.group(1)
                row["speed_년도"] = m.group(2)
                row["speed_사건본번"] = m.group(3)
                row["speed_물건번호"] = m.group(4)
                row["court_name"] = self.COURT_CODE_MAP.get(m.group(1), m.group(1))
                row["token"] = f"{m.group(1)}|{m.group(2)}|{m.group(3)}|{m.group(4)}"

            # 조회수 (숫자만 추출)
            if len(tds) > self.COL_조회수:
                hit_text = tds[self.COL_조회수].get_text(strip=True)
                hit = re.sub(r'[^0-9]', '', hit_text)
                row['speed_조회수'] = int(hit) if hit.isdigit() else 0

            # 특수물건 판단: 주소 열에 [ ] 내 텍스트 확인
            addr = row.get(self.COLUMNS[self.COL_주소], '')
            bracket_texts = re.findall(r'\[([^\]]+)\]', addr)
            special_flags = []
            for bt in bracket_texts:
                if any(kw in bt for kw in ['매각', '데드라인', '마감', '변경', '진행']):
                    special_flags.append(bt)
            row['speed_특수표시'] = '|'.join(special_flags) if special_flags else ''

            # 물건종류 (입찰 컬럼)
            item_type = row.get(self.COLUMNS[2], '')
            row['speed_물건종류'] = item_type

            row['수집일시'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            rows.append(row)

        return pd.DataFrame(rows)

    def normalize_case_no(self, speed_case_raw: str = None, year: str = None, event_no: str = None) -> str:
        """SpeedAuction 사건번호 → court 형식 (2004타경12246)"""
        if year and event_no:
            return f"{year}타경{event_no.zfill(5)}"
        if not speed_case_raw:
            return speed_case_raw or ''
        m = re.match(r'(\d{4})\s*[-–—]\s*(\d+)', speed_case_raw.strip())
        if m:
            return f"{m.group(1)}타경{m.group(2).zfill(5)}"
        if '타경' in speed_case_raw:
            return speed_case_raw.strip()
        return speed_case_raw.strip()

    def crawl_all_pages(self, max_pages=5) -> pd.DataFrame:
        all_dfs = []
        for page in range(1, max_pages + 1):
            html = self.fetch_listing_html(page)
            df = self.parse_listing(html)
            if df.empty:
                break
            all_dfs.append(df)
            time.sleep(0.5)
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        return pd.DataFrame()

    # 페이지 공통(chrome) 이미지 alt — 특수물건 판단에서 제외
    CHROME_ALT_TEXTS = {
        '스피드옥션', '대법원', '관할법원안내', '카카오지도', '네이버지도',
        '기일현황', '지점 안내', '사무소안내', '가맹점 모집', '법원별지사 모집',
        '상담신청', '현장제보', 'LG몰', 'LG로고',
    }

    def fetch_detail(self, token: str) -> dict:
        """개별 물건 상세 정보"""
        url = self.BASE + "/pop/open/!/view/product?token=" + token
        r = self.session.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        detail = {'token': token}

        # 특수물건 표시 아이콘: 페이지 공통 이미지를 제외한 모든 alt 텍스트 수집
        special_icons = []
        for img in soup.find_all('img'):
            alt = img.get('alt', '').strip()
            src = img.get('src', '')
            if alt and alt not in self.CHROME_ALT_TEXTS and 'logo' not in src.lower():
                special_icons.append(alt)
        if special_icons:
            detail['특수물건_아이콘'] = special_icons

        # "특수물건등" red span/폰트 확인
        for el in soup.find_all(['span', 'font']):
            txt = el.get_text(strip=True).replace('\u200b', '').strip()
            if '특수' in txt:
                color = el.get('color', '')
                style = el.get('style', '')
                cls = ' '.join(el.get('class', []))
                if color == 'red' or 'red' in style.lower() or 'red' in cls.lower():
                    detail['특수물건등_표시'] = txt
                    break

        # TODAY/TOTAL 조회수
        for tag in soup.find_all(['span', 'em', 'strong']):
            txt = tag.get_text(strip=True)
            if txt == 'TODAY':
                sibling = tag.find_next_sibling()
                if sibling:
                    detail['speed_오늘조회'] = sibling.get_text(strip=True)
            elif txt == 'TOTAL':
                sibling = tag.find_next_sibling()
                if sibling:
                    detail['speed_전체조회'] = sibling.get_text(strip=True)

        # dt/dd pairs
        info_items = {}
        for dt in soup.find_all('dt'):
            label = dt.get_text(strip=True)
            dd = dt.find_next_sibling('dd')
            if dd:
                value = dd.get_text(' ', strip=True).strip()[:200]
                if label and value and label not in info_items:
                    info_items[label] = value
        if info_items:
            detail['info_items'] = info_items

        return detail

    def crawl_details(self, df: pd.DataFrame, max_items: int = None) -> pd.DataFrame:
        """목록 DataFrame의 각 항목에 대해 상세 페이지 데이터를 추가"""
        df = df.copy()
        items_to_crawl = df.head(max_items) if max_items else df
        detail_cols = ['특수물건_아이콘', 'speed_오늘조회', 'speed_전체조회',
                       '특수물건등_표시', 'info_items']

        for col in detail_cols:
            if col not in df.columns:
                df[col] = None

        for idx, row in items_to_crawl.iterrows():
            token = row.get('token', '')
            if not token:
                continue
            try:
                detail = self.fetch_detail(token)
                icons = detail.get('특수물건_아이콘', [])
                if icons:
                    df.at[idx, '특수물건_아이콘'] = '|'.join(icons) if isinstance(icons, list) else icons
                df.at[idx, 'speed_오늘조회'] = detail.get('speed_오늘조회')
                df.at[idx, 'speed_전체조회'] = detail.get('speed_전체조회')
                df.at[idx, '특수물건등_표시'] = detail.get('특수물건등_표시')
                info = detail.get('info_items', {})
                if info:
                    for k, v in info.items():
                        col_name = f'상세_{k}'
                        if col_name not in df.columns:
                            df[col_name] = None
                        df.at[idx, col_name] = v
            except Exception as e:
                print(f"  Detail crawl fail [{token}]: {e}")
            time.sleep(0.3)

        return df

    def close(self):
        self.session.close()


def match_court_and_speed(court_df: pd.DataFrame, speed_df: pd.DataFrame) -> dict:
    """
    법원경매 데이터와 SpeedAuction 데이터를 사건번호로 cross-check
    Returns:
        {
            'matched': DataFrame (양쪽 모두 있는 항목)
            'court_only': DataFrame (법원에만 있는 항목)
            'speed_only': DataFrame (SpeedAuction에만 있는 항목)
            'compare': DataFrame (감정가 등 비교 결과)
        }
    """
    # Court 사건번호 정규화
    court_cases = {}
    court_df = court_df.copy()
    speed_df = speed_df.copy()

    # SpeedAuction 정규화 (onclick 토큰 기반: speed_년도 + speed_사건본번)
    if 'speed_사건번호_정규' not in speed_df.columns:
        crawler = SpeedAuctionCrawler()
        if 'speed_년도' in speed_df.columns and 'speed_사건본번' in speed_df.columns:
            speed_df['speed_사건번호_정규'] = speed_df.apply(
                lambda r: crawler.normalize_case_no(year=str(r['speed_년도']),
                                                     event_no=str(r['speed_사건본번'])), axis=1)
        elif 'speed_사건번호' in speed_df.columns:
            speed_df['speed_사건번호_정규'] = speed_df['speed_사건번호'].apply(
                lambda x: crawler.normalize_case_no(x.split('\n')[1].strip())
                           if '\n' in str(x) else crawler.normalize_case_no(str(x)))
        elif '사건번호' in speed_df.columns:
            speed_df['speed_사건번호_정규'] = speed_df['사건번호']

    court_df['사건번호_정규'] = court_df.get('사건번호', court_df.get('printCsNo', ''))

    matched = court_df[court_df['사건번호_정규'].isin(speed_df['speed_사건번호_정규'])].copy()
    court_df_only = court_df[~court_df['사건번호_정규'].isin(speed_df['speed_사건번호_정규'])].copy()
    speed_df_only = speed_df[~speed_df['speed_사건번호_정규'].isin(court_df['사건번호_정규'])].copy()

    # 비교 정보
    compare_rows = []
    for _, cr in matched.iterrows():
        case_no = cr['사건번호_정규']
        sr = speed_df[speed_df['speed_사건번호_정규'] == case_no].iloc[0]
        compare_rows.append({
            '사건번호': case_no,
            'court_주소': cr.get('물건주소', ''),
            'speed_주소': sr.get('speed_주소', sr.get('speed_사건번호', '')),
            'court_감정가': cr.get('감정가', cr.get('gamevalAmt', '')),
            'speed_조회수': sr.get('speed_조회수', 0),
            'speed_특수표시': sr.get('speed_특수표시', ''),
            'speed_물건종류': sr.get('speed_물건종류', ''),
        })

    return {
        'total_court': len(court_df),
        'total_speed': len(speed_df),
        'matched': matched,
        'court_only': court_df_only,
        'speed_only': speed_df_only,
        'compare': pd.DataFrame(compare_rows),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

    c = SpeedAuctionCrawler()
    if c.login(os.environ["SPEED_AUCTION_ID"], os.environ["SPEED_AUCTION_PW"]):
        print("\n--- Listing crawl ---")
        df = c.crawl_all_pages(max_pages=3)
        print(f"Total items: {len(df)}")
        print(df.columns.tolist())
        if not df.empty:
            print(df[[c for c in df.columns if c in ('speed_사건번호','speed_조회수','speed_주소','speed_특수표시')]].head().to_string())
    c.close()
