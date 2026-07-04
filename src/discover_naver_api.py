"""
Selenium으로 land.naver.com 접속 → API 엔드포인트 자동 발견
"""
import json, time, os, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,1024")
options.add_argument("--disable-blink-features=AutomationControlled")
# 네이버 로그인 세션 유지를 위해 기존 프로필 사용
user_profile = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
options.add_argument(f"--user-data-dir={user_profile}")
options.add_argument("--profile-directory=Default")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("1. land.naver.com 접속 중...")
    driver.get("https://land.naver.com/")
    time.sleep(5)
    print(f"   최종 URL: {driver.current_url}")

    # 네트워크 로그 수집
    logs = driver.get_log("performance")
    print(f"   로그: {len(logs)}개")

    # API 요청 패턴 분석
    api_calls = {}  # url -> method, status, headers
    for entry in logs:
        try:
            msg = json.loads(entry['message'])['message']
            method = msg['method']
            params = msg.get('params', {})

            if method == 'Network.requestWillBeSent':
                req = params.get('request', {})
                url = req.get('url', '')
                if 'land.naver.com' in url and 'naver' in url.split('/')[-1]:
                    api_calls[url] = {
                        'method': req.get('method'),
                        'headers': req.get('headers', {}),
                    }
            elif method == 'Network.responseReceived':
                req_url = params.get('request', {}).get('url', '') or params.get('documentURL', '')
                if req_url in api_calls:
                    api_calls[req_url]['status'] = params.get('response', {}).get('status')
                    api_calls[req_url]['type'] = params.get('type', '')
        except:
            pass

    print(f"\n2. 발견된 API 호출 ({len(api_calls)}개):")
    seen_paths = set()
    for url, info in sorted(api_calls.items()):
        path = url.split('land.naver.com', 1)[-1]
        if path not in seen_paths:
            seen_paths.add(path)
            status = info.get('status', '?')
            print(f"   [{status}] {path}")

    # 쿠키 저장
    selenium_cookies = driver.get_cookies()
    with open(os.path.expandvars(r'%TEMP%\naver_cookies.json'), 'w') as f:
        json.dump({c['name']: c['value'] for c in selenium_cookies}, f)
    print(f"\n3. 쿠키 저장 완료 ({len(selenium_cookies)}개)")

    # 페이지에서 API 엔드포인트 패턴 찾기
    print("\n4. 페이지 소스에서 API 패턴 검색...")
    page_source = driver.page_source
    api_patterns = set()
    for m in re.finditer(r'["\'](/[a-zA-Z]+/[a-zA-Z]+\.naver[^"\']*)["\']', page_source):
        api_patterns.add(m.group(1))
    for p in sorted(api_patterns)[:20]:
        print(f"   {p}")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n완료")
