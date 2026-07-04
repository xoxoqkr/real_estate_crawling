import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

r = requests.get('https://m.land.naver.com', headers=headers, timeout=10, allow_redirects=True)
print('Status:', r.status_code)
print('Final URL:', r.url)
print('Content length:', len(r.text))

apis = re.findall(r'https?://[^"\'\s]+(?:api|complex|region|article)[^"\'\s]+', r.text)
print('\nAPI endpoints found:', len(apis))
for a in sorted(set(apis))[:20]:
    print(' ', a)

scripts = re.findall(r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>', r.text)
print('\nNext.js data scripts:', len(scripts))
if scripts:
    data = json.loads(scripts[0])
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])

states = re.findall(r'window\.__[A-Z_]+\s*=\s*({.*?});', r.text)
print('\nWindow state vars:', len(states))
for s in states[:3]:
    try:
        d = json.loads(s)
        print(json.dumps(d, ensure_ascii=False, indent=2)[:500])
    except:
        print(' (json parse failed)', s[:200])
