import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, paginate_and_extract, extract_results, process_court_data
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import uuid

driver = setup_webdriver()
driver.get("https://www.courtauction.go.kr/pgj/index.on")
time.sleep(5)

# Click search properly
court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
court_select.select_by_visible_text("서울중앙지방법원")

search_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "mf_btn_quickSearchGds"))
)
driver.execute_script("arguments[0].click();", search_button)
time.sleep(5)

print('=== paginate_and_extract test (1 page) ===')
result_df = paginate_and_extract(driver, max_pages=1, loading_wait_time_sec=3)
print('Result rows:', len(result_df))
print('Columns:', list(result_df.columns))

if not result_df.empty:
    print(result_df[['printCsNo', 'maemulSer', 'printSt']].head(5).to_string())
    
    print('\n=== process_court_data test ===')
    uid = str(uuid.uuid4())
    processed = process_court_data(result_df, 'C:/Users/xoxoq/Downloads/', uid)
    print('Processed rows:', len(processed))
    print(processed[['사건번호', '물건주소']].head(5).to_string())
    
    # Save
    processed.to_csv('C:/Users/xoxoq/Downloads/court_final_test.csv', encoding='CP949')
    print('Saved to court_final_test.csv')

driver.quit()
