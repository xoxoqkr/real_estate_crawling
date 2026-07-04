import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page
import time
from bs4 import BeautifulSoup

driver = setup_webdriver()
navigate_to_search_page(driver, court_name='서울중앙지방법원')
time.sleep(5)

# Print current URL
print('현재 URL:', driver.current_url)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Check for any iframes
iframes = driver.find_elements(By.TAG_NAME, 'iframe')
print('iframe 개수:', len(iframes))
for i, iframe in enumerate(iframes):
    print(f'  iframe[{i}]: id={iframe.get_attribute("id")}, name={iframe.get_attribute("name")}, src={iframe.get_attribute("src")[:100] if iframe.get_attribute("src") else "N/A"}')

frames = driver.find_elements(By.TAG_NAME, 'frame')
print('frame 개수:', len(frames))
for i, frame in enumerate(frames):
    print(f'  frame[{i}]: id={frame.get_attribute("id")}, name={frame.get_attribute("name")}, src={frame.get_attribute("src")[:100] if frame.get_attribute("src") else "N/A"}')

# Check page source for relevant elements
soup = BeautifulSoup(driver.page_source, 'html.parser')
# Look for login-related elements
login_els = soup.find_all(['input', 'button', 'a'], {'id': lambda x: x and ('login' in x.lower() or 'Login' in x)})
print('로그인 관련 요소:', len(login_els))

# Check for search button
search_btn = soup.find(['button', 'input', 'a'], {'id': lambda x: x and 'search' in x.lower()})
print('검색 버튼 있음:', search_btn is not None)
if search_btn:
    print('  tag:', search_btn.name, 'id:', search_btn.get('id'))

driver.quit()
