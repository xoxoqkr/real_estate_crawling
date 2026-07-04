import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page, extract_results
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = setup_webdriver()
driver.get("https://www.courtauction.go.kr/pgj/index.on")

import time
time.sleep(5)

# Fix the click issue by using JS click directly
from selenium.webdriver.support.ui import Select
court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
court_select.select_by_visible_text("서울중앙지방법원")

search_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "mf_btn_quickSearchGds"))
)
driver.execute_script("arguments[0].click();", search_button)
time.sleep(5)

result_df = extract_results(driver, 3)
print('추출된 행 수:', len(result_df))
print('컬럼:', list(result_df.columns))
if not result_df.empty:
    print(result_df.head(3).to_string())
else:
    print('데이터 없음')

driver.quit()
