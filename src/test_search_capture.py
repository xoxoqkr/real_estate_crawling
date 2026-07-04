"""
Selenium CDP: land.naver.com에서 단지 검색 후 XHR 캡처
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json

options = Options()
# Use headless=false so we can see what's happening
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
# Disable images for speed
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)

# Enable network performance logging
driver.execute_cdp_cmd("Network.enable", {})

print("1. Loading land.naver.com...")
driver.get("https://land.naver.com/")
time.sleep(3)

# Find search box and type a query
print("2. Finding search box...")
search_box = driver.find_element(By.ID, "queryInputHeader")
print(f"   Found: {search_box.get_attribute('placeholder')}")

print("3. Typing search query '한남더힐'...")
search_box.click()
search_box.clear()
search_box.send_keys("한남더힐")
time.sleep(2)

# Try pressing Enter
print("4. Pressing Enter...")
search_box.send_keys(Keys.ENTER)
time.sleep(5)

print(f"   Current URL: {driver.current_url}")
print(f"   Title: {driver.title}")

# Collect network data
print("\n5. Collecting network requests via Performance API...")
perf_data = driver.execute_script("""
    var entries = performance.getEntriesByType('resource');
    return entries.map(function(e) {
        return {name: e.name, initiatorType: e.initiatorType, duration: e.duration, transferSize: e.transferSize};
    });
""")

print(f"\n=== All Network Requests ({len(perf_data)}) ===")
for entry in perf_data:
    url = entry["name"]
    if any(x in url for x in ["naver.com/api", "complex", "search", "region", "article", "cortar"]):
        print(f"[{entry['initiatorType']}] {entry['transferSize']}B - {url[:300]}")

if not perf_data:
    print("(no resources captured via Performance API)")
    
    # Try getting directly from document
    print("\n=== Checking page source for embedded data ===")
    source = driver.page_source
    
    import re
    # Look for JSON data in <script> tags
    script_pattern = re.compile(r'<script[^>]*>(window\.__[^<]+)</script>', re.IGNORECASE)
    for m in script_pattern.finditer(source):
        print(f"  Found script data: {m.group(1)[:200]}")
    
    # Look for any API urls
    url_pattern = re.compile(r'https?://[^"\'\\\s]+(?:api|complex|search|region|article)[^"\'\\\s]+')
    urls = url_pattern.findall(source)
    for u in sorted(set(urls))[:20]:
        print(f"  URL: {u}")

# Also check by looking at the page content
print("\n6. Page content analysis...")
for selector in [".search_result", ".complex_item", ".result", "[class*='result']", "[class*='list']", "ul", "[class*='Complex']"]:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    if els:
        for el in els[:5]:
            text = el.text.strip()[:100]
            if text:
                c = el.get_attribute("class") or ""
                print(f"  '{selector}' class='{c[:60]}': {text[:80]}")

driver.quit()
