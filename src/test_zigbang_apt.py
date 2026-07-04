"""
직방(Zigbang) API - 아파트 매물 조회
"""
import requests, json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Search complex
r = session.get('https://apis.zigbang.com/search?q=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90&serviceType=zigbang&page=1&size=10')
data = r.json()
complex_id = data['items'][0]['id']
source = data['items'][0]['_source']
lat = data['items'][0]['lat']
lng = data['items'][0]['lng']
print(f"Complex ID: {complex_id}")
print(f"lat: {lat}, lng: {lng}")
print()

# Try geohash approach for apartment
import geohash2
geo = geohash2.encode(lat, lng, precision=5)
print(f"Geohash: {geo}")
print()

# Try different 아파트 item APIs
tests = [
    # GET requests
    ('GET', f'https://apis.zigbang.com/v2/items?complex_ids={complex_id}&sales_type=1', None),
    ('GET', f'https://apis.zigbang.com/v2/items/forSale?complexNo={complex_id}', None),
    ('GET', f'https://apis.zigbang.com/v2/complexes/{complex_id}', None),
    ('GET', f'https://apis.zigbang.com/v2/items/apartment?complex_ids={complex_id}', None),
    ('GET', f'https://apis.zigbang.com/v2/items/apartment?geohash={geo}', None),
    ('GET', f'https://apis.zigbang.com/v2/items?geohash={geo}&sales_type=1', None),
    
    # POST requests
    ('POST', 'https://apis.zigbang.com/v2/items/list', {'domain': 'zigbang', 'complex_ids': [complex_id]}),
    ('POST', 'https://apis.zigbang.com/v2/items/list', {'domain': 'zigbang', 'item_ids': []}),
]

for method, url, data in tests:
    try:
        if method == 'GET':
            r = session.get(url, timeout=10)
        else:
            r = session.post(url, data=data, timeout=10)
        
        print(f"[{r.status_code}] {method} {url[:120]}")
        if r.status_code == 200:
            try:
                d = r.json()
                if isinstance(d, dict):
                    print(f"  Keys: {list(d.keys())[:10]}")
                    pre = json.dumps(d, ensure_ascii=False)[:500]
                    print(f"  {pre}")
                elif isinstance(d, list):
                    print(f"  Length: {len(d)}")
                    if d:
                        print(f"  First: {json.dumps(d[0], ensure_ascii=False)[:300]}")
            except:
                print(f"  Text: {r.text[:200]}")
        else:
            print(f"  {r.text[:200]}")
        print()
    except Exception as e:
        print(f"[ERR] {e}")
        print()
