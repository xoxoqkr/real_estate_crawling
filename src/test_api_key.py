"""
API 키 테스트 - 강남구 실거래가 조회
"""
import requests, xml.etree.ElementTree as ET

api_key = "2170133e4cf567015f269c06bcc8f2211c6ff6b35a15870fb94e3581f683222f"

url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
params = {
    'serviceKey': api_key,
    'LAWD_CD': '11680',  # 강남구
    'DEAL_YMD': '202505',  # 2025년 5월
    'pageNo': '1',
    'numOfRows': '10',
}

print(f"요청 URL: {url}")
print(f"Params: LAWD_CD=11680(강남구), DEAL_YMD=202505")
print()

r = requests.get(url, params=params, timeout=15)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"Body length: {len(r.text)}")
print()

if r.status_code == 200:
    # Try parsing XML
    try:
        root = ET.fromstring(r.text)
        result_code = root.findtext('.//resultCode', '')
        result_msg = root.findtext('.//resultMsg', '')
        total_count = root.findtext('.//totalCount', '0')
        print(f"Result Code: {result_code}")
        print(f"Result Msg: {result_msg}")
        print(f"Total Count: {total_count}")
        
        items = root.findall('.//item')
        print(f"\nItems returned: {len(items)}")
        for item in items[:5]:
            apt_nm = item.findtext('aptNm', '')
            amount = item.findtext('dealAmount', '')
            area = item.findtext('excluUseAr', '')
            umd = item.findtext('umdNm', '')
            floor = item.findtext('floor', '')
            year = item.findtext('dealYear', '')
            month = item.findtext('dealMonth', '')
            day = item.findtext('dealDay', '')
            print(f"  {apt_nm} | {amount}만원 | {area}㎡ | {umd} | {floor}층 | {year}-{month}-{day}")
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        print(f"Body: {r.text[:1000]}")
else:
    print(f"Error: {r.text[:1000]}")
