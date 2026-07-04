"""
Selenium CDP: m.land.naver.com 검색 후 XHR 캡처
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time, json

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=430,932")  # Mobile viewport
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Network.enable", {})

print("1. Loading m.land.naver.com...")
driver.get("https://m.land.naver.com/")
time.sleep(3)

print(f"   URL: {driver.current_url}")
print(f"   Title: {driver.title}")

# Find search box
print("\n2. Looking for search element...")
for selector in ["#query", "input[type='text']", "input", "[class*='search']", "[class*='Search']"]:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    if els:
        el = els[0]
        tag = el.tag_name
        pid = el.get_attribute("id") or ""
        pclass = el.get_attribute("class") or ""
        ph = el.get_attribute("placeholder") or ""
        print(f"   '{selector}': <{tag}> id='{pid}' class='{pclass[:60]}' placeholder='{ph}'")

# Maybe it's a different navigation pattern
print("\n3. Checking page structure...")
els = driver.find_elements(By.CSS_SELECTOR, "a, button, [onclick]")
for el in els[:20]:
    text = el.text.strip()
    href = el.get_attribute("href") or ""
    onclick = el.get_attribute("onclick") or ""
    if text or href or onclick:
        print(f"   text='{text[:30]}' href='{href[:80]}' onclick='{onclick[:80]}'")

# Collect network requests
time.sleep(2)
perf = driver.execute_script("""
    return performance.getEntriesByType('resource').map(function(e) {
        return {name: e.name, initiatorType: e.initiatorType};
    });
""")

print(f"\n4. Network requests captured ({len(perf)}):")
for p in perf:
    url = p['name']
    if 'api' in url.lower() or 'complex' in url.lower() or 'search' in url.lower() or 'region' in url.lower() or 'article' in url.lower() or 'cortar' in url.lower():
        print(f"   [{p['initiatorType']}] {url[:300]}")

if not perf:
    print("   (none captured via Performance API)")

# Try to navigate to search
print("\n5. Try navigating to search page...")
driver.get("https://m.land.naver.com/search")
time.sleep(3)
print(f"   URL: {driver.current_url}")

perf2 = driver.execute_script("""
    return performance.getEntriesByType('resource').map(function(e) {
        return {name: e.name, initiatorType: e.initiatorType};
    });
""")

print(f"\n6. Network requests on /search ({len(perf2)}):")
for p in perf2:
    url = p['name']
    if any(x in url.lower() for x in ['api', 'complex', 'search', 'region', 'article', 'cortar', 'list']):
        print(f"   [{p['initiatorType']}] {url[:300]}")

driver.quit()
