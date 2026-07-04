import requests

api_key = '2170133e4cf567015f269c06bcc8f2211c6ff6b35a15870fb94e3581f683222f'

tests = [
    ('202504', '11680'),
    ('202503', '11680'),
    ('202502', '11680'),
    ('202501', '11680'),
    ('202412', '11680'),
    ('202505', '11110'),  # 종로구
]

for ymd, lawd in tests:
    url = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade'
    params = {'serviceKey': api_key, 'LAWD_CD': lawd, 'DEAL_YMD': ymd}
    r = requests.get(url, params=params, timeout=15)
    print(f'LAWD={lawd} YMD={ymd}: Status={r.status_code}', end='')
    if r.status_code == 200:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        code = root.findtext('.//resultCode', '')
        msg = root.findtext('.//resultMsg', '')
        total = root.findtext('.//totalCount', '0')
        items = len(root.findall('.//item'))
        print(f' Code={code} Msg={msg} Total={total} Items={items}')
    else:
        print(f' Body={r.text[:200]}')
