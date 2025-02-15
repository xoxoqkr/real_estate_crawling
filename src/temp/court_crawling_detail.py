#!/usr/bin/env python
# coding: utf-8

# In[9]:


import requests

cookies = {
    'WMONID': 'QGpWYOCGstc',
    'realJiwonNm': '%B0%ED%BE%E7%C1%F6%BF%F8',
    'daepyoSidoCd': '',
    'daepyoSiguCd': '',
    'rd1Cd': '',
    'rd2Cd': '',
    'realVowel': '35207_45207',
    'lastAccess': '1738375648769',
    'globalDebug': 'false',
    'menuLst': '%5B%5D',
    'LGDN_TM': '1738384646063',
    'SID': '',
    'cortAuctnLgnMbr': '',
    'wcCookieV2': '116.44.45.108_T_204884_WC',
    'JSESSIONID': 'VqjA7hfNJ7N5-dHaJkMIEKeHMwA2947BaTeXCHIM-11QgjxqVLO6!-1054482192',
}

headers = {
    'Accept': 'application/json',
    'Accept-Language': 'ko,en;q=0.9,en-US;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    # 'Cookie': 'WMONID=QGpWYOCGstc; realJiwonNm=%B0%ED%BE%E7%C1%F6%BF%F8; daepyoSidoCd=; daepyoSiguCd=; rd1Cd=; rd2Cd=; realVowel=35207_45207; lastAccess=1738375648769; globalDebug=false; menuLst=%5B%5D; LGDN_TM=1738384646063; SID=; cortAuctnLgnMbr=; wcCookieV2=116.44.45.108_T_204884_WC; JSESSIONID=VqjA7hfNJ7N5-dHaJkMIEKeHMwA2947BaTeXCHIM-11QgjxqVLO6!-1054482192',
    'Origin': 'https://www.courtauction.go.kr',
    'Referer': 'https://www.courtauction.go.kr/pgj/index.on?w2xPath=/pgj/ui/pgj100/PGJ151F00.xml',
    'SC-Pgmid': 'PGJ15BM01',
    'SC-Userid': 'NONUSER',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
    'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'submissionid': 'mf_wfm_mainFrame_sbm_selectGdsDtlSrchDtlInfo',
}

json_data = {
    'dma_srchGdsDtlSrch': {
        'csNo': '2021타경108187', #'2021타경108187' '2022타경3944'
        'cortOfcCd': 'B000210',
        'dspslGdsSeq': '1',
        'pgmId': 'PGJ151F01',
        'srchInfo': {
            'rletDspslSpcCondCd': '',
            'bidDvsCd': '000331',
            'mvprpRletDvsCd': '00031R',
            'cortAuctnSrchCondCd': '0004601',
            'rprsAdongSdCd': '',
            'rprsAdongSggCd': '',
            'rprsAdongEmdCd': '',
            'rdnmSdCd': '',
            'rdnmSggCd': '',
            'rdnmNo': '',
            'mvprpDspslPlcAdongSdCd': '',
            'mvprpDspslPlcAdongSggCd': '',
            'mvprpDspslPlcAdongEmdCd': '',
            'rdDspslPlcAdongSdCd': '',
            'rdDspslPlcAdongSggCd': '',
            'rdDspslPlcAdongEmdCd': '',
            'cortOfcCd': 'B000210',
            'jdbnCd': '',
            'execrOfcDvsCd': '',
            'lclDspslGdsLstUsgCd': '',
            'mclDspslGdsLstUsgCd': '',
            'sclDspslGdsLstUsgCd': '',
            'cortAuctnMbrsId': '',
            'aeeEvlAmtMin': '',
            'aeeEvlAmtMax': '',
            'lwsDspslPrcRateMin': '',
            'lwsDspslPrcRateMax': '',
            'flbdNcntMin': '',
            'flbdNcntMax': '',
            'objctArDtsMin': '',
            'objctArDtsMax': '',
            'mvprpArtclKndCd': '',
            'mvprpArtclNm': '',
            'mvprpAtchmPlcTypCd': '',
            'notifyLoc': 'off',
            'lafjOrderBy': '',
            'pgmId': 'PGJ151F01',
            'csNo': '',
            'cortStDvs': '1',
            'statNum': 1,
            'bidBgngYmd': '20250201',
            'bidEndYmd': '20250215',
            'dspslDxdyYmd': '',
            'fstDspslHm': '',
            'scndDspslHm': '',
            'thrdDspslHm': '',
            'fothDspslHm': '',
            'dspslPlcNm': '',
            'lwsDspslPrcMin': '',
            'lwsDspslPrcMax': '',
            'grbxTypCd': '',
            'gdsVendNm': '',
            'fuelKndCd': '',
            'carMdyrMax': '',
            'carMdyrMin': '',
            'carMdlNm': '',
            'sideDvsCd': '2',
            'menuNm': '물건상세검색',
        },
    },
}

