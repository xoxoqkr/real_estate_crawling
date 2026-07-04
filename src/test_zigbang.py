"""
직방(Zigbang) API 테스트 - 현재 매물 정보 조회
"""
import requests, json

session = requests.Session()

# 1. 지역코드로 단지 검색 (직방 API)
print("=== 직방 API 테스트 ===")

# 직방은 geohash 기반이지만, 단지명 검색도 가능
# Try: search by complex name
r = session.get(
    'https://apis.zigbang.com/search?q=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90&serviceType=zigbang&page=1&size=10',
    headers={'User-Agent': 'Mozilla/5.0'},
    timeout=10
)
print(f"[{r.status_code}] Search by name")
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
else:
    print(f"  {r.text[:300]}")

print()

# Try zigbang API v2
r2 = session.get(
    'https://api.zigbang.com/v1/search?q=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90',
    headers={'User-Agent': 'Mozilla/5.0'},
    timeout=10
)
print(f"[{r2.status_code}] API v1 search")
if r2.status_code == 200:
    data = r2.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
else:
    print(f"  {r2.text[:300]}")

print()

# Try Dabang API
r3 = session.get(
    'https://www.dabangapp.com/api/search?keyword=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90',
    headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.dabangapp.com/'},
    timeout=10
)
print(f"[{r3.status_code}] Dabang search")
if r3.status_code == 200:
    data = r3.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
else:
    print(f"  {r3.text[:300]}")
