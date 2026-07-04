"""
fin.land.naver.com/map 페이지에서 API 엔드포인트 추출
"""
import requests, re, json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
})

# Get the map page
r = session.get('https://fin.land.naver.com/map?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90', timeout=10)
text = r.text
print(f"Status: {r.status_code}, Size: {len(text)} bytes")

# Find all JS bundles
scripts = re.findall(r'<script[^>]*src="([^"]+)"', text)
print(f"\nScripts found: {len(scripts)}")
js_urls = []
for s in scripts:
    if 'static' in s or 'js' in s or 'chunk' in s or 'bundle' in s:
        if 'naver' in s or 'land' in s or 'fin' in s:
            js_urls.append(s if s.startswith('http') else 'https://fin.land.naver.com' + s)
            print(f"  {s}")

# Download and analyze JS bundles for API endpoints
print(f"\nAnalyzing JS bundles for API endpoints...")
for js_url in js_urls[:5]:
    try:
        r_js = session.get(js_url, timeout=10)
        js = r_js.text
        # Find API URLs
        apis = re.findall(r'["\'](https?://(?!.*\.(?:png|jpg|jpeg|gif|svg|css|woff))[^"\']*(?:api|complex|region|article|search|list|cortar|complexes|property)[^"\']*)["\']', js)
        
        # Also find relative paths that look like APIs
        paths = re.findall(r'["\'](/[^"\']*(?:api|complex|region|article|search|list|cortar|complexes|property)[^"\']*)["\']', js)
        
        all_endpoints = apis + [('https://fin.land.naver.com' + p) if p.startswith('/') else p for p in paths]
        
        if all_endpoints:
            print(f"\n  {js_url.split('/')[-1][:50]}: {len(all_endpoints)} endpoints")
            for ep in sorted(set(all_endpoints))[:10]:
                print(f"    {ep[:200]}")
    except Exception as e:
        print(f"  ERR {js_url}: {e}")
