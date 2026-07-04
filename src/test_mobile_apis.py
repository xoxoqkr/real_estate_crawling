"""
m.land.naver.com API 엔드포인트 테스트
"""
import requests, json, time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Referer': 'https://m.land.naver.com/search',
})

# Test all discovered API endpoints
tests = [
    ('GET', '/api/autocomplete/mobile?keyword=한남더힐', None),
    ('GET', '/search/recommendKeyword', None),
    ('GET', '/search/recommendTag', None),
]

base = 'https://m.land.naver.com'

for method, path, data in tests:
    url = base + path
    try:
        if method == 'GET':
            r = session.get(url, timeout=10)
        else:
            r = session.post(url, data=data, timeout=10)
        
        print(f'[{r.status_code}] {method} {path}')
        ct = r.headers.get('content-type', '')
        print(f'  Content-Type: {ct}')
        print(f'  Size: {len(r.text)} bytes')
        
        if r.status_code == 200:
            try:
                d = r.json()
                if isinstance(d, dict):
                    print(f'  Keys: {list(d.keys())[:10]}')
                    print(f'  Preview: {json.dumps(d, ensure_ascii=False)[:500]}')
                elif isinstance(d, list):
                    print(f'  List length: {len(d)}')
                    if d:
                        print(f'  First item: {json.dumps(d[0], ensure_ascii=False)[:300]}')
            except:
                print(f'  Text: {r.text[:300]}')
        else:
            print(f'  Body: {r.text[:200]}')
    except Exception as e:
        print(f'[ERR] {method} {path}: {e}')
    print()
    time.sleep(0.5)
