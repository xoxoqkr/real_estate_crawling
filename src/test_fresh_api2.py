import requests, json

cookies = {
    "NAC": "nqjwBswNzc0p",
    "NNB": "Z4GOMF7VBFYWQ",
    "NACT": "1",
    "NID_AUT": "BK+YIg1PG6vWW0DN/3LydbRDSflepvzGXzxccp5ZDCHjW+97PouLVSLiyoX8Y/je",
    "NID_SES": "AAABoTpeavXbO4Ni9y+H/hG1psDd90e01vKXsQ8W029jBEf88vIT6oG2mATSL21VGIcWZ/C8iOKn7Rp8ZltliWmEadptcIILm2qsaJ4t6KISPiT17j+X6HbNJK5u4sEaZm2sCC8Ze0FkWoYNgSTHJmrdQ6fqq8k275fNvSTFKYBiPfNS4zgaLBA01IvatVb+STg7qKaxK6ydRv7yBE8Qc9U3Q6GP/zMCAOuaoXgWoWJSYUAwo4KaO4d5JHoFcwv7bLzDBFERsyGdBC4+QN/Gnf9WVfsJ2ArOc+vfuN2mKYPCJ6FcqLiTSDydDHbDyRnT1eO88yUqR9oStdtLxQJgXN7Mc7suyu1vNNoyDCj6JoMrN47KG+255MvjeYFsUTYxbgEtjK2DH8ba1YdwHGRj2ZnqGiz4vxytPb+CogOgHmeUXPFn3KE7S6MH95LN5bT0yr3mz7xSPTHpsMiqj+yeHZWbMS1SnB08pXUsmP+N1gbXUgnF1QHxkh3DP222PpGGC3zuRmhDZ6XlI9Fab+LUjrVaNeUwPcggRpzEyY1ODOfC85PIEI1wZb3IWbpcy2lPX6v/og==",
    "BUC": "Mdilk94CWRPRuXXNJAIZ_jAPLL2v5in9GIOCLabm_C4=",
    "JSESSIONID": "067C4169427F7AFAEA176275DD00E57A",
    "landHomeFlashUseYn": "Y",
    "nhn.realestate.article.rlet_type_cd": "A01",
    "wcs_bt": "60717a12f2b3c8:1781314166",
}
headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "referer": "https://land.naver.com/",
    "x-requested-with": "XMLHttpRequest",
    "dnt": "1",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# 1. 사용자가 DevTools에서 보여준 것과 동일한 요청
print("1. news/airsList.naver (사용자 요청과 동일)")
r = requests.get(
    "https://new.land.naver.com/news/airsList.naver?baseDate=2026-06-13&page=1&size=5",
    headers=headers, cookies=cookies, timeout=10
)
print(f"   {r.status_code}")
if r.status_code == 200:
    print(f"   ✅ {r.text[:200]}")
else:
    print(f"   ❌ {r.text[:200]}")

# 2. region API with param
print("\n2. regions/list (sameAddressGroup 파라미터 추가)")
r = requests.get(
    "https://new.land.naver.com/api/regions/list?cortarNo=0000000000&sameAddressGroup=false",
    headers=headers, cookies=cookies, timeout=10
)
print(f"   {r.status_code}")
if r.status_code == 200:
    d = r.json()
    if "regionList" in d:
        print(f"   ✅ 성공! {len(d['regionList'])}개 시도")
        for x in d["regionList"][:5]:
            print(f"      {x['regionName']}")
    else:
        print(f"   응답: {json.dumps(d, ensure_ascii=False)[:200]}")
else:
    print(f"   ❌ {r.text[:200]}")
