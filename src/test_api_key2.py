"""
API 키 테스트 - 여러 변형 시도
"""
import requests, xml.etree.ElementTree as ET
from urllib.parse import quote

api_key_dec = "2170133e4cf567015f269c06bcc8f2211c6ff6b35a15870fb94e3581f683222f"
api_key_enc = quote(api_key_dec)  # URL-encode

# Try both encoding types
for label, key in [("Decoding", api_key_dec), ("Encoding", api_key_enc)]:
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    params = {
        'serviceKey': key,
        'LAWD_CD': '11680',
        'DEAL_YMD': '202505',
        'pageNo': '1',
        'numOfRows': '5',
    }
    
    r = requests.get(url, params=params, timeout=15)
    print(f"[{label}] Status: {r.status_code}, Body: {r.text[:200]}")
    
    if r.status_code == 200:
        try:
            root = ET.fromstring(r.text)
            result_code = root.findtext('.//resultCode', '')
            print(f"  ResultCode: {result_code}")
            if result_code == '00':
                items = root.findall('.//item')
                print(f"  Items: {len(items)}")
                for item in items[:3]:
                    print(f"    {item.findtext('aptNm','')}: {item.findtext('dealAmount','')}만원")
        except:
            print(f"  Body: {r.text[:500]}")
    print()

# Also try HTTPS
print("=== HTTPS 시도 ===")
for proto in ['https', 'http']:
    url = f"{proto}://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    params = {'serviceKey': api_key_enc, 'LAWD_CD': '11680', 'DEAL_YMD': '202505', 'pageNo': '1', 'numOfRows': '5'}
    try:
        r = requests.get(url, params=params, timeout=15)
        print(f"[{proto}] Status: {r.status_code}, Body: {r.text[:200]}")
    except Exception as e:
        print(f"[{proto}] Error: {e}")