response = requests.post(
    'https://www.courtauction.go.kr/pgj/pgj15B/selectAuctnCsSrchRslt.on',
    cookies=cookies,
    headers=headers,
    json=json_data,
)

# 응답 크기가 큰 경우 일부만 출력
print("Final URL:", response.url)
print("Status Code:", response.status_code)

try:
    response_json = response.json()
    print("Response JSON (First 500 chars):", str(response_json)[:5000])  # 일부만 출력
except ValueError:
    print("Response Text (First 500 chars):", response.text[:5000])  # 일부만 출력


# In[38]:


#print("Response JSON (First 500 chars):", str(response_json)[:5000])  # 일부만 출력
#print(type(response_json['data']['dma_result']))
print(response_json['data']['dma_result'].keys())
temp = response_json['data']['dma_result']['dstrtDemnInfo']
#print(temp)
try:
    for info in temp:
        print('{} ; {}'.format(info, temp[info]))
except:
    print(type(temp[0]))
    print(temp[0])
#    #print(info)
#    print('done')


# In[73]:


#csBaseInfo 기본정보
temp = response_json['data']['dma_result']['csBaseInfo']
print(temp)
print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[69]:


#dstrtDemnInfo ??
temp = response_json['data']['dma_result']['dstrtDemnInfo']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[39]:


#'dspslGdsDxdyInfo' 경매 정보?
#print(response_json['data']['dma_result'].keys())
temp = response_json['data']['dma_result']['dspslGdsDxdyInfo']
#print(temp)
try:
    for info in temp:
        print('{} ; {}'.format(info, temp[info]))
except:
    print(type(temp[0]))
    print(temp[0])


# In[55]:


#picDvsIndvdCnt 이미지 정보
temp = response_json['data']['dma_result']['picDvsIndvdCnt']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            for key in info.keys():
                print(info[key])
        #print(type(info))
except:
    print("Fail")


# In[59]:


#'csPicLst' 이미지 상세
temp = response_json['data']['dma_result']['csPicLst']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
        #print(type(info))
except:
    print("Fail")


# In[61]:


#gdsDspslDxdyLst 기일내역
temp = response_json['data']['dma_result']['gdsDspslDxdyLst']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[62]:


#gdsDspslObjctLst 전유물부분 건물의 표시
temp = response_json['data']['dma_result']['gdsDspslObjctLst']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[63]:


#rgltLandLstAll 목룍내역 중 대지권
temp = response_json['data']['dma_result']['rgltLandLstAll']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[64]:


#bldSdtrDtlLstAll 목록내역 중 건물 표시
temp = response_json['data']['dma_result']['bldSdtrDtlLstAll']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[65]:


#gdsNotSugtBldLsstAll
temp = response_json['data']['dma_result']['gdsNotSugtBldLsstAll']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[66]:


#gdsRletStLtnoLstAll
temp = response_json['data']['dma_result']['gdsRletStLtnoLstAll']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[67]:


#aeeWevlMnpntLst 감정평가요항표 요약
temp = response_json['data']['dma_result']['aeeWevlMnpntLst']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[68]:


#aroundDspslStats 인근매각물건사례 중 인근매각통계
temp = response_json['data']['dma_result']['aroundDspslStats']
#print(temp)
#print(type(temp))
try:
    for info in temp:
        if type(info) == list:
            print("List")
            print(info)
        elif type(info) == dict:
            print("dict content")
            print(info.keys())
            print('key ; 내용')
            for key in info.keys():
                print('{}; {}'.format(key, info[key]))
except:
    print("Fail")


# In[ ]:




