"""
search.min.js에서 API 엔드포인트 추출
"""
import requests, re, json

headers = {'User-Agent': 'Mozilla/5.0'}

# Download the search JS bundle
url = "https://ssl.pstatic.net/static.land/static/space/js/deploy/20260516042747/min/search.min.js"
r = requests.get(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}, Size: {len(r.text)} bytes")

js = r.text

# Find all API-like URLs
api_pattern = re.compile(r'https?://[^"\'\\\s,)]+(?:api|complex|region|article|search|list|cortar|complexes)[^"\'\\\s,)]*')
apis = api_pattern.findall(js)

print(f"\nAPI URLs found in JS: {len(apis)}")
for a in sorted(set(apis)):
    print(f"  {a[:300]}")

# Also find URL patterns with template strings
template_pattern = re.compile(r'["\'](https?://[^"\']*\\+[^"\']*|[^"\']*(?:api|complex|region)[^"\']*)["\']')
templates = template_pattern.findall(js)
print(f"\nURL templates: {len(templates)}")
for t in sorted(set(templates))[:30]:
    print(f"  {t[:300]}")

# Find paths with /api/ or similar
path_pattern = re.compile(r'["\'](/[^"\']*(?:api|complex|region|article|search|list|cortar)[^"\']*)["\']')
paths = path_pattern.findall(js)
print(f"\nPaths: {len(paths)}")
for p in sorted(set(paths))[:30]:
    print(f"  {p[:300]}")

# Look for common patterns like fetch, axios, ajax, etc.
for keyword in ['fetch(', 'axios.', 'ajax', 'XMLHttpRequest', 'xhr', 'getJSON']:
    count = js.count(keyword)
    if count > 0:
        print(f"  {keyword}: {count} occurrences")
