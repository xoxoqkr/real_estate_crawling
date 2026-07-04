import sys
sys.path.insert(0, 'src')
from CourtRealestateCrawling import setup_webdriver, navigate_to_search_page
import time
from bs4 import BeautifulSoup

driver = setup_webdriver()
navigate_to_search_page(driver, court_name='서울중앙지방법원')
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')

frames = soup.find_all('frame')
iframes = soup.find_all('iframe')
print('프레임 개수:', len(frames), len(iframes))
print('page_title:', soup.title.string if soup.title else 'N/A')

all_classes = set()
for el in soup.find_all(True):
    if el.get('class'):
        for c in el.get('class'):
            all_classes.add(c)
grid_classes = [c for c in all_classes if 'grid' in c.lower() or 'body' in c.lower() or 'row' in c.lower()]
print('관련 클래스:', grid_classes[:20])

text = soup.get_text()
print('페이지 텍스트 길이:', len(text))
print('첫 500자:', text[:500])

driver.quit()
