"""
직방(Zigbang) API - 매물 리스트 조회
"""
import requests, json

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Step 1: Search complex
print("=== Step 1: Search complex ===")
r = session.get('https://apis.zigbang.com/search?q=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90&serviceType=zigbang&page=1&size=10')
data = r.json()
complex_id = data['items'][0]['id']
complex_name = data['items'][0]['name']
print(f"Complex: {complex_name} (id={complex_id})")
print(f"Address: {data['items'][0]['_source']['address']}")
print()

# Step 2: Get complex detail
print("=== Step 2: Complex detail ===")
r2 = session.get(f'https://apis.zigbang.com/v2/complexes/{complex_id}')
if r2.status_code == 200:
    detail = r2.json()
    print(json.dumps(detail, ensure_ascii=False, indent=2)[:2000])
else:
    print(f"[{r2.status_code}] {r2.text[:200]}")
print()

# Step 3: Get items (매매 listings)
print("=== Step 3: Get 매매 items ===")
# Try various API patterns
endpoints = [
    f'https://apis.zigbang.com/v2/items?complex_ids={complex_id}&sales_type=1&page=1&size=20',
    f'https://apis.zigbang.com/v2/items?complexNo={complex_id}&tradeTypeCode=A1&page=1&size=20',
    f'https://api.zigbang.com/v1/items?complex_id={complex_id}&type=apartment&page=1&size=20',
    f'https://www.zigbang.com/api/items?complex_id={complex_id}&sales_type=1',
]

for url in endpoints:
    try:
        r = session.get(url, timeout=10)
        print(f"[{r.status_code}] {url[:100]}...")
        if r.status_code == 200:
            d = r.json()
            print(f"  Keys: {list(d.keys())[:10]}" if isinstance(d, dict) else f"  Type: {type(d).__name__}, Len: {len(d)}")
            if isinstance(d, dict) and 'items' in d:
                items = d['items']
                print(f"  Items count: {len(items)}")
                if items:
                    print(f"  First item: {json.dumps(items[0], ensure_ascii=False)[:500]}")
            else:
                print(f"  Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
        print()
    except Exception as e:
        print(f"[ERR] {url[:80]}: {e}")
        print()

# Step 4: Try the item detail API
print("=== Step 4: Try item detail ===")
# Zigbang has /v2/items/{itemNo} for detail
# First find an item
r_items = session.get(f'https://www.zigbang.com/api/items?complex_id={complex_id}&sales_type=1', timeout=10)
if r_items.status_code == 200:
    print(json.dumps(r_items.json(), ensure_ascii=False, indent=2)[:1000])
else:
    print(f"[{r_items.status_code}] {r_items.text[:200]}")
