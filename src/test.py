import requests

cookies = {
    'NNB': 'RUYBKWD5FJTWA',
    'ASID': '70d6b7520000017949eeb1890000006c',
    'NV_WETR_LOCATION_RGN_M': '"MDIxMzMxMDk="',
    '_fwb': '143iknsGPmFqPcOWqfHPZgC.1703902005482',
    '_fwb': '143iknsGPmFqPcOWqfHPZgC.1703902005482',
    '_ga': 'GA1.1.1536067081.1703902098',
    'NV_WETR_LAST_ACCESS_RGN_M': '"MDIxMzMxMDk="',
    '_ga_451MFZ9CFM': 'GS1.1.1711238576.2.1.1711238607.0.0.0',
    'landHomeFlashUseYn': 'Y',
    'wcs_bt': '4f99b5681ce60:1730628175',
    'ba.uuid': 'b6c27d1a-8abc-4194-a91a-f2427d90b6fc',
    'NAC': '1R7rBQwUT62t',
    'nhn.realestate.article.rlet_type_cd': 'A01',
    'nhn.realestate.article.trade_type_cd': '""',
    'NACT': '1',
    'realestate.beta.lastclick.cortar': '1100000000',
    'REALESTATE': 'Mon%20Jan%2027%202025%2017%3A54%3A47%20GMT%2B0900%20(Korean%20Standard%20Time)',
    'BUC': 'GQf-mDWs3gF_bSGcgx1l_kpcVhGtIS0W6ireKyRtseY=',
}

headers = {
    'accept': '*/*',
    'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3Mzc5NjgwODcsImV4cCI6MTczNzk3ODg4N30.bcJSC9gteHYMF1S5AmAEOMa_lVORV9OVAKbO_truiJs',
    # 'cookie': 'NNB=RUYBKWD5FJTWA; ASID=70d6b7520000017949eeb1890000006c; NV_WETR_LOCATION_RGN_M="MDIxMzMxMDk="; _fwb=143iknsGPmFqPcOWqfHPZgC.1703902005482; _fwb=143iknsGPmFqPcOWqfHPZgC.1703902005482; _ga=GA1.1.1536067081.1703902098; NV_WETR_LAST_ACCESS_RGN_M="MDIxMzMxMDk="; _ga_451MFZ9CFM=GS1.1.1711238576.2.1.1711238607.0.0.0; landHomeFlashUseYn=Y; wcs_bt=4f99b5681ce60:1730628175; ba.uuid=b6c27d1a-8abc-4194-a91a-f2427d90b6fc; NAC=1R7rBQwUT62t; nhn.realestate.article.rlet_type_cd=A01; nhn.realestate.article.trade_type_cd=""; NACT=1; realestate.beta.lastclick.cortar=1100000000; REALESTATE=Mon%20Jan%2027%202025%2017%3A54%3A47%20GMT%2B0900%20(Korean%20Standard%20Time); BUC=GQf-mDWs3gF_bSGcgx1l_kpcVhGtIS0W6ireKyRtseY=',
    'priority': 'u=1, i',
    'referer': 'https://new.land.naver.com/complexes/111396?ms=37.5760948,127.0516631,17&a=APT:PRE:ABYG:JGC&e=RETAIL',
    'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
}

params = {
    'sameAddressGroup': 'false',
}
apt_num = 119219
response = requests.get(f'https://new.land.naver.com/api/complexes/{apt_num}', params=params, cookies=cookies, headers=headers)

print(response.text)
