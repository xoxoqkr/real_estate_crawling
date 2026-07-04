"""
Selenium Performance Log 로 네이버 부동산 API 토큰 추출 (자동)
"""
import json, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,1024")
options.add_argument("--disable-blink-features=AutomationControlled")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 여러 URL 시도
urls = [
    "https://new.land.naver.com/complexes/8928?ms=37.482968,127.0634,16&a=APT&b=A1&e=RETAIL",
    "https://new.land.naver.com/",
]

for url in urls:
    print(f"\n1. 접속: {url}")
    driver.get(url)
    time.sleep(5)
    print(f"   현재 URL: {driver.current_url}")

    print("2. 쿠키 추출 중...")
    selenium_cookies = driver.get_cookies()
    cookie_dict = {}
    for c in selenium_cookies:
        cookie_dict[c['name']] = c['value']
    print(f"   쿠키: {len(selenium_cookies)}개, 주요 키: {[k for k in cookie_dict.keys()][:10]}")

    print("3. Performance Log 분석 중...")
    logs = driver.get_log("performance")
    print(f"   로그 항목: {len(logs)}개")

    bearer_token = None
    api_urls = set()

    for entry in logs:
        msg = json.loads(entry.get('message', '{}'))
        msg_msg = msg.get('message', {})
        method = msg_msg.get('method', '')
        
        if method == 'Network.requestWillBeSent':
            req = msg_msg.get('params', {}).get('request', {})
            req_url = req.get('url', '')
            req_headers = req.get('headers', {})
            
            if 'new.land.naver.com/api/' in req_url:
                api_urls.add(req_url)
                auth = req_headers.get('authorization', '')
                if auth and auth.startswith('Bearer '):
                    bearer_token = auth

    print(f"   API 호출: {len(api_urls)}개")
    if bearer_token:
        print(f"   ✅ Bearer 토큰 발견!")
        print(f"      {bearer_token[:60]}...")

    if api_urls:
        print(f"\n   API 호출 목록 (처음 5개):")
        for u in list(api_urls)[:5]:
            print(f"      {u[:120]}")
        break
    else:
        print("   API 호출이 없습니다. 다른 URL 시도...")

if bearer_token:
    print("\n" + "="*60)
    print("[갱신된 인증 정보]")
    print("="*60)
    
    print("\n# cookies (NaverRealestateCrawling.py 교체용):")
    print("cookies = {")
    for k, v in cookie_dict.items():
        print(f"    '{k}': '{v}',")
    print("}")
    
    print(f"\n# headers authorization:")
    print(f"headers['authorization'] = '{bearer_token}'")
    
    # test
    import requests
    print("\n\n4. API 테스트...")
    test_headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'referer': 'https://new.land.naver.com/',
        'authorization': bearer_token,
    }
    r = requests.get('https://new.land.naver.com/api/regions/list?cortarNo=0000000000',
                     headers=test_headers, cookies=cookie_dict)
    print(f"   상태: {r.status_code}")
    if r.status_code == 200:
        import pandas as pd
        data = json.loads(r.text)
        regions = [x['cortarNo'] for x in data['regionList']]
        print(f"   ✅ 성공! 시도 목록: {regions[:5]}")
    else:
        print(f"   ❌ 실패: {r.text[:200]}")
else:
    print("\n❌ Bearer 토큰을 찾을 수 없습니다.")
    print("브라우저에서 직접 DevTools로 확인하세요:")
    print("1. Chrome으로 https://new.land.naver.com 접속")
    print("2. F12 → Network 탭")
    print("3. 새로고침")
    print("4. 'api' 필터 → 아무 요청 클릭")
    print("5. Request Headers에서 'authorization: Bearer ...' 복사")

driver.quit()
