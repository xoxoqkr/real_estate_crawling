"""
Selenium으로 land.naver.com 에 접속 → 모든 API 요청 캡처
사용자 쿠키를 직접 주입해서 로그인 세션 유지
"""
import json, time, os, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 사용자 쿠키
user_cookies = [
    {"name":"NAC","value":"nqjwBswNzc0p","domain":".naver.com"},
    {"name":"NNB","value":"Z4GOMF7VBFYWQ","domain":".naver.com"},
    {"name":"NACT","value":"1","domain":".naver.com"},
    {"name":"NID_AUT","value":"BK+YIg1PG6vWW0DN/3LydbRDSflepvzGXzxccp5ZDCHjW+97PouLVSLiyoX8Y/je","domain":".naver.com"},
    {"name":"NID_SES","value":"AAABoTpeavXbO4Ni9y+H/hG1psDd90e01vKXsQ8W029jBEf88vIT6oG2mATSL21VGIcWZ/C8iOKn7Rp8ZltliWmEadptcIILm2qsaJ4t6KISPiT17j+X6HbNJK5u4sEaZm2sCC8Ze0FkWoYNgSTHJmrdQ6fqq8k275fNvSTFKYBiPfNS4zgaLBA01IvatVb+STg7qKaxK6ydRv7yBE8Qc9U3Q6GP/zMCAOuaoXgWoWJSYUAwo4KaO4d5JHoFcwv7bLzDBFERsyGdBC4+QN/Gnf9WVfsJ2ArOc+vfuN2mKYPCJ6FcqLiTSDydDHbDyRnT1eO88yUqR9oStdtLxQJgXN7Mc7suyu1vNNoyDCj6JoMrN47KG+255MvjeYFsUTYxbgEtjK2DH8ba1YdwHGRj2ZnqGiz4vxytPb+CogOgHmeUXPFn3KE7S6MH95LN5bT0yr3mz7xSPTHpsMiqj+yeHZWbMS1SnB08pXUsmP+N1gbXUgnF1QHxkh3DP222PpGGC3zuRmhDZ6XlI9Fab+LUjrVaNeUwPcggRpzEyY1ODOfC85PIEI1wZb3IWbpcy2lPX6v/og==","domain":".naver.com"},
    {"name":"BUC","value":"Mdilk94CWRPRuXXNJAIZ_jAPLL2v5in9GIOCLabm_C4=","domain":".naver.com"},
    {"name":"JSESSIONID","value":"067C4169427F7AFAEA176275DD00E57A","domain":"land.naver.com"},
    {"name":"landHomeFlashUseYn","value":"Y","domain":"land.naver.com"},
    {"name":"wcs_bt","value":"60717a12f2b3c8:1781314166","domain":".naver.com"},
]

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,1024")
options.add_argument("--disable-blink-features=AutomationControlled")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # 먼저 land.naver.com 에 쿠키 설정을 위해 접속
    print("1. land.naver.com 접속...")
    driver.get("https://land.naver.com")
    time.sleep(2)
    
    # 쿠키 주입
    for c in user_cookies:
        try:
            driver.add_cookie(c)
        except:
            pass
    
    # 새로고침으로 쿠키 적용
    driver.get("https://land.naver.com")
    time.sleep(5)
    
    print(f"   URL: {driver.current_url}")
    print(f"   Title: {driver.title}")
    
    # 페이지에서 링크 클릭 등 인터랙션은 생략하고 로그 수집
    # 이미 로드된 페이지의 네트워크 로그 확인
    logs = driver.get_log("performance")
    print(f"\n2. 네트워크 로그: {len(logs)}개")
    
    # API 엔드포인트 추출
    endpoints = {}  # url -> info
    
    for entry in logs:
        try:
            msg = json.loads(entry['message'])['message']
            method = msg['method']
            params = msg.get('params', {})
            
            url = None
            status = None
            content_type = None
            
            if method == 'Network.responseReceived':
                response = params.get('response', {})
                url = response.get('url', '')
                status = response.get('status', 0)
                content_type = (response.get('mimeType', '') or '').lower()
                
                if 'land.naver.com' in url and url != 'https://land.naver.com/':
                    if status == 200 and ('json' in content_type or 'naver' in url.split('/')[-1]):
                        if url not in endpoints:
                            endpoints[url] = {'status': status, 'type': content_type, 'method': 'GET'}
        except:
            pass
    
    print(f"\n3. 발견된 JSON/API 엔드포인트 ({len(endpoints)}개):")
    for url in sorted(endpoints.keys()):
        path = url.split('land.naver.com', 1)[-1]
        info = endpoints[url]
        print(f"   [{info['status']}] {path}  ({info['type']})")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n완료")
