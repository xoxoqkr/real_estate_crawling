"""
fin.land.naver.com 리다이렉트 체인 분석
"""
import requests, json, re

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
})

# Track redirects
r = session.get('https://fin.land.naver.com/complexes/8928', allow_redirects=True, timeout=10)
print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")
print(f"History:")
for i, resp in enumerate(r.history):
    print(f"  {i}: [{resp.status_code}] {resp.url}")
    for k, v in resp.headers.items():
        if k.lower() in ('location', 'refresh'):
            print(f"     {k}: {v}")

# Check the final page content
if r.status_code == 200:
    text = r.text
    title = re.search(r'<title>(.*?)</title>', text)
    if title:
        print(f"Title: {title.group(1)}")
    
    # Look for any embedded data
    scripts = re.findall(r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>', text)
    print(f"Next.js data: {len(scripts)}")
    for s in scripts:
        try:
            d = json.loads(s)
            print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
        except:
            print(f"  (parse error) {s[:200]}")
    
    # Look for any state/initial data
    for pattern in [r'window\.__INITIAL_STATE__\s*=\s*({.*?});', r'window\.__DATA__\s*=\s*({.*?});']:
        matches = re.findall(pattern, text)
        if matches:
            print(f"Found state: {matches[0][:500]}")

# Also try searching on fin.land.naver.com
print("\n=== Try fin.land.naver.com search ===")
r2 = session.get('https://fin.land.naver.com/search?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90', allow_redirects=True, timeout=10)
print(f"[{r2.status_code}] {r2.url}")
