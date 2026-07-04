import requests, json, sys

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

# 1. news API - verify cookies work
r = requests.get(
    "https://new.land.naver.com/news/airsList.naver?baseDate=2026-06-13&page=1&size=5",
    headers=headers, cookies=cookies, timeout=10
)
result = "OK" if r.status_code == 200 else "FAIL"
print(f"1. news API: {r.status_code} [{result}]")

# 2. region API
r = requests.get(
    "https://new.land.naver.com/api/regions/list?cortarNo=0000000000&sameAddressGroup=false",
    headers=headers, cookies=cookies, timeout=10
)
print(f"2. region API: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    if "regionList" in d:
        names = [x["regionName"] for x in d["regionList"]]
        print(f"   SUCCESS! {len(names)} regions: {names[:5]}")
    else:
        print(f"   response: {str(d)[:200]}")
else:
    print(f"   FAIL: {r.text[:200]}")

# 3. complex API test
r = requests.get(
    "https://new.land.naver.com/api/complexes/8928?sameAddressGroup=false",
    headers=headers, cookies=cookies, timeout=10
)
print(f"3. complex API: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    cd = d.get("complexDetail", {})
    print(f"   name: {cd.get('complexName')}")
    print(f"   addr: {cd.get('address')}")
    print(f"   lat/lng: {cd.get('latitude')}/{cd.get('longitude')}")
else:
    print(f"   FAIL: {r.text[:200]}")
