# -*- coding: utf-8 -*-
"""
통합 파이프라인: 마이옥션 검색 -> 국토부 실거래가 매칭 -> 법원경매/SpeedAuction 보조정보 병합

2026-08-22 구조 변경: 기존에는 법원경매(Selenium) 크롤링이 1단계이자 실거래가 매칭의
기준 데이터였는데, (1) 법원경매 크롤링은 Selenium 기반이라 느리고 사이트 구조 변화에
취약하며 (2) 마이옥션 3사 교차검증 결과 마이옥션이 법원경매 데이터를 이미 그대로
포함하고 있어 별도로 두 번 수집할 필요가 없고 (3) 마이옥션은 검색 시점에 물건종류
(아파트 등)를 바로 지정할 수 있어 국토부 실거래가 API(아파트 실거래만 제공)와 궁합이
훨씬 좋다는 것을 확인했다. 그래서 마이옥션 검색 -> 국토부 매칭을 파이프라인의 핵심
경로로 삼고, 법원경매/SpeedAuction은 사건번호 기준으로 나중에 보조정보(담당계,
유찰횟수, 조회수 등)만 붙이는 방식으로 바꿨다.
"""
import os, sys, uuid, time, json, argparse, re, threading
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page, paginate_and_extract, process_court_data
from SpeedAuctionCrawler import SpeedAuctionCrawler
from MyAuctionCrawler import MyAuctionCrawler
from CourtTradeMatcher import match_batch
from AWSFunction import save_to_s3, load_seen_cases, save_seen_cases

SAVE_DIR = os.environ.get('SAVE_DIR', os.path.expanduser('~/Downloads/'))
os.makedirs(SAVE_DIR, exist_ok=True)
API_KEY = os.environ["MOLIT_API_KEY"]
SPEED_ID = os.environ["SPEED_AUCTION_ID"]
SPEED_PW = os.environ["SPEED_AUCTION_PW"]
MY_AUCTION_ID = os.environ.get("MY_AUCTION_ID")
MY_AUCTION_PW = os.environ.get("MY_AUCTION_PW")
BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", "odtest01")

# 마이옥션 물건종류(usage_names) -> SpeedAuction 용도코드 매핑
# SpeedAuction은 대분류(0=전체,1=주거용,2=업무상업,3=공업,4=토지,5=기타)만 지원해서
# 마이옥션만큼 세분화된 선택은 못하지만, 최대한 맞춰서 함께 넘겨준다.
USAGE_TO_SPEED_CODE = {
    '아파트': '1', '주택': '1', '다세대(빌라)': '1', '다가구주택': '1',
    '근린주택': '1', '오피스텔': '1', '도시형생활주택': '1',
    '근린시설': '2', '근린상가': '2', '상가': '2',
    '공장': '3',
    '대지': '4', '임야': '4', '전': '4', '답': '4',
}


def _start_timeout_watchdog(timeout_minutes):
    """
    실행 시간이 timeout_minutes를 넘으면 프로세스를 강제 종료한다.
    2026-08-22 추가: 주간 EventBridge 스케줄로 도는 배치라 무한정 붙잡고 있으면
    안 됨(과거 Selenium/chromedriver가 죽었을 때 스크립트가 아무 타임아웃 없이
    영원히 멈춰있던 사례가 실제로 있었음 - §8 참고). `signal.alarm`은 Windows에서
    못 쓰므로(이 프로젝트는 로컬 Windows 개발 이력도 있음, 레거시 코드의
    'C:/Users/...' 경로 참고) 플랫폼 무관하게 동작하는 데몬 스레드로 구현.
    타임아웃이 걸리면 os._exit()으로 즉시 종료 - 진행 중이던 S3 업로드 등은
    유실될 수 있으나, 무한 대기보다는 낫다는 판단.
    """
    def _kill():
        print(f"\n{'!'*50}")
        print(f"⏱ 타임아웃({timeout_minutes}분) 초과 - 파이프라인 강제 종료")
        print(f"{'!'*50}")
        os._exit(1)

    timer = threading.Timer(timeout_minutes * 60, _kill)
    timer.daemon = True
    timer.start()
    return timer


