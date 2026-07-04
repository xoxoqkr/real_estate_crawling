import requests, json, re

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
}

tests = [
    'https://land.naver.com/complex/8928',
    'https://land.naver.com/complexes/8928', 
    'https://land.naver.com/apt/8928',
    'https://fin.land.naver.com/complexes/8928',
    'https://land.naver.com/',
]

for url in tests:
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f'[{r.status_code}] {url}')
        print(f'  Final URL: {r.url}')
        print(f'  Content-Type: {r.headers.get("content-type", "")}')
        if r.status_code == 200:
            text = r.text
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', text)
            if title_match:
                print(f'  Title: {title_match.group(1)}')
            print(f'  Length: {len(text)} bytes')
            # Look for JSON data in script tags
            matches = re.findall(r'<script[^>]+>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>', text)
            if matches:
                print(f'  Found __INITIAL_STATE__ data')
        else:
            print(f'  Body: {r.text[:200]}')
        print()
    except Exception as e:
        print(f'[ERR] {url}: {e}')
        print()
