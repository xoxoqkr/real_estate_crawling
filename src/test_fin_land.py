"""
Selenium CDP로 fin.land.naver.com 네트워크 요청 캡처
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time, json

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

# Enable network logging via CDP
driver.execute_cdp_cmd("Network.enable", {})

# Collect network requests
requests_log = []
def log_request(request):
    if "api" in request["request"]["url"] or "complex" in request["request"]["url"]:
        requests_log.append(request["request"]["url"])

driver.request_interceptor = log_request

# Visit fin.land.naver.com
print("=== Loading fin.land.naver.com ===")
driver.get("https://fin.land.naver.com/")
time.sleep(5)

print(f"Title: {driver.title}")
print(f"URL: {driver.current_url}")

# Wait more for async requests
time.sleep(3)

# Get performance logs
logs = driver.execute_cdp_cmd("Network.getCookies", {})
print(f"\nCookies: {len(logs)}")

# Get all network requests from performance log
perf_logs = driver.execute_cdp_cmd("Performance.getMetrics", {})
print(f"\nPerformance metrics: {perf_logs.keys() if isinstance(perf_logs, dict) else 'N/A'}")

# Collect all XHR/fetch requests from the browser's performance log
# We need to use the DevTools protocol to capture network events
# Let's do it properly with CDP listeners
driver.quit()

# Now try with proper CDP event listeners
print("\n\n=== Second attempt with proper CDP listeners ===")
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver2 = webdriver.Chrome(options=options)
network_requests = []

def capture_request(request):
    network_requests.append(request)

# Set up CDP listener for network requests
driver2.execute_cdp_cmd("Network.enable", {})
driver2.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

# Start listening
driver2.get("https://fin.land.naver.com/")
time.sleep(8)

# Extract network logs via JavaScript performance API
perf_data = driver2.execute_script("""
    var entries = performance.getEntriesByType('resource');
    return entries.map(function(e) {
        return {name: e.name, initiatorType: e.initiatorType, duration: e.duration};
    });
""")

print(f"\n=== Network requests ({len(perf_data)}) ===")
for entry in perf_data:
    url = entry["name"]
    if "api" in url.lower() or "complex" in url.lower() or "search" in url.lower() or "region" in url.lower() or "article" in url.lower():
        print(f"[{entry['initiatorType']}] {url[:200]}")

# Print all APIs found
print("\n=== All API-like requests ===")
for entry in perf_data:
    url = entry["name"]
    if any(x in url.lower() for x in ["api", "complex", "search", "region", "article", "list", "detail"]):
        print(f"  {url[:250]}")

driver2.quit()
