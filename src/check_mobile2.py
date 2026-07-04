import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
}

# Try various mobile search/complex URLs
urls = [
    'https://m.land.naver.com/search?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90',
    'https://m.land.naver.com/search/result?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90',
    'https://m.land.naver.com/search/complex?query=%ED%95%9C%EB%82%A8%EB%8D%94%ED%9E%90',
    'https://m.land.naver.com/complex/8928',
    'https://m.land.naver.com/complexes/8928',
    'https://m.land.naver.com/api/complexes/8928',
    'https://m.land.naver.com/api/regions/list?cortarNo=0000000000',
    'https://m.land.naver.com/api/articles/complex/8928',
    'https://m.land.naver.com/article/info?articleNo=2508514668',
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        clen = len(r.text)
        content_type = r.headers.get('content-type', '')
        print(f'[{r.status_code}] {url}')
        print(f'  Type: {content_type[:50]} | Size: {clen}B')
        if r.status_code == 200 and 'json' in content_type:
            try:
                d = r.json()
                print(f'  JSON keys: {list(d.keys())[:10]}')
                print(f'  Preview: {json.dumps(d, ensure_ascii=False)[:300]}')
            except:
                print(f'  Text: {r.text[:200]}')
        elif r.status_code == 200:
            title = re.search(r'<title>(.*?)</title>', r.text)
            if title:
                print(f'  Title: {title.group(1)}')
            apis = re.findall(r'https?://[^"\'\s]+(?:api|complex|region|article|search)[^"\'\s]+', r.text)
            if apis:
                for a in sorted(set(apis))[:5]:
                    print(f'  API in page: {a}')
        print()
    except Exception as e:
        print(f'[ERR] {url}: {e}')
        print()
