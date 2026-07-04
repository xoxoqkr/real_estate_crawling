"""
Selenium으로 네이버 부동산에 접속 → 쿠키 + Authorization 토큰 갱신
"""
import json, time, re
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- 1. Selenium 으로 페이지 열기 ----------
options = Options()
# headless=False 로 해야 정상 로그인/인증 가능
#options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,1024")

# Performance logging 설정 (network request 캡처용)
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("1. 네이버 부동산 접속 중...")
    driver.get("https://new.land.naver.com/")
    time.sleep(5)
    
    # 현재 URL 확인 (로그인 페이지로 리다이렉트되었는지)
    print(f"   현재 URL: {driver.current_url}")
    
    # ---------- 2. 쿠키 추출 ----------
    selenium_cookies = driver.get_cookies()
    print(f"2. 쿠키 추출: {len(selenium_cookies)}개")
    
    cookie_dict = {}
    for c in selenium_cookies:
        cookie_dict[c['name']] = c['value']
    
    # 주요 쿠키 출력 (NNB, NID_SES 등)
    for key in ['NNB', 'NID_SES', 'NID_AUT', 'NID_JKT', 'BUC', 'NAC']:
        if key in cookie_dict:
            print(f"   {key}: {cookie_dict[key][:30]}...")
    
    # ---------- 3. Performance Log 에서 Authorization 토큰 찾기 ----------
    print("3. Performance Log 분석 중 (Bearer 토큰 탐색)...")
    logs = driver.get_log("performance")
    
    bearer_token = None
    api_urls = set()
    
    for entry in logs:
        log_data = json.loads(entry.get('message', '{}'))
        message = log_data.get('message', {})
        method = message.get('method', '')
        
        if method == 'Network.requestWillBeSent':
            request = message.get('params', {}).get('request', {})
            url = request.get('url', '')
            headers = request.get('headers', {})
            
            if 'new.land.naver.com/api/' in url:
                api_urls.add(url)
                auth = headers.get('authorization', '')
                if auth and auth.startswith('Bearer '):
                    bearer_token = auth
                    print(f"   🔑 Bearer 토큰 발견!")
                    print(f"      {bearer_token[:50]}...")
    
    print(f"   API 호출 패턴 ({len(api_urls)}개):")
    for u in list(api_urls)[:5]:
        print(f"      {u[:100]}")
    
    # ---------- 4. 갱신된 값으로 API 테스트 ----------
    print("\n4. API 테스트...")
    
    # 갱신된 헤더
    headers = {
        'accept': '*/*',
        'accept-language': 'ko,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'referer': 'https://new.land.naver.com/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    }
    if bearer_token:
        headers['authorization'] = bearer_token
    
    # 시도 목록 API 호출
    url = 'https://new.land.naver.com/api/regions/list?cortarNo=0000000000'
    r = requests.get(url, headers=headers, cookies=cookie_dict)
    print(f"   응답 코드: {r.status_code}")
    print(f"   응답 내용: {r.text[:200]}")
    
    if r.status_code == 200 and 'regionList' in r.text:
        print("\n✅ API 정상 동작 확인!")
        
        # ---------- 5. 생성된 코드 출력 (복사/붙여넣기 용) ----------
        print("\n" + "="*60)
        print("⬇️  NaverRealestateCrawling.py 에 아래 값 복사")
        print("="*60)
        
        # cookies 문자열 생성
        print("\n# ----- 갱신된 cookies -----")
        print("cookies = {")
        for k, v in cookie_dict.items():
            print(f"    '{k}': '{v}',")
        print("}")
        
        if bearer_token:
            print("\n# ----- 갱신된 Authorization -----")
            print(f"headers['authorization'] = '{bearer_token}'")
        
        # Selenium cookies 네이버 land 용도로 변환
        nv_cookies = {k: v for k, v in cookie_dict.items() 
                      if k in ['NNB', 'NID_SES', 'NID_AUT', 'NID_JKT', 'BUC', 'NAC', 'ASID',
                               'NV_WETR_LOCATION_RGN_M', 'NV_WETR_LAST_ACCESS_RGN_M',
                               'landHomeFlashUseYn', 'nhn.realestate.article.rlet_type_cd',
                               'REALESTATE', '_ga', '_ga_451MFZ9CFM', 'wcs_bt', 'ba.uuid']}
        
        print("\n# ----- NaverRealestateCrawling.py cookies 교체용 -----")
        print("cookies = {")
        for k, v in nv_cookies.items():
            print(f"    '{k}': '{v}',")
        print("}")
    else:
        print("\n❌ API 테스트 실패. 로그인이 필요할 수 있습니다.")
        print("   브라우저 창이 열려있다면 로그인 후 다시 시도하세요.")
        print("   또는 수동으로 Network 탭에서 토큰을 복사하세요.")

finally:
    input("\n계속하려면 Enter 키를 누르세요...")
    driver.quit()
    print("종료")
