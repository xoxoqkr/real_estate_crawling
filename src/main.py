# -*- coding: utf-8 -*-
"""
통합 파이프라인: 법원경매 + SpeedAuction cross-check + 국토부 실거래가 매칭
"""
import os, sys, uuid, time, json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page, paginate_and_extract, process_court_data
from SpeedAuctionCrawler import SpeedAuctionCrawler, match_court_and_speed
from CourtTradeMatcher import match_batch, parse_court_address
from AWSFunction import save_to_s3
from AptTradeAPI import get_lawd_cd

SAVE_DIR = os.environ.get('SAVE_DIR', os.path.expanduser('~/Downloads/'))
os.makedirs(SAVE_DIR, exist_ok=True)
API_KEY = os.environ["MOLIT_API_KEY"]
SPEED_ID = os.environ["SPEED_AUCTION_ID"]
SPEED_PW = os.environ["SPEED_AUCTION_PW"]
BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", "odtest01")


def crawl_court_data(court_name="서울중앙지방법원", max_pages=5):
    """Step 1: 법원경매 사이트 크롤링"""
    print(f"\n{'='*50}")
    print(f"[1/4] 법원경매 크롤링: {court_name} (최대 {max_pages}페이지)")
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
    """Step 2: SpeedAuction 크롤링
    Args:
        search_address: 검색할 지역명 (예: '서울', '광주', '강남' 등, 빈 문자열=전체)
        usage: 용도코드 ('0'=전체, '1'=주거용, '2'=업무상업, '3'=공업, '4'=토지, '5'=기타)
        max_pages: 최대 페이지 수
        crawl_details: True면 상세페이지 크롤링
    """
    print(f"\n{'='*50}")
    print(f"[2/4] SpeedAuction 크롤링 (지역={search_address or '전체'}, 용도={usage})")
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


def cross_check(court_df, speed_df):
    """Step 3: 법원경매 ↔ SpeedAuction cross-check"""
    print(f"\n{'='*50}")
    print(f"[3/4] Cross-check: 법원경매 vs SpeedAuction")
    print(f"{'='*50}")

    if court_df.empty or speed_df.empty:
        print("데이터 부족으로 cross-check 생략")
        return None, court_df

    result = match_court_and_speed(court_df, speed_df)

    print(f"  법원경매 전체: {result['total_court']}건")
    print(f"  SpeedAuction 전체: {result['total_speed']}건")
    print(f"  일치(교집합): {len(result['matched'])}건")
    print(f"  법원에만 있음: {len(result['court_only'])}건")
    print(f"  Speed에만 있음: {len(result['speed_only'])}건")

    if not result['compare'].empty:
        print(f"\n비교 상세:")
        for _, r in result['compare'].head(10).iterrows():
            print(f"  {r['사건번호']} | 조회:{r['speed_조회수']} | 특수:{r['speed_특수표시']}")

        # 저장
        path = os.path.join(SAVE_DIR, f'cross_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        result['compare'].to_csv(path, index=False, encoding='utf-8-sig')
        print(f"Cross-check 저장: {path}")

    # 병합: court_df에 speed 정보 추가
    merged = court_df.copy()
    if not speed_df.empty and 'speed_사건번호_정규' in speed_df.columns:
        speed_merge = speed_df[['speed_사건번호_정규', 'speed_조회수', 'speed_특수표시',
                                 'speed_물건종류', 'speed_주소', 'court_name']].copy()
        speed_merge = speed_merge.rename(columns={
            'speed_주소': 'speed_주소_raw',
            'court_name': 'speed_법원명',
        })

        court_norm_col = '사건번호' if '사건번호' in merged.columns else 'printCsNo'
        if court_norm_col in merged.columns:
            merged = merged.merge(speed_merge, left_on=court_norm_col,
                                  right_on='speed_사건번호_정규', how='left')

    # 저장
    path = os.path.join(SAVE_DIR, f'court_data_merged_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    merged.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"병합 데이터 저장: {path} ({len(merged)}건)")

    return result, merged


def run_trade_matching(merged_df):
    """Step 4: 국토부 실거래가 매칭"""
    print(f"\n{'='*50}")
    print(f"[4/4] 국토부 실거래가 매칭")
    print(f"{'='*50}")

    if merged_df.empty:
        print("매칭할 데이터 없음")
        return pd.DataFrame()

    match_results = match_batch(API_KEY, merged_df)

    # 결과 정리
    success = match_results[match_results['success'] == True]
    fail = match_results[match_results['success'] == False]

    # 사건번호 연결
    if '사건번호' in merged_df.columns:
        match_results['사건번호'] = merged_df['사건번호'].values[:len(match_results)]

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

    # S3 저장
    try:
        save_to_s3(match_results, BUCKET_NAME, "court_data/trade_matched")
        save_to_s3(success, BUCKET_NAME, "court_data/trade_matched_success")
    except Exception as e:
        print(f"S3 저장 실패: {e}")

    return match_results


def main():
    print(f"=== 통합 경매 분석 파이프라인 ===")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: 법원경매 크롤링
    court_df, uid = crawl_court_data("서울중앙지방법원", max_pages=5)

    if court_df.empty:
        # 저장된 파일이 있으면 로드
        court_files = [f for f in os.listdir(SAVE_DIR) if 'court_Data' in f and f.endswith('.csv')]
        if court_files:
            court_df = pd.read_csv(os.path.join(SAVE_DIR, sorted(court_files)[-1]), encoding='utf-8')
            print(f"기존 파일 로드: {sorted(court_files)[-1]} ({len(court_df)}건)")
        else:
            print("법원경매 데이터 없음")

    # Step 2: SpeedAuction 크롤링 (서울, 주거용, 상세페이지 포함)
    speed_df = crawl_speed_data(search_address="서울", usage="1", max_pages=10, crawl_details=True)

    # Step 3: Cross-check
    cross_result, merged_df = cross_check(court_df, speed_df)

    # Step 4: 실거래가 매칭
    match_results = run_trade_matching(cross_result.get('matched', merged_df) if cross_result else merged_df)

    print(f"\n{'='*50}")
    print(f"파이프라인 완료!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