def crawl_court_data(court_name="서울중앙지방법원", max_pages=5):
    """Step 3(보조): 법원경매 사이트 크롤링 - 마이옥션에 없는 담당계/유찰횟수 등 보강용"""
    print(f"\n{'='*50}")
    print(f"[3/5] 법원경매 크롤링(보조): {court_name} (최대 {max_pages}페이지)")
    print(f"{'='*50}")

    _uuid = str(uuid.uuid4())
    driver = setup_webdriver()
    try:
        navigate_to_search_page(driver, court_name=court_name)
        merged_result_df = paginate_and_extract(driver, max_pages=max_pages)
        if merged_result_df.empty:
            print("법원경매 데이터 없음")
            return pd.DataFrame(), _uuid

        merged_result_df = process_court_data(merged_result_df, SAVE_DIR, _uuid)
        return merged_result_df, _uuid
    finally:
        driver.quit()


def crawl_speed_data(search_address="", usage="1", max_pages=10, crawl_details=False):
    """Step 4(보조): SpeedAuction 크롤링 - 조회수/특수표시 등 보강용
    Args:
        search_address: 검색할 지역명 (예: '서울', '광주', '강남' 등, 빈 문자열=전체)
        usage: 용도코드 ('0'=전체, '1'=주거용, '2'=업무상업, '3'=공업, '4'=토지, '5'=기타)
        max_pages: 최대 페이지 수
        crawl_details: True면 상세페이지 크롤링
    """
    print(f"\n{'='*50}")
    print(f"[4/5] SpeedAuction 크롤링(보조) (지역={search_address or '전체'}, 용도={usage})")
    print(f"{'='*50}")

    crawler = SpeedAuctionCrawler()
    if not crawler.login(SPEED_ID, SPEED_PW):
        print("SpeedAuction 로그인 실패, 건너뜁니다")
        return pd.DataFrame()

    try:
        all_dfs = []
        for page in range(1, max_pages + 1):
            html = crawler.search_by_address(search_address, usage=usage, page=page) if search_address \
                    else crawler.fetch_listing_html(page)
            df = crawler.parse_listing(html)
            if df.empty:
                break
            all_dfs.append(df)
            time.sleep(0.5)

        if not all_dfs:
            print("SpeedAuction 데이터 없음")
            return pd.DataFrame()
        df = pd.concat(all_dfs, ignore_index=True)

        # 사건번호 정규화
        if 'speed_년도' in df.columns and 'speed_사건본번' in df.columns:
            df['speed_사건번호_정규'] = df.apply(
                lambda r: crawler.normalize_case_no(year=str(r['speed_년도']),
                                                     event_no=str(r['speed_사건본번'])), axis=1)
        # 조회수 컬럼명 통일
        if 'speed_조회수' in df.columns:
            df['speed_조회수'] = pd.to_numeric(df['speed_조회수'], errors='coerce').fillna(0).astype(int)

        # 상세페이지 크롤링
        if crawl_details and not df.empty:
            print(f"\n  상세페이지 크롤링 ({len(df)}건)...")
            df = crawler.crawl_details(df)
            print(f"  상세페이지 완료")

        # 저장
        path = os.path.join(SAVE_DIR, f'speed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"SpeedAuction 저장: {path} ({len(df)}건)")

        return df
    finally:
        crawler.close()


def crawl_myauction_data(sido_name="서울특별시", usage_names=None, max_pages=10):
    """Step 1: 마이옥션 검색 (파이프라인의 기준 데이터 소스)
    Args:
        sido_name: MyAuctionCrawler.SIDO_CODE_MAP 키 (예: '서울특별시')
        usage_names: MyAuctionCrawler.USAGE_CODE_MAP 키 리스트 (예: ['아파트'], None=전체)
        max_pages: 최대 페이지 수 (페이지당 20건)
    """
    print(f"\n{'='*50}")
    print(f"[1/5] 마이옥션 검색 (지역={sido_name}, 용도={usage_names or '전체'})")
    print(f"{'='*50}")

    if not MY_AUCTION_ID or not MY_AUCTION_PW:
        print("MY_AUCTION_ID/PW 미설정, 마이옥션 크롤링 건너뜁니다")
        return pd.DataFrame()

    crawler = MyAuctionCrawler()
    use_recommend = True
    if crawler.login(MY_AUCTION_ID, MY_AUCTION_PW):
        use_recommend = False  # 로그인 성공 -> 전체 DB(search_list.php) 대상 조회
    else:
        print("마이옥션 로그인 실패, 추천물건(recommend.php)으로 대체 조회")

    try:
        usage_codes = [MyAuctionCrawler.USAGE_CODE_MAP[u] for u in usage_names
                        if u in MyAuctionCrawler.USAGE_CODE_MAP] if usage_names else None
        sido_code = MyAuctionCrawler.SIDO_CODE_MAP.get(sido_name, "")

        df = crawler.crawl_all_pages(max_pages=max_pages, sido_code=sido_code,
                                      usage_codes=usage_codes,
                                      use_recommend_endpoint=use_recommend)
        if df.empty:
            print("마이옥션 데이터 없음")
            return pd.DataFrame()

        path = os.path.join(SAVE_DIR, f'myauction_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"마이옥션 저장: {path} ({len(df)}건)")

        return df
    finally:
        crawler.close()


def run_trade_matching(myauction_df):
    """
    Step 2: 국토부 실거래가 매칭 - 마이옥션 검색 결과를 직접 사용.

    법원경매/SpeedAuction 크롤링을 기다리지 않고 마이옥션 결과(주소/감정가)만으로
    바로 매칭한다. 마이옥션은 검색 시점에 물건종류를 지정할 수 있어(예: 아파트만),
    국토부 API가 아파트 실거래만 제공하는 것과 맞아떨어져 매칭 신뢰도가 높다.
    """
    print(f"\n{'='*50}")
    print(f"[2/5] 국토부 실거래가 매칭 (마이옥션 결과 기반)")
    print(f"{'='*50}")

    if myauction_df.empty:
        print("매칭할 마이옥션 데이터 없음")
        return pd.DataFrame()

    # match_batch -> match_court_to_market -> parse_court_address()는 법원경매 주소
    # 형식의 "[... NN.NN㎡]" 패턴에서 면적을 추출하는데, 마이옥션 주소(my_주소)에는
    # 이 표기가 없다(면적은 my_건물면적_평에 평 단위로 별도 저장됨). 그대로 넘기면
    # 전부 "주소 파싱 실패"가 난다 - 마이옥션 면적(평)을 ㎡로 환산해 같은 표기를
    # 덧붙여서 기존 파싱 로직을 그대로 재사용한다.
    PYEONG_TO_M2 = 3.305785
    match_input = myauction_df.copy()

    def _with_area_bracket(row):
        addr = str(row.get('my_주소', ''))
        py = row.get('my_건물면적_평')
        if pd.notna(py):
            area_m2 = float(py) * PYEONG_TO_M2
            return f"{addr} [집합건물 {area_m2:.2f}㎡]"
        return addr

    match_input['물건주소'] = match_input.apply(_with_area_bracket, axis=1)
    match_input = match_input.rename(columns={'my_감정가': '감정가'})
    match_results = match_batch(API_KEY, match_input)

    # 사건번호/마이옥션 부가정보 연결
    match_results['사건번호'] = myauction_df['my_사건번호'].values[:len(match_results)]
    match_results['my_최저가'] = myauction_df['my_최저가'].values[:len(match_results)]
    match_results['my_물건종류'] = myauction_df['my_물건종류'].values[:len(match_results)]

    success = match_results[match_results['success'] == True]
    fail = match_results[match_results['success'] == False]

    print(f"  매칭 성공: {len(success)}건")
    print(f"  매칭 실패: {len(fail)}건")

    if not fail.empty:
        print(f"  실패 사유:")
        for _, r in fail.head(5).iterrows():
            print(f"    - {r.get('court_address', '')[:50]}: {r.get('error', '')}")

    if not success.empty:
        print(f"\n  시세 비교 결과 (상위 5건):")
        for _, r in success.head(5).iterrows():
            avg = r.get('avg_market_price', 0)
            gameval = r.get('gameval_amt', 0)
            diff = r.get('diff_ratio', 0)
            addr = r.get('court_address', '')[:40]
            arrow = '▲' if diff > 0 else '▼'
            print(f"    {addr}: 감정가 {gameval:.0f}만원 → 시세 {avg:.0f}만원 ({arrow} {abs(diff):.1f}%)")

    # 저장
    path = os.path.join(SAVE_DIR, f'trade_matching_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    match_results.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"매칭 결과 저장: {path}")

    return match_results


def _normalize_case_no(raw):
    """
    법원경매 원본 '사건번호'는 법원명이 앞에 붙고(예: "서울중앙지방법원 2008타경25092
    2015타경19958 (중복)") 때로 병합된 사건번호가 여러 개 이어붙는다. 마이옥션/
    match_results 쪽 사건번호는 "YYYY타경NNNNN"(5자리 zero-pad, 법원명 없음) 형식으로
    정규화되어 있으므로, 병합 전에 첫 번째 사건번호만 뽑아 같은 형식으로 맞춘다.
    """
    if not isinstance(raw, str):
        return None
    m = re.search(r'(\d{4})\s*타경\s*(\d+)', raw)
    if not m:
        return None
    return f"{m.group(1)}타경{m.group(2).zfill(5)}"


def enrich_with_sources(match_results, court_df, speed_df):
    """
    Step 5: 법원경매/SpeedAuction 보조정보 병합 + 최종 저장 + S3 업로드.

    법원경매/SpeedAuction은 이제 매칭의 기준 데이터가 아니라, 사건번호가 일치하는
    경우에만 담당계/유찰횟수/조회수 등 마이옥션에 없는 필드를 추가로 붙여주는
    보조 역할이다. 둘 다 실패하거나 비어 있어도 match_results 자체는 이미
    완성되어 있으므로 파이프라인은 계속 진행된다.
    """
    print(f"\n{'='*50}")
    print(f"[5/5] 법원경매/SpeedAuction 보조정보 병합")
    print(f"{'='*50}")

    merged = match_results.copy()

    if not court_df.empty and '사건번호' in court_df.columns:
        court_merge = court_df[['사건번호', '담당계', '유찰횟수', '비고']].copy()
        court_merge['사건번호_norm'] = court_merge['사건번호'].apply(_normalize_case_no)
        court_merge = court_merge.dropna(subset=['사건번호_norm']).drop_duplicates(subset=['사건번호_norm'])
        court_merge = court_merge.drop(columns=['사건번호']).rename(columns={
            '담당계': 'court_담당계', '유찰횟수': 'court_유찰횟수', '비고': 'court_비고',
        })
        merged = merged.merge(court_merge, left_on='사건번호', right_on='사건번호_norm', how='left')
        merged = merged.drop(columns=['사건번호_norm'])
        print(f"  법원경매 매칭: {merged['court_담당계'].notna().sum()}건")
    else:
        print("  법원경매 데이터 없음, 보조정보 병합 생략")

    if not speed_df.empty and 'speed_사건번호_정규' in speed_df.columns:
        speed_merge = speed_df[['speed_사건번호_정규', 'speed_조회수', 'speed_특수표시', 'court_name']].copy()
        speed_merge = speed_merge.rename(columns={'court_name': 'speed_법원명'})
        merged = merged.merge(speed_merge, left_on='사건번호', right_on='speed_사건번호_정규', how='left')
        print(f"  SpeedAuction 매칭: {merged['speed_조회수'].notna().sum()}건")
    else:
        print("  SpeedAuction 데이터 없음, 보조정보 병합 생략")

    # 최종 저장
    path = os.path.join(SAVE_DIR, f'final_merged_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    merged.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"최종 결과 저장: {path} ({len(merged)}건)")

    # S3 저장
    success = merged[merged['success'] == True] if 'success' in merged.columns else merged
    try:
        save_to_s3(merged, BUCKET_NAME, "court_data/trade_matched")
        save_to_s3(success, BUCKET_NAME, "court_data/trade_matched_success")
    except Exception as e:
        print(f"S3 저장 실패: {e}")

    return merged


def main(usage_names=None, max_pages=5, skip_court=False, skip_speed=False,
         timeout_minutes=30, skip_seen=True, reset_seen=False):
    """
    Args:
        usage_names: MyAuctionCrawler.USAGE_CODE_MAP 키 리스트 (예: ['아파트']).
            None이면 마이옥션은 전체 용도로 조회함. SpeedAuction도 이 값에 맞춰
            대분류 용도코드로 함께 필터링됨 (USAGE_TO_SPEED_CODE 참고).
            국토부 실거래가 API는 아파트 실거래만 제공하므로, 이 값을 아파트로
            좁힐수록(기본값) 국토부 매칭 성공률과 신뢰도가 높아짐 - 다른 용도는
            매칭돼도 "근처의 다른 아파트 시세"가 잘못 잡히는 경우가 많음
            (2026-08-22 마이옥션 3사 교차검증 작업에서 확인).
        max_pages: 마이옥션/법원경매/SpeedAuction 각 단계의 최대 페이지 수
        skip_court: True면 법원경매 크롤링(Selenium, 느리고 사이트 변화에 취약)을
            건너뛴다. 마이옥션 기준 매칭 결과 자체는 영향 없고, 담당계/유찰횟수 등
            법원경매 고유 보조정보만 빠진다.
        skip_speed: True면 SpeedAuction 크롤링을 건너뛴다.
        timeout_minutes: 이 시간(분)을 넘기면 프로세스를 강제 종료한다 (2026-08-22
            추가 - 매주 자동 실행되는 배치라 hang 상태로 계속 도는 것을 방지).
        skip_seen: True(기본값)면 S3에 기록된 처리 이력(`AWSFunction.load_seen_cases`)에
            있는 사건번호는 이번 실행에서 건너뛴다 - 매주 도는 배치에서 이미 본 매물을
            국토부 API로 반복 조회하지 않기 위함(2026-08-22 추가). **주의**: 완전히
            건너뛰므로, 이미 본 매물이 그 사이 유찰되어 최저가가 바뀌었어도 반영되지
            않는다 - 최신 가격까지 반영하려면 False로 끌 것.
        reset_seen: True면 필터링에 기존 이력을 사용하지 않는다(전체 재처리). 처리
            이력 자체는 이번 실행 결과로 계속 갱신됨 - 이력을 완전히 지우고 싶으면
            S3에서 `court_data/seen_cases.json`를 직접 삭제할 것.
    """
    usage_names = usage_names if usage_names is not None else ['아파트']
    print(f"=== 통합 경매 분석 파이프라인 ===")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"물건종류 필터: {', '.join(usage_names) if usage_names else '전체'}")
    print(f"타임아웃: {timeout_minutes}분")

    watchdog = _start_timeout_watchdog(timeout_minutes)
    try:
        # Step 1: 마이옥션 검색 (기준 데이터)
        myauction_df = crawl_myauction_data(sido_name="서울특별시", usage_names=usage_names, max_pages=max_pages * 2)

        # 이미 처리한 사건번호 필터링 (매주 반복 실행 시 중복 방지)
        if skip_seen and not reset_seen and not myauction_df.empty and 'my_사건번호' in myauction_df.columns:
            seen = load_seen_cases(BUCKET_NAME)
            before = len(myauction_df)
            myauction_df = myauction_df[~myauction_df['my_사건번호'].isin(seen)].copy()
            print(f"처리 이력 필터링: {before}건 중 {before - len(myauction_df)}건은 이미 처리됨 -> "
                  f"{len(myauction_df)}건만 새로 처리")
        elif reset_seen:
            print("reset_seen=True - 처리 이력 무시하고 전체 재처리")

        # Step 2: 국토부 실거래가 매칭 (마이옥션 결과 기반, 법원경매/SpeedAuction 안 기다림)
        match_results = run_trade_matching(myauction_df)

        # Step 3: 법원경매 크롤링 (보조) - 필요시 건너뛸 수 있음
        court_df = pd.DataFrame()
        if not skip_court:
            court_df, uid = crawl_court_data("서울중앙지방법원", max_pages=max_pages)
            if court_df.empty:
                # 저장된 파일이 있으면 로드
                court_files = [f for f in os.listdir(SAVE_DIR) if 'court_Data' in f and f.endswith('.csv')]
                if court_files:
                    court_df = pd.read_csv(os.path.join(SAVE_DIR, sorted(court_files)[-1]), encoding='utf-8')
                    print(f"기존 파일 로드: {sorted(court_files)[-1]} ({len(court_df)}건)")
        else:
            print(f"\n[3/5] 법원경매 크롤링 건너뜀 (skip_court=True)")

        # Step 4: SpeedAuction 크롤링 (보조) - 필요시 건너뛸 수 있음
        speed_df = pd.DataFrame()
        if not skip_speed:
            speed_usage_codes = {USAGE_TO_SPEED_CODE.get(u, '0') for u in usage_names} if usage_names else {'0'}
            speed_usage = speed_usage_codes.pop() if len(speed_usage_codes) == 1 else '0'
            speed_df = crawl_speed_data(search_address="서울", usage=speed_usage, max_pages=max_pages * 2, crawl_details=True)
        else:
            print(f"\n[4/5] SpeedAuction 크롤링 건너뜀 (skip_speed=True)")

        # Step 5: 법원경매/SpeedAuction 보조정보 병합 + 최종 저장
        final_df = enrich_with_sources(match_results, court_df, speed_df)

        # 처리 이력 갱신 (이번에 새로 처리한 사건번호를 이력에 추가)
        if not myauction_df.empty and 'my_사건번호' in myauction_df.columns:
            save_seen_cases(myauction_df['my_사건번호'].tolist(), BUCKET_NAME)

        print(f"\n{'='*50}")
        print(f"파이프라인 완료!")
        print(f"{'='*50}")
    finally:
        watchdog.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="법원경매 통합 분석 파이프라인 (마이옥션 검색 -> 국토부 실거래가 매칭)")
    parser.add_argument(
        "--usage", "-u", nargs="+",
        choices=sorted(MyAuctionCrawler.USAGE_CODE_MAP.keys()) + ['전체'],
        default=['아파트'],
        help="조회할 물건종류 (기본값: 아파트). 국토부 실거래가는 아파트만 제공하므로 "
             "다른 용도를 고르면 실거래가 매칭이 부정확해질 수 있음. "
             "'전체'를 주면 용도 필터 없이 전체 조회."
    )
    parser.add_argument("--max-pages", type=int, default=5, help="각 단계 최대 페이지 수 (기본값: 5)")
    parser.add_argument("--skip-court", action="store_true", help="법원경매(Selenium) 크롤링 건너뛰기")
    parser.add_argument("--skip-speed", action="store_true", help="SpeedAuction 크롤링 건너뛰기")
    parser.add_argument("--timeout-minutes", type=int, default=30,
                         help="이 시간(분)을 넘기면 강제 종료 (기본값: 30). 주간 자동 실행 시 "
                              "hang 방지용")
    parser.add_argument("--no-skip-seen", action="store_true",
                         help="S3에 기록된 처리 이력을 무시하지 않고 사용 (기본 동작) 대신, "
                              "이미 처리한 사건번호도 매번 다시 처리하고 싶을 때 사용")
    parser.add_argument("--reset-seen", action="store_true",
                         help="이번 실행만 처리 이력을 무시하고 전체 재처리 (이력 자체는 "
                              "이번 결과로 계속 갱신됨)")
    args = parser.parse_args()

    usage_arg = None if '전체' in args.usage else args.usage
    main(usage_names=usage_arg, max_pages=args.max_pages,
         skip_court=args.skip_court, skip_speed=args.skip_speed,
         timeout_minutes=args.timeout_minutes,
         skip_seen=not args.no_skip_seen, reset_seen=args.reset_seen)
