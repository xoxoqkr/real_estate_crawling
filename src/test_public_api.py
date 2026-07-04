"""
국토교통부 실거래가 API 테스트
- 공공데이터포털 Open API (아파트매매 실거래자료)
- 대안: rt.molit.go.kr 웹 스크래핑
"""
import requests, json, xmltodict, re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
})

# ========== 방법 1: rt.molit.go.kr 스크래핑 (API 키 불필요) ==========
print("=== 방법 1: rt.molit.go.kr 스크래핑 ===")

# 실거래가 공개 시스템
urls = [
    'https://rt.molit.go.kr/',
    'https://rt.molit.go.kr/srh/search.do',
    'https://rt.molit.go.kr/srh/getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202505',
    'https://rt.molit.go.kr/srv/getRTMSDataSvcAptTrade?LAWD_CD=11620&DEAL_YMD=202505',
]

for url in urls:
    try:
        r = session.get(url, timeout=10)
        print(f'[{r.status_code}] {url}')
        if r.status_code == 200:
            print(f'  Size: {len(r.text)} bytes')
            # Check if XML or HTML
            if r.text.strip().startswith('<?xml') or r.text.strip().startswith('<response'):
                print(f'  XML: {r.text[:500]}')
            else:
                title = re.search(r'<title>(.*?)</title>', r.text)
                print(f'  Title: {title.group(1) if title else "N/A"}')
                print(f'  Preview: {r.text[:300]}')
        else:
            print(f'  {r.text[:200]}')
        print()
    except Exception as e:
        print(f'[ERR] {url}: {e}')
        print()

# ========== 방법 2: data.go.kr 오픈 API (API 키 필요) ==========
print("=== 방법 2: data.go.kr 실거래가 API ===")

# The user might need to get a key from https://www.data.go.kr/data/15058747/openapi.do
# Service key is typically needed

# Try without API key first (some endpoints are open)
base = 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTrade'
params = {
    'LAWD_CD': '11680',  # 강남구
    'DEAL_YMD': '202505',  # 2025년 5월
    'serviceKey': '',  # empty - will fail but shows the format
    'numOfRows': '10',
    'pageNo': '1',
}

r = session.get(base, params=params, timeout=10)
print(f'[{r.status_code}] OpenAPI endpoint')
print(f'  URL: {r.url[:200]}')
print(f'  Response: {r.text[:500]}')
