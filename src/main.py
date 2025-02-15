from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page, paginate_and_extract, process_court_data
from AWSFunction import save_to_s3
import uuid

if __name__ == "__main__":
    uuid = str(uuid.uuid4())
    # S3 설정
    BUCKET_NAME = "odtest01"  # 실제 S3 버킷 이름으로 변경
    FOLDER_NAME = "court_data"        # 원하는 폴더 이름으로 변경
    
    save_dir = 'C:/Users/xoxoq/Downloads/'
    driver = setup_webdriver()
    navigate_to_search_page(driver, court_name="서울중앙지방법원")
    merged_result_df = paginate_and_extract(driver, max_pages=5)
    
    # 원본 데이터 S3 저장
    try:
        save_to_s3(merged_result_df, BUCKET_NAME, f"{FOLDER_NAME}/raw")
    except Exception as e:
        print(f"원본 데이터 S3 저장 중 오류 발생: {e}")
        # 로컬에 백업 저장
        merged_result_df.to_csv(f'{save_dir}court_Data_org.csv')
    
    # 데이터 처리
    if len(merged_result_df) > 0:
        merged_result_df = process_court_data(merged_result_df, save_dir, uuid)
        # 처리된 데이터 S3 저장
        try:
            save_to_s3(merged_result_df, BUCKET_NAME, f"{FOLDER_NAME}/processed")
        except Exception as e:
            print(f"처리된 데이터 S3 저장 중 오류 발생: {e}")
            # 로컬에 백업 저장
            merged_result_df.to_csv(f'{save_dir}court_Data_processed.csv')
    
    driver.quit()
    print("크롤링 종료")