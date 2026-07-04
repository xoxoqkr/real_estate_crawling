"""
Selenium headless로 land.naver.com 구조 확인 (사용자 프로필 불필요)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time, re

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get("https://land.naver.com/")
time.sleep(3)

print("=== Page Info ===")
print(f"Title: {driver.title}")
print(f"URL: {driver.current_url}")

print("\n=== Page source analysis (API endpoints) ===")
source = driver.page_source
api_pattern = re.compile(r'https?://[^"\'\\\s]+api[^"\'\\\s]+')
matches = api_pattern.findall(source)
for m in sorted(set(matches))[:30]:
    print(f"  {m}")

print("\n=== Search box ===")
for selector in [
    "input[type='text']", 
    "input[class*='search']", 
    "input[class*='Search']",
    "input[placeholder*='검색']",
    "input[placeholder*='단지']",
]:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    if els:
        el = els[0]
        print(f"  Selector '{selector}': id={el.get_attribute('id')}, class={el.get_attribute('class')[:100]}, placeholder={el.get_attribute('placeholder')}")

print("\n=== Link elements (first 30) ===")
links = driver.find_elements(By.TAG_NAME, "a")
for a in links[:30]:
    href = a.get_attribute("href")
    text = a.text.strip()
    if href and text:
        print(f"  {text[:50]}: {href[:100]}")

print("\n=== Important divs ===")
for selector in ["#container", "#content", ".search_area", ".search_result", ".section", "main", "[class*='complex']", "[class*='search']"]:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    if els:
        for el in els[:3]:
            c = el.get_attribute("class") or ""
            i = el.get_attribute("id") or ""
            print(f"  {selector} -> id='{i}' class='{c[:80]}' (children: {len(el.find_elements(By.XPATH, './/*'))})")

driver.quit()
