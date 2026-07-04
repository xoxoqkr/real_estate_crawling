"""
기존 Chrome 프로필(로그인 세션) 재사용 → 쿠키/토큰 추출
"""
import json, time, os, requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 사용자 Chrome 프로필 경로
user_profile = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
print(f"Chrome 프로필: {user_profile}")

options = Options()
options.add_argument(f"--user-data-dir={user_profile}")
options.add_argument("--profile-directory=Default")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,1024")
options.add_argument("--disable-blink-features=AutomationControlled")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    url = "https://new.land.naver.com/complexes/8928?ms=37.482968,127.0634,16&a=APT&b=A1&e=RETAIL"
    print(f"1. 접속: {url}")
    driver.get(url)
    time.sleep(5)
    print(f"   최종 URL: {driver.current_url[:80]}")
    print(f"   페이지 타이틀: {driver.title}")

    # 쿠키 추출
    selenium_cookies = driver.get_cookies()
    cookie_dict = {}
    for c in selenium_cookies:
        cookie_dict[c['name']] = c['value']
    print(f"2. 쿠키: {len(selenium_cookies)}개")
    print(f"   주요 키: {sorted(cookie_dict.keys())}")

    # Performance Log → Bearer 토큰 찾기
    print("3. Performance Log 분석...")
    logs = driver.get_log("performance")
    print(f"   로그: {len(logs)}개")

    bearer_token = None
    api_urls = set()
    for entry in logs:
        try:
            msg = json.loads(entry.get('message', '{}'))
            m = msg.get('message', {})
            if m.get('method') == 'Network.requestWillBeSent':
                req = m.get('params', {}).get('request', {})
                req_url = req.get('url', '')
                if 'new.land.naver.com/api/' in req_url:
                    api_urls.add(req_url)
                    auth = req.get('headers', {}).get('authorization', '')
                    if auth.startswith('Bearer '):
                        bearer_token = auth
        except:
            pass

    print(f"   API 호출: {len(api_urls)}개")
    if bearer_token:
        print(f"   ✅ Bearer 토큰: {bearer_token[:50]}...")
    else:
        print("   ❌ Bearer 토큰 없음")

    # 4. 추출된 값으로 API 테스트
    print("\n4. API 테스트...")
    test_headers = {
        'accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'referer': 'https://new.land.naver.com/',
    }
    if bearer_token:
        test_headers['authorization'] = bearer_token

    r = requests.get(
        'https://new.land.naver.com/api/regions/list?cortarNo=0000000000',
        headers=test_headers, cookies=cookie_dict, timeout=10
    )
    print(f"   상태코드: {r.status_code}")
    if r.status_code == 200:
        data = json.loads(r.text)
        regions = [x['cortarNo'] for x in data['regionList']]
        print(f"   ✅ 성공! 시도: {regions[:5]}")

        # NaverRealestateCrawling.py 용 cookies 포맷 출력
        print("\n" + "="*60)
        print("[NaverRealestateCrawling.py 갱신 값]")
        print("="*60)

        relevant_keys = ['NNB', 'NID_SES', 'NID_AUT', 'NID_JKT', 'ASID',
                         'NV_WETR_LOCATION_RGN_M', 'NV_WETR_LAST_ACCESS_RGN_M',
                         'BUC', 'NAC', 'NACT', '_ga', '_ga_451MFZ9CFM',
                         'wcs_bt', 'ba.uuid', 'landHomeFlashUseYn',
                         'nhn.realestate.article.rlet_type_cd', 'REALESTATE',
                         'realestate.beta.lastclick.cortar']
        filtered = {k: v for k, v in cookie_dict.items() if k in relevant_keys}

        print("\ncookies = {")
        for k, v in filtered.items():
            print(f"    '{k}': '{v}',")
        print("}")

        if bearer_token:
            print(f"\n# headers authorization 갱신")
            print(f"headers['authorization'] = '{bearer_token}'")

        # 파일 자동 갱신
        import NaverRealestateCrawling as nv_mod
        nv_path = os.path.join(os.path.dirname(nv_mod.__file__), 'NaverRealestateCrawling.py')
        print(f"\n5. 파일 자동 갱신: {nv_path}")

        with open(nv_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # cookies 교체
        import re
        cookie_start = content.find("cookies = {")
        if cookie_start > 0:
            cookie_end = content.find("}", cookie_start)
            new_cookies = "cookies = {\n"
            for k, v in filtered.items():
                new_cookies += f"    '{k}': '{v}',\n"
            new_cookies += "}"
            content = content[:cookie_start] + new_cookies + content[cookie_end+1:]
            print("   ✅ cookies 갱신 완료")

        # authorization 교체
        if bearer_token:
            auth_pattern = r"(headers\['authorization'\]\s*=\s*)'.*?'"
            if re.search(auth_pattern, content):
                content = re.sub(auth_pattern, f"\\1'{bearer_token}'", content)
                print("   ✅ authorization 갱신 완료")

        with open(nv_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("\n✅ 자동 갱신 완료!")
    else:
        print(f"   ❌ 실패: {r.text[:300]}")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n종료")
