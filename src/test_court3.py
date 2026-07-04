import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, click_button
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

driver = setup_webdriver()

# Go directly to the site
driver.get("https://www.courtauction.go.kr/pgj/index.on")
time.sleep(3)
print('초기 URL:', driver.current_url)

# Save initial HTML
with open('C:/Users/xoxoq/Downloads/court_before.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

# Try selecting court and searching
wait = WebDriverWait(driver, 10)
court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
court_select.select_by_visible_text("서울중앙지방법원")

search_button = wait.until(EC.element_to_be_clickable((By.ID, "mf_btn_quickSearchGds")))
click_button(driver, search_button)

time.sleep(5)
print('검색 후 URL:', driver.current_url)

# Save after HTML
with open('C:/Users/xoxoq/Downloads/court_after.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

# Check for grid_body_row
soup = BeautifulSoup(driver.page_source, 'html.parser')
rows = soup.find_all('tr', class_='grid_body_row')
print('검색 후 grid_body_row:', len(rows))

if rows:
    tds = rows[0].find_all('td')
    for td in tds:
        col_id = td.get('data-col_id')
        text = ' '.join(td.stripped_strings)
        print(f'  {col_id}: {text[:60]}')
else:
    # Check any table/tr
    all_trs = soup.find_all('tr')
    print('전체 tr 개수:', len(all_trs))
    # Check for any class containing grid
    for el in soup.find_all(True):
        cls = el.get('class')
        if cls and any('grid' in c.lower() for c in cls):
            print(f'grid 요소: {el.name}, class={cls}')
    
    # Print all class names found
    all_classes = set()
    for el in soup.find_all(True):
        if el.get('class'):
            all_classes.update(el.get('class'))
    print('모든 클래스 (처음 30):', sorted(all_classes)[:30])

driver.quit()
