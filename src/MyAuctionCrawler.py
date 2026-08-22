# -*- coding: utf-8 -*-
"""
마이옥션(my-auction.co.kr) 크롤러
- 경매 물건 목록 수집 (지역/용도/가격/기일 필터, 사건번호/감정가/최저가/유찰횟수/조회수 등)

2026-08-22 리버스엔지니어링 + 실 계정 로그인 검증 결과 요약:
- `/auction/search.php`(경매종합검색) → `/auction/search_list.php`(검색결과)는 비로그인 시
  "로그인 후 이용가능합니다" alert와 함께 결과를 보여주지 않는 회원 전용 기능이다.
  실 계정으로 로그인 후 폼의 전체 필드셋(지역/용도/가격/기일/정렬 등)을 그대로 GET으로
  보내면 실제 목록이 반환됨을 확인했다 (예: 서울+아파트 필터 시 총 248건, 13페이지 규모 —
  사이트 전체 경매 DB를 대상으로 함). 필드 일부가 빠지면 `alert('error2')`로 거부된다.
- 로그인 없이도 같은 파라미터(지역/용도/가격/정렬/페이지)를 받는 `/auction/recommend.php`
  (추천경매물건)는 필터·정렬·페이지네이션이 정상 동작하지만, 이건 "추천물건" 풀(사이트
  표시상 전체 약 100~130건 규모)만 대상이라 커버리지가 훨씬 좁다. 필터링 후 결과가 몇 건
  안 되면 이후 페이지가 첫 페이지와 동일하게 반환되는 것도 확인됨(더 보여줄 데이터가 없다는
  뜻, 에러 아님). 계정 없이 빠르게 표본만 확인하고 싶을 때 대안으로 남겨둠.
- 두 엔드포인트 모두 결과 목록은 동일한 HTML 테이블 템플릿을 쓰므로 `parse_listing()`
  하나로 둘 다 파싱된다.
- 로그인(`login()`)은 `/member/login_handle.php`에 POST 시 `Referer` 헤더가 없으면
  간헐적으로 `alert('error2')`가 나는 것을 확인함 — 반드시 `Referer: {BASE}/member/login.php`
  헤더를 넣을 것 (본 모듈은 이미 적용됨).
"""
import re
import base64
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class MyAuctionCrawler:
    BASE = "https://www.my-auction.co.kr"

    # 시/도 코드 (address1_01) - /auction/search.php 폼 <select name="address1_01"> 기준
    SIDO_CODE_MAP = {
        '서울특별시': '10', '경기도': '3', '인천광역시': '12', '강원도': '2',
        '충청남도': '16', '대전광역시': '8', '충청북도': '17', '세종시': '18',
        '부산광역시': '9', '울산광역시': '11', '대구광역시': '7',
        '경상북도': '5', '경상남도': '4', '전남광주': '6', '전라북도': '14', '제주도': '15',
    }

    # 용도 코드 (usage_code) - /auction/search.php 폼 체크박스 기준 (일부, 주거용 중심)
    USAGE_CODE_MAP = {
        '아파트': '101', '주택': '102', '다세대(빌라)': '103', '다가구주택': '104',
        '근린주택': '105', '오피스텔': '106', '도시형생활주택': '107',
        '근린시설': '201', '근린상가': '202', '상가': '203', '공장': '204',
        '대지': '301', '임야': '302', '전': '303', '답': '304',
    }

    # 관할법원 코드 (acourt) - /auction/search.php 폼 <select name="acourt"> 기준
    # (CourtRealestateCrawling.py/SpeedAuctionCrawler.py의 법원명과 매칭용)
    COURT_CODE_MAP = {
        '서울중앙지방법원': '210', '서울동부지방법원': '211', '서울남부지방법원': '212',
        '서울북부지방법원': '213', '서울서부지방법원': '215', '의정부지방법원': '214',
        '인천지방법원': '240', '수원지방법원': '250', '성남지원': '251',
        '춘천지방법원': '260', '청주지방법원': '270', '대전지방법원': '280',
        '대구지방법원': '310', '부산지방법원': '410', '울산지방법원': '411',
        '창원지방법원': '420', '광주지방법원': '510', '전주지방법원': '520',
        '제주지방법원': '530',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    def login(self, user_id: str, user_pw: str) -> bool:
        """
        회원 로그인 (실 계정으로 성공/실패 케이스 모두 검증 완료 - 2026-08-22).

        사이트 JS(common.js)는 로그인 폼 제출 시 아이디/비밀번호를
        표준 base64(UTF-8)로 인코딩해 `id`/`pwd` 필드에 담아
        `/member/login_handle.php`로 POST한다 (js/java_base64.js의
        `_keyStr110216_1` 알파벳이 표준 base64 알파벳과 동일함을 확인).

        응답 본문으로 성공/실패 구분:
            성공: <script>top.location.href='https://www.my-auction.co.kr/';</script>
            실패: <script>alert('회원정보가 일치하지 않습니다.');history.go(-1);</script>
                  또는 <script>alert('비밀번호가 일치하지 않습니다.');history.go(-1);</script>
        """
        self.session.get(self.BASE + "/member/login.php")
        data = {
            "rtn_page": "",
            "id": base64.b64encode(user_id.encode("utf-8")).decode(),
            "pwd": base64.b64encode(user_pw.encode("utf-8")).decode(),
            "login_id": "",
            "login_pw": "",
        }
        r = self.session.post(self.BASE + "/member/login_handle.php", data=data,
                               headers={"Referer": self.BASE + "/member/login.php"})
        if "alert(" in r.text:
            print(f"MyAuction login FAIL: {r.text.strip()}")
            return False
        print("MyAuction login OK")
        return True

    def search_list(self, sido_code: str = "", gungu_code: str = "", dong_code: str = "",
                     acourt_code: str = "", usage_codes=None, aresult: str = "", aorder: str = "1",
                     ipdate1: str = "", ipdate2: str = "", page: int = 1, rows: int = 20,
                     use_recommend_endpoint: bool = True) -> str:
        """
        경매물건 목록 조회.

        Args:
            sido_code: SIDO_CODE_MAP 값 (예: 서울 '10'). acourt_code와 동시 지정 시
                acourt_code가 우선한다(stc=2 관할법원 모드로 전환).
            acourt_code: COURT_CODE_MAP 값 (예: 서울중앙지방법원 '210'). 지정하면
                지역 대신 관할법원 기준으로 검색한다 - 법원경매 크롤러(court_name)와
                동일 법원으로 마이옥션 결과를 맞출 때 사용.
            usage_codes: USAGE_CODE_MAP 값 리스트 (예: ['101'] = 아파트만)
            aresult: 진행상태 필터 (예: '진행', '매각' 등, 빈 문자열=전체)
            aorder: 정렬 (1=입찰일 가까운순 등, /auction/search.php의 aorder 옵션 참고)
            ipdate1/ipdate2: 입찰일 범위 (YYYY-MM-DD). 미지정 시 오늘~+90일로 채움
                (사이트 폼 기본값과 동일). `search_list.php`는 두 날짜 사이가 186일을
                넘으면 거부한다(사이트 측 제약).
            use_recommend_endpoint:
                True(기본값) - 로그인 불필요한 `/auction/recommend.php` 사용.
                    "추천물건" 풀(사이트 전체 기준 약 100~130건)만 대상이라 전체 경매
                    DB 커버리지는 아니지만, 계정 없이도 바로 동작한다.
                False - 회원 전용 `/auction/search_list.php` 사용. `login()` 성공 후
                    호출해야 실제 데이터가 반환된다 (실 계정으로 검증 완료 - 2026-08-22,
                    서울+아파트 필터 시 248건/13페이지 규모 확인). 로그인 없이 호출하면
                    빈 결과가 반환된다.
        """
        if not ipdate1 or not ipdate2:
            today = datetime.now().date()
            ipdate1 = ipdate1 or today.isoformat()
            ipdate2 = ipdate2 or (today + timedelta(days=90)).isoformat()

        path = "/auction/recommend.php" if use_recommend_endpoint else "/auction/search_list.php"
        # search_list.php는 /auction/search.php 폼의 전체 필드가 채워지지 않으면
        # alert('error2')로 거부한다 (일부 필드만 보내면 실패 - 확인됨). recommend.php는
        # 이 전체 필드셋을 보내도 문제없이 동작하므로 두 경로에 동일하게 사용한다.
        stc = "2" if acourt_code else "1"
        params = {
            "id": "", "stc": stc,
            "address1_01": sido_code, "address1_02": gungu_code, "address1_03": dong_code,
            "address2_01": sido_code, "address2_02": gungu_code, "address2_03": dong_code,
            "acourt": acourt_code, "acharge": "", "acharge_01": "",
            "sno": "", "tno": "",
            "ipdate1": ipdate1, "ipdate2": ipdate2,
            "eprice1": "0", "eprice2": "0",
            "regal": "",
            "mprice1": "0", "mprice2": "0",
            "barea1": "", "barea2": "",
            "np1": "", "np2": "",
            "apoint1": "", "apoint2": "",
            "larea1": "", "larea2": "",
            "buildingtxt": "",
            "aresult": aresult, "aorder": aorder,
            "usage_code_all": ",".join(usage_codes) if usage_codes else "",
            "npls": "N", "spels": "Y", "schs": "N", "pchs": "N",
            "spe_age": "", "gm_age": "", "stitle": "", "ps_alert": "",
            "page": str(page), "rows": str(rows),
        }
        r = self.session.get(self.BASE + path, params=params,
                              headers={"Referer": self.BASE + "/auction/search.php"})
        return r.text

    def parse_listing(self, html: str) -> pd.DataFrame:
        """
        search_list()가 반환한 HTML에서 목록 테이블을 파싱한다.
        (/auction/recommend.php, 로그인 후 /auction/search_list.php 응답 모두
        동일 템플릿을 사용함을 확인 - 2026-08-22)
        """
        soup = BeautifulSoup(html, "html.parser")
        rows = []

        for tr in soup.find_all("tr"):
            checkbox = tr.find("input", {"name": "idBox"})
            if not checkbox:
                continue
            tds = tr.find_all("td")
            if len(tds) < 7:
                continue

            row = {"my_물건ID": checkbox.get("value", "")}

            # 용도 / 사건번호 / 법원
            usage_td = tds[2]
            strong = usage_td.find("strong")
            row["my_물건종류"] = strong.get_text(strip=True) if strong else ""
            usage_lines = list(usage_td.stripped_strings)
            row["my_사건번호_raw"] = usage_lines[1] if len(usage_lines) > 1 else ""
            row["my_법원"] = usage_lines[2] if len(usage_lines) > 2 else ""
            row["my_사건번호"] = self.normalize_case_no(row["my_사건번호_raw"])

            # 소재지 / 면적 / 특수권리
            addr_td = tds[3]
            addr_a = addr_td.find("a")
            row["my_주소"] = addr_a.get_text(strip=True) if addr_a else ""
            area_text = addr_td.get_text(" ", strip=True)
            b_area = re.search(r'건물\s*([\d.]+)\s*평', area_text)
            l_area = re.search(r'토지\s*([\d.]+)\s*평', area_text)
            row["my_건물면적_평"] = float(b_area.group(1)) if b_area else None
            row["my_토지면적_평"] = float(l_area.group(1)) if l_area else None
            refer = addr_td.find("span", class_="refer")
            row["my_특수권리"] = refer.get_text(strip=True) if refer else ""

            # 감정가 / 최저가 (+ 국토부실거래가 참고치가 표시되는 경우 함께)
            price_td = tds[4]
            price_text = price_td.get_text("\n", strip=True)
            prices = re.findall(r'[\d,]{5,}', price_text)
            row["my_감정가"] = int(prices[0].replace(",", "")) if len(prices) > 0 else None
            row["my_최저가"] = int(prices[1].replace(",", "")) if len(prices) > 1 else None
            if "국토부실거래가" in price_text and len(prices) > 2:
                row["my_국토부실거래가_참고"] = int(prices[2].replace(",", ""))

            # 현재상태 (유찰횟수 등)
            status_td = tds[5]
            status_text = status_td.get_text(" ", strip=True)
            row["my_현재상태"] = status_text
            yuchal = re.search(r'유찰\s*(\d+)\s*회', status_text)
            row["my_유찰횟수"] = int(yuchal.group(1)) if yuchal else 0

            # 매각기일
            row["my_매각기일"] = tds[6].get_text(" ", strip=True)

            # 조회수
            row["my_조회수"] = 0
            if len(tds) > 7:
                hit_text = tds[7].get_text(strip=True)
                row["my_조회수"] = int(hit_text) if hit_text.isdigit() else 0

            rows.append(row)

        return pd.DataFrame(rows)

    def normalize_case_no(self, raw: str) -> str:
        """마이옥션 사건번호("2026-4233", "2025-51204(1)") → court 형식("2026타경04233")"""
        if not raw:
            return ""
        m = re.match(r'(\d{4})-(\d+)', raw.strip())
        if not m:
            return raw.strip()
        year, event_no = m.group(1), m.group(2)
        return f"{year}타경{event_no.zfill(5)}"

    def crawl_all_pages(self, max_pages: int = 5, **search_kwargs) -> pd.DataFrame:
        all_dfs = []
        seen_ids = set()
        for page in range(1, max_pages + 1):
            html = self.search_list(page=page, **search_kwargs)
            df = self.parse_listing(html)
            if df.empty:
                break
            # recommend.php는 필터링된 결과가 rows보다 적으면 다음 페이지에 같은
            # 항목을 반복 반환하는 것으로 확인됨 -> 중복 물건ID면 조기 종료
            new_ids = set(df["my_물건ID"]) - seen_ids
            if not new_ids:
                break
            seen_ids |= new_ids
            all_dfs.append(df)
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=["my_물건ID"])
        return pd.DataFrame()

    def close(self):
        self.session.close()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

    c = MyAuctionCrawler()
    my_id = os.environ.get("MY_AUCTION_ID")
    my_pw = os.environ.get("MY_AUCTION_PW")
    use_recommend = True

    if my_id and my_pw:
        if c.login(my_id, my_pw):
            use_recommend = False  # 로그인 성공 시 전체 DB(search_list.php)로 조회
        else:
            print("로그인 실패, 추천물건(recommend.php)으로 대체 조회")
    else:
        print("MY_AUCTION_ID/PW 미설정 - 추천물건(recommend.php)만 조회 (로그인 불필요)")

    print(f"--- 서울 아파트 조회 ({'전체 DB' if not use_recommend else '추천물건 풀'}) ---")
    df = c.crawl_all_pages(max_pages=3, sido_code=MyAuctionCrawler.SIDO_CODE_MAP['서울특별시'],
                            usage_codes=[MyAuctionCrawler.USAGE_CODE_MAP['아파트']],
                            use_recommend_endpoint=use_recommend)
    print(f"Total items: {len(df)}")
    if not df.empty:
        cols = ['my_사건번호', 'my_물건종류', 'my_주소', 'my_감정가', 'my_최저가', 'my_유찰횟수']
        print(df[[c for c in cols if c in df.columns]].to_string())
    c.close()
