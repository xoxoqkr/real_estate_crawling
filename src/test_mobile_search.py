"""
Selenium mobile emulation: m.land.naver.com 검색
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=430,932")
# Set mobile user-agent
options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

driver = webdriver.Chrome(options=options)

# Navigate to search page with query
print("1. Loading search page...")
driver.get("https://m.land.naver.com/search?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90")
time.sleep(5)

print(f"   URL: {driver.current_url}")
print(f"   Title: {driver.title}")

# Check if we got redirected to 404
if "404" in driver.current_url:
    print("   -> Redirected to 404!")
    
    # Try homepage first, then search
    print("\n2. Trying homepage first...")
    driver.get("https://m.land.naver.com/")
    time.sleep(3)
    print(f"   URL: {driver.current_url}")
    
    # Look for search box and type
    for selector in ["#query", "input[type='text']", "input", ".search_box input", "[class*='search'] input"]:
        els = driver.find_elements(By.CSS_SELECTOR, selector)
        if els:
            el = els[0]
            print(f"   Found input: tag={el.tag_name} id={el.get_attribute('id')} class={el.get_attribute('class')[:50]}")
            el.send_keys("한남더힐")
            el.submit()
            time.sleep(5)
            print(f"   After submit URL: {driver.current_url}")
            break

# Collect page content
print(f"\n3. Current page analysis...")
print(f"   URL: {driver.current_url}")
print(f"   Title: {driver.title}")

# Look for any complex/article data
els = driver.find_elements(By.CSS_SELECTOR, "[class*='complex'], [class*='item'], [class*='list'], li, [class*='result'], [class*='card'], a")
print(f"   Found {len(els)} potential data elements")

complexes = []
for el in els[:50]:
    text = el.text.strip()
    href = el.get_attribute("href") or ""
    if text and len(text) > 3:
        print(f"   text='{text[:60]}' href='{href[:80]}'")

# Get network requests
perf = driver.execute_script("""
    return performance.getEntriesByType('resource').map(function(e) {
        return {name: e.name, initiatorType: e.initiatorType, transferSize: e.transferSize};
    });
""")
print(f"\n4. Network requests ({len(perf)}):")
for p in perf:
    url = p['name']
    if any(x in url for x in ['api', 'naver', 'complex', 'search', 'region', 'article', 'list']):
        print(f"   [{p['initiatorType']}] {p['transferSize']}B {url[:250]}")

driver.quit()
