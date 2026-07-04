"""
Selenium으로 land.naver.com 현재 구조 확인
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json, time

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=C:\\Users\\xoxoq\\AppData\\Local\\Google\\Chrome\\User Data")
options.add_argument("--profile-directory=Default")
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(options=options)
driver.get("https://land.naver.com/")

# Wait for page to load
time.sleep(3)

# Get all network requests captured (Selenium doesn't do this directly)
# Instead, let's look at the page structure
print("=== Page Title ===")
print(driver.title)

print("\n=== Current URL ===")
print(driver.current_url)

print("\n=== Searching for API endpoints in page source ===")
page_source = driver.page_source

# Look for any embedded JSON data
import re
matches = re.findall(r'https?://[^"\'\\]+api[^"\'\\]+', page_source)
for m in matches[:20]:
    print(f"  API: {m}")

# Look for script tags with data
scripts = driver.find_elements(By.TAG_NAME, "script")
print(f"\n=== Script tags: {len(scripts)} ===")
for s in scripts:
    src = s.get_attribute("src")
    if src and ("api" in src or "config" in src or "env" in src):
        print(f"  Script: {src}")

# Check if search element exists
try:
    search = driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[placeholder*='검색'], input.SearchBox")
    print(f"\n=== Search box found ===")
    print(f"  Name: {search.get_attribute('name')}")
    print(f"  Placeholder: {search.get_attribute('placeholder')}")
    print(f"  Class: {search.get_attribute('class')}")
except:
    print("\n=== Search box NOT found by common selectors ===")

# Try to find any meaningful divs
for selector in [".complex_list", ".article_list", ".search_result", "#container", "#content", ".content", "main"]:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    if els:
        print(f"\n=== Found '{selector}': {len(els)} elements ===")

driver.quit()
