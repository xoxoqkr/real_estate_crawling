import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, click_button
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

driver = setup_webdriver()
driver.get("https://www.courtauction.go.kr/pgj/index.on")
time.sleep(5)

# Try switching to main frame if it exists
wait = WebDriverWait(driver, 10)

# Check for any alerts
try:
    alert = driver.switch_to.alert
    print('Alert found:', alert.text)
    alert.accept()
except:
    print('No alert')

# Check current URL
print('Current URL:', driver.current_url)

# Check available select options
try:
    court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
    options = [o.text for o in court_select.options]
    print('법원 선택 옵션:', options[:10])
except Exception as e:
    print('Select error:', e)

# Select court and search
court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
court_select.select_by_visible_text("서울중앙지방법원")
print('Selected 서울중앙지방법원')

search_button = wait.until(EC.element_to_be_clickable((By.ID, "mf_btn_quickSearchGds")))
print('Search button found, clicking...')

# Try direct click first
try:
    search_button.click()
    print('Direct click worked')
except Exception as e:
    print('Direct click failed:', e)
    driver.execute_script("arguments[0].click();", search_button)
    print('JS click done')

time.sleep(8)

# Check for alerts after click
try:
    alert = driver.switch_to.alert
    print('Post-click Alert:', alert.text)
    alert.accept()
except:
    print('Post-click: No alert')

# Check page after search
soup = BeautifulSoup(driver.page_source, 'html.parser')
rows = soup.find_all('tr', class_='grid_body_row')
print('grid_body_row after search:', len(rows))

# Check iframe
iframes = driver.find_elements(By.TAG_NAME, 'iframe')
print('iframes:', len(iframes))
for i, f in enumerate(iframes):
    print(f'  [{i}] id={f.get_attribute("id")}, name={f.get_attribute("name")}')

# Try switching to each iframe to find the grid
for i, iframe in enumerate(iframes):
    try:
        driver.switch_to.frame(iframe)
        print(f'Switched to iframe {i}')
        inner = BeautifulSoup(driver.page_source, 'html.parser')
        rows = inner.find_all('tr', class_='grid_body_row')
        print(f'  grid_body_row in iframe {i}: {len(rows)}')
        if rows:
            tds = rows[0].find_all('td')
            for td in tds[:5]:
                print(f'    {td.get("data-col_id")}: {td.get_text(strip=True)[:50]}')
        driver.switch_to.default_content()
    except:
        driver.switch_to.default_content()
        print(f'Could not switch to iframe {i}')

# Check mainFrame by name
try:
    driver.switch_to.frame('main')
    print('Switched to frame main')
    inner = BeautifulSoup(driver.page_source, 'html.parser')
    rows = inner.find_all('tr', class_='grid_body_row')
    print(f'  grid_body_row in frame main: {len(rows)}')
    driver.switch_to.default_content()
except:
    driver.switch_to.default_content()
    print('No frame named main')

# Try mf_wfm_mainFrame
try:
    main_frame = driver.find_element(By.ID, 'mf_wfm_mainFrame')
    print(f'mf_wfm_mainFrame found, tag={main_frame.tag_name}')
    driver.switch_to.frame(main_frame)
    print('Switched to mf_wfm_mainFrame')
    inner = BeautifulSoup(driver.page_source, 'html.parser')
    rows = inner.find_all('tr', class_='grid_body_row')
    print(f'  grid_body_row in mf_wfm_mainFrame: {len(rows)}')
    if rows:
        tds = rows[0].find_all('td')
        for td in tds[:5]:
            print(f'    {td.get("data-col_id")}: {td.get_text(strip=True)[:50]}')
    driver.switch_to.default_content()
except Exception as e:
    driver.switch_to.default_content()
    print('Could not switch to mf_wfm_mainFrame:', e)

driver.quit()
