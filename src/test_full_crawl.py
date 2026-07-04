import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page, paginate_and_extract, process_court_data
import uuid

uid = str(uuid.uuid4())
save_dir = 'C:/Users/xoxoq/Downloads/'

print('1. 웹드라이버 설정')
driver = setup_webdriver()

print('2. 페이지 이동 및 검색')
navigate_to_search_page(driver, court_name="서울중앙지방법원")

print('3. 페이지별 데이터 추출 (최대 2페이지)')
result_df = paginate_and_extract(driver, max_pages=2, loading_wait_time_sec=3)
print(f'   추출 완료: {len(result_df)} 행')

if len(result_df) > 0:
    # Save raw data
    raw_path = f'{save_dir}court_raw_test_{uid}.csv'
    result_df.to_csv(raw_path, encoding='CP949')
    print(f'4. 원본 저장: {raw_path}')
    
    # Print sample
    print('\n--- 원본 데이터 샘플 ---')
    for _, row in result_df.head(3).iterrows():
        print(f"  사건: {row['printCsNo']}, 물건: {row['maemulSer']}, 주소: {row['printSt'][:40]}")
    
    print('5. 데이터 처리 (사건번호 병합)')
    processed_df = process_court_data(result_df, save_dir, uid)
    proc_path = f'{save_dir}court_processed_test_{uid}.csv'
    processed_df.to_csv(proc_path, encoding='CP949')
    print(f'   처리 완료: {len(processed_df)} 행')
    
    print('\n--- 처리 데이터 샘플 ---')
    for _, row in processed_df.head(3).iterrows():
        print(f"  사건번호: {row['사건번호']}")
        print(f"  물건주소: {row['물건주소'][:60]}...")
        print(f"  감정가: {row['감정가']}, 최저가: {row['최저가']}, 유찰: {row['유찰횟수']}")
else:
    print('추출된 데이터가 없습니다.')

driver.quit()
print('\n=== 전체 크롤링 테스트 완료 ===')
