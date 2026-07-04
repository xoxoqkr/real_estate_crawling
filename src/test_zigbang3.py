"""
직방(Zigbang) API - 매물 리스트 조회 v2
"""
import requests, json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Search complex
r = session.get('https://apis.zigbang.com/search?q=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90&serviceType=zigbang&page=1&size=10')
data = r.json()
item = data['items'][0]
complex_id = item['id']
complex_name = item['name']
source = item['_source']
print(f"Complex: {complex_name} (id={complex_id})")
print(f"Address: {source.get('address2', '')} {source.get('address', '')}")
print()

# Try different item listing APIs
urls = [
    f'https://apis.zigbang.com/v2/items?complex_ids={complex_id}&sales_type=1&page=1&size=20',
    f'https://apis.zigbang.com/v2/items?complex_ids={complex_id}&page=1&size=20',
    f'https://api.zigbang.com/v1/items?complex_id={complex_id}&page=1&size=20',
    f'https://www.zigbang.com/api/items/list?complex_id={complex_id}&sales_type=1',
    f'https://www.zigbang.com/v2/api/items?complex_ids={complex_id}',
    f'https://apis.zigbang.com/v2/items/forSale?complexNo={complex_id}',
    f'https://apis.zigbang.com/v2/complexes/{complex_id}/items',
]

for url in urls:
    try:
        r = session.get(url, timeout=10)
        print(f"[{r.status_code}] {url[:120]}...")
        if r.status_code == 200:
            d = r.json() if r.text.startswith('{') or r.text.startswith('[') else None
            if d:
                if isinstance(d, dict):
                    print(f"  Keys: {list(d.keys())[:10]}")
                    if 'items' in d and d['items']:
                        print(f"  Items: {len(d['items'])}")
                        print(f"  Sample: {json.dumps(d['items'][0], ensure_ascii=False)[:500]}")
                    elif 'data' in d and d['data']:
                        print(f"  Data: {json.dumps(d['data'][:2], ensure_ascii=False)[:500]}")
                    else:
                        print(f"  Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
                elif isinstance(d, list):
                    print(f"  List length: {len(d)}")
                    if d:
                        print(f"  First: {json.dumps(d[0], ensure_ascii=False)[:500]}")
            else:
                print(f"  Text: {r.text[:200]}")
        else:
            print(f"  Error: {r.text[:200]}")
        print()
    except Exception as e:
        print(f"[ERR] {e}")
        print()

# Also try 네이버 부동산 통합검색 API 
# (from m.land.naver.com/search JS bundle)
print("=== Naver search APIs ===")
naver_urls = [
    ('https://m.land.naver.com/search/autoCompleteProxy', 
     {'keyword': '한남더힐', 'keywordType': 'COMPLEX'}),
    ('https://m.land.naver.com/search/moreList', 
     {'page': 1, 'size': 20, 'query': '한남더힐', 'searchType': 'COMPLEX'}),
    ('https://m.land.naver.com/search/searchAutoCompleteAddress', 
     {'keyword': '한남더힐'}),
]

for url, params in naver_urls:
    try:
        r = session.get(url, params=params, timeout=10)
        print(f"[{r.status_code}] {url}")
        if r.status_code == 200:
            try:
                d = r.json()
                print(f"  {json.dumps(d, ensure_ascii=False)[:500]}")
            except:
                print(f"  {r.text[:200]}")
        else:
            print(f"  {r.text[:200]}")
        print()
    except Exception as e:
        print(f"[ERR] {e}")
        print()
