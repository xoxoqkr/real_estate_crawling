import requests, json, time

cookies = {
    "NID_AUT": "BK+YIg1PG6vWW0DN/3LydbRDSflepvzGXzxccp5ZDCHjW+97PouLVSLiyoX8Y/je",
    "NID_SES": "AAABoTpeavXbO4Ni9y+H/hG1psDd90e01vKXsQ8W029jBEf88vIT6oG2mATSL21VGIcWZ/C8iOKn7Rp8ZltliWmEadptcIILm2qsaJ4t6KISPiT17j+X6HbNJK5u4sEaZm2sCC8Ze0FkWoYNgSTHJmrdQ6fqq8k275fNvSTFKYBiPfNS4zgaLBA01IvatVb+STg7qKaxK6ydRv7yBE8Qc9U3Q6GP/zMCAOuaoXgWoWJSYUAwo4KaO4d5JHoFcwv7bLzDBFERsyGdBC4+QN/Gnf9WVfsJ2ArOc+vfuN2mKYPCJ6FcqLiTSDydDHbDyRnT1eO88yUqR9oStdtLxQJgXN7Mc7suyu1vNNoyDCj6JoMrN47KG+255MvjeYFsUTYxbgEtjK2DH8ba1YdwHGRj2ZnqGiz4vxytPb+CogOgHmeUXPFn3KE7S6MH95LN5bT0yr3mz7xSPTHpsMiqj+yeHZWbMS1SnB08pXUsmP+N1gbXUgnF1QHxkh3DP222PpGGC3zuRmhDZ6XlI9Fab+LUjrVaNeUwPcggRpzEyY1ODOfC85PIEI1wZb3IWbpcy2lPX6v/og==",
    "NNB": "Z4GOMF7VBFYWQ",
    "BUC": "Mdilk94CWRPRuXXNJAIZ_jAPLL2v5in9GIOCLabm_C4=",
    "JSESSIONID": "067C4169427F7AFAEA176275DD00E57A",
}
headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "referer": "https://land.naver.com/",
    "x-requested-with": "XMLHttpRequest",
}

# 여러 도메인/패턴 테스트
tests = [
    # fin subdomain (from tours.naver response)
    ("https://fin.land.naver.com/complexes/8928", "fin/complexes/8928"),
    ("https://fin.land.naver.com/api/complexes/8928", "fin/api/complexes/8928"),
    ("https://fin.land.naver.com/regions/list?cortarNo=0000000000", "fin/regions/list"),
    ("https://fin.land.naver.com/complexes?cortarNo=1100000000", "fin/complexes?cortarNo"),
    # api subdomain
    ("https://api.land.naver.com/complexes/8928", "api/complexes/8928"),
    # m subdomain
    ("https://m.land.naver.com/api/regions/list?cortarNo=0000000000", "m/api/regions/list"),
    # new.land with new cookies
    ("https://new.land.naver.com/api/regions/list?cortarNo=0000000000", "new/api/regions/list"),
    ("https://new.land.naver.com/api/complexes/8928?sameAddressGroup=false", "new/complexes/8928"),
    # land.naver.com new patterns
    ("https://land.naver.com/region/list.naver?cortarNo=0000000000", "land/region/list.naver"),
    ("https://land.naver.com/complex/info.naver?complexNo=8928", "land/complex/info.naver"),
]

for url, name in tests:
    time.sleep(0.5)
    try:
        r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        s = r.status_code
        if s == 200:
            try:
                j = r.json()
                print(f"[200] {name}")
                keys_str = str(list(j.keys()))[:100]
                data_preview = str(j)[:200]
                print(f"      keys={keys_str}")
                print(f"      data={data_preview}")
            except:
                print(f"[200] {name} -> (not json) {r.text[:100]}")
        else:
            print(f"[{s}] {name} -> {r.text[:100]}")
    except Exception as e:
        print(f"[ERR] {name}: {e}")
