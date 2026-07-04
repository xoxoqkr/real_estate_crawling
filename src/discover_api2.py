"""
새로운 land.naver.com API 엔드포인트 탐색
"""
import requests, json, time

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
}

# 시도해볼 API 패턴들
patterns = [
    # region
    "/region/list.naver",
    "/region/list.naver?cortarNo=0000000000",
    "/regions/list.naver",
    "/regions/list.naver?cortarNo=0000000000",
    # complex
    "/complex/list.naver",
    "/complex/list.naver?cortarNo=1100000000&realEstateType=APT",
    "/complexes/list.naver",
    "/complex/detail.naver?complexNo=8928",
    "/complex/detail.naver?complexNumber=8928",
    "/complex/8928.naver",
    # article
    "/article/list.naver",
    "/article/list.naver?complexNo=8928",
    "/articles/list.naver",
    "/complex/article.naver",
    "/complex/articleList.naver",
    # search
    "/search/complex.naver",
    "/search/complex.naver?keyword=test",
    # new pattern
    "/complex/complexes.naver",
    "/complex/complexes.naver?cortarNo=1100000000",
    # fin domain
    "/complex/complexes",
    "/complex/articles",
]

base = "https://land.naver.com"

for path in patterns:
    url = f"{base}{path}"
    time.sleep(0.3)
    try:
        r = requests.get(url, headers=headers, cookies=cookies, timeout=5)
        status = r.status_code
        if status == 200:
            try:
                j = r.json()
                if j.get("code") == "success" and j.get("data"):
                    print(f"[200 ✅ DATA] {path}")
                    print(f"   keys: {list(j['data'][0].keys()) if isinstance(j['data'], list) else list(j['data'].keys())[:5]}")
                    print(f"   sample: {str(j['data'][:1])[:150]}")
                else:
                    print(f"[200] {path} -> {str(j)[:150]}")
            except:
                print(f"[200] {path} -> {r.text[:100]}")
        elif status == 404:
            pass  # skip 404s silently
        else:
            print(f"[{status}] {path} -> {r.text[:100]}")
    except Exception as e:
        pass
