import requests, json

cookies = {
    "NAC": "nqjwBswNzc0p",
    "NNB": "Z4GOMF7VBFYWQ",
    "NACT": "1",
    "NID_AUT": "BK+YIg1PG6vWW0DN/3LydbRDSflepvzGXzxccp5ZDCHjW+97PouLVSLiyoX8Y/je",
    "NID_SES": "AAABoTpeavXbO4Ni9y+H/hG1psDd90e01vKXsQ8W029jBEf88vIT6oG2mATSL21VGIcWZ/C8iOKn7Rp8ZltliWmEadptcIILm2qsaJ4t6KISPiT17j+X6HbNJK5u4sEaZm2sCC8Ze0FkWoYNgSTHJmrdQ6fqq8k275fNvSTFKYBiPfNS4zgaLBA01IvatVb+STg7qKaxK6ydRv7yBE8Qc9U3Q6GP/zMCAOuaoXgWoWJSYUAwo4KaO4d5JHoFcwv7bLzDBFERsyGdBC4+QN/Gnf9WVfsJ2ArOc+vfuN2mKYPCJ6FcqLiTSDydDHbDyRnT1eO88yUqR9oStdtLxQJgXN7Mc7suyu1vNNoyDCj6JoMrN47KG+255MvjeYFsUTYxbgEtjK2DH8ba1YdwHGRj2ZnqGiz4vxytPb+CogOgHmeUXPFn3KE7S6MH95LN5bT0yr3mz7xSPTHpsMiqj+yeHZWbMS1SnB08pXUsmP+N1gbXUgnF1QHxkh3DP222PpGGC3zuRmhDZ6XlI9Fab+LUjrVaNeUwPcggRpzEyY1ODOfC85PIEI1wZb3IWbpcy2lPX6v/og==",
    "JSESSIONID": "067C4169427F7AFAEA176275DD00E57A",
    "BUC": "Mdilk94CWRPRuXXNJAIZ_jAPLL2v5in9GIOCLabm_C4=",
    "landHomeFlashUseYn": "Y",
    "nhn.realestate.article.rlet_type_cd": "A01",
    "wcs_bt": "60717a12f2b3c8:1781314166",
}
headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "referer": "https://land.naver.com/",
    "x-requested-with": "XMLHttpRequest",
}

# land.naver.com API 패턴 테스트
tests = [
    ("/complex/tours.naver", "GET"),
    ("/api/regions/list?cortarNo=0000000000", "GET"),
    ("/complex/tours.naver?cortarNo=0000000000", "GET"),
]

for path, method in tests:
    url = f"https://land.naver.com{path}"
    try:
        r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        print(f"[{r.status_code}] {path}")
        if r.status_code == 200:
            print(f"  body: {r.text[:300]}")
        elif r.status_code == 404:
            print(f"  (not found)")
        else:
            print(f"  {r.text[:200]}")
    except Exception as e:
        print(f"[ERR] {path}: {e}")
