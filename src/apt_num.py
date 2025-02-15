import requests
import json
import pandas as pd
import copy


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






down_url = 'https://new.land.naver.com/api/complexes/8928'
down_url = 'https://new.land.naver.com/api/articles/complex/113059?realEstateType=APT%3APRE%3AABYG%3AJGC&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page=1&complexNo=113059&buildingNos=&areaNos=&type=list&order=rank'
r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
    "Accept-Encoding": "gzip",
    "Host": "new.land.naver.com",
    "Referer": "https://new.land.naver.com/complexes/8928?ms=37.482968,127.0634,16&a=APT&b=A1&e=RETAIL",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
})
r.encoding = "utf-8-sig"
temp =json.loads(r.text)
print(temp)
temp_data=json.loads(r.text)







def get_sido_info():
    down_url = 'https://new.land.naver.com/api/regions/list?cortarNo=0000000000'
    r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/102378?ms=37.5018495,127.0438028,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp=json.loads(r.text)
    temp=list(pd.DataFrame(temp["regionList"])["cortarNo"])
    return temp
def get_gungu_info(sido_code):
    down_url = 'https://new.land.naver.com/api/regions/list?cortarNo='+sido_code
    r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/102378?ms=37.5018495,127.0438028,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp=json.loads(r.text)
    temp=list(pd.DataFrame(temp['regionList'])["cortarNo"])
    return temp
def get_dong_info(gungu_code):
    down_url = 'https://new.land.naver.com/api/regions/list?cortarNo='+gungu_code
    r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/102378?ms=37.5018495,127.0438028,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp=json.loads(r.text)
    temp=list(pd.DataFrame(temp['regionList'])["cortarNo"])
    return temp
def get_apt_list(dong_code):
    down_url = 'https://new.land.naver.com/api/regions/complexes?cortarNo='+dong_code+'&realEstateType=APT&order='
    r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/102378?ms=37.5018495,127.0438028,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp=json.loads(r.text)
    try:
        temp=list(pd.DataFrame(temp['complexList'])["complexNo"])
    except:
        temp=[]
    return temp

def get_school_info(apt_code):
    down_url = 'https://new.land.naver.com/api/complexes/'+apt_code+'/schools'
    r = requests.get(down_url,headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/"+apt_code+"?ms=37.482968,127.0634,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp_school=json.loads(r.text)
    return temp_school

def get_school_info2(apt_code):
    response = requests.get(f'https://new.land.naver.com/api/complexes/{apt_code}/schools', params=params, cookies=cookies, headers=headers)
    return json.loads(response.text)


##################가격정보
def apt_price(apt_code,index):
    p_num=temp["complexPyeongDetailList"][index]["pyeongNo"]
    down_url = 'https://new.land.naver.com/api/complexes/'+apt_code+'/prices?complexNo='+apt_code+'&tradeType=A1&year=5&priceChartChange=true&areaNo='+p_num+'&areaChange=true&type=table'

    r = requests.get(down_url,headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/"+apt_code+"?ms=37.4830877,127.0579863,15&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp_price=json.loads(r.text)
    return temp_price

def get_apt_info(apt_code):
    down_url = 'https://new.land.naver.com/api/complexes/'+apt_code+'?sameAddressGroup=false'
    r = requests.get(down_url,data={"sameAddressGroup":"false"},headers={
        "Accept-Encoding": "gzip",
        "Host": "new.land.naver.com",
        "Referer": "https://new.land.naver.com/complexes/"+apt_code+"?ms=37.482968,127.0634,16&a=APT&b=A1&e=RETAIL",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    })
    r.encoding = "utf-8-sig"
    temp=json.loads(r.text)
    return temp



def process_apartment_data(temp, temp_school, area_list):
    """
    Process apartment data and create a DataFrame with detailed information
    
    Args:
        temp (dict): Dictionary containing apartment complex details
        temp_school (dict): Dictionary containing school information
        area_list (list): List of apartment areas
        
    Returns:
        pd.DataFrame: DataFrame containing processed apartment information
    """
    temp_data = pd.DataFrame(index=range(len(area_list)))
    
    for i in range(len(area_list)):
        print(temp["complexDetail"]["address"], temp["complexDetail"]["complexName"])
        
        # Basic information
        temp_data.loc[i, "아파트명"] = temp["complexDetail"]["complexName"]
        temp_data.loc[i, "면적"] = area_list[i]
        temp_data.loc[i, "법정동주소"] = temp["complexDetail"]["address"] + " " + temp["complexDetail"]["detailAddress"]
        
        # Address information with error handling
        try:
            temp_data.loc[i, "도로명주소"] = temp["complexDetail"]["roadAddressPrefix"] + " " + temp["complexDetail"]["roadAddress"]
        except KeyError:
            temp_data.loc[i, "도로명주소"] = temp["complexDetail"]["roadAddressPrefix"]
            
        # Location and building information
        temp_data.loc[i, "latitude"] = temp["complexDetail"]["latitude"]
        temp_data.loc[i, "longitude"] = temp["complexDetail"]["longitude"]
        temp_data.loc[i, "세대수"] = temp["complexDetail"]["totalHouseholdCount"]
        temp_data.loc[i, "임대세대수"] = temp["complexDetail"]["totalLeaseHouseholdCount"]
        temp_data.loc[i, "최고층"] = temp["complexDetail"]["highFloor"]
        temp_data.loc[i, "최저층"] = temp["complexDetail"]["lowFloor"]
        
        # Building details with error handling
        fields_to_try = {
            "용적률": ["complexDetail", "batlRatio"],
            "건폐율": ["complexDetail", "btlRatio"],
            "주차대수": ["complexDetail", "parkingPossibleCount"],
            "건설사": ["complexDetail", "constructionCompanyName"],
            "난방": ["complexDetail", "heatMethodTypeCode"],
            "공급면적": ["complexPyeongDetailList", i, "supplyArea"],
            "전용면적": ["complexPyeongDetailList", i, "exclusiveArea"],
            "전용율": ["complexPyeongDetailList", i, "exclusiveRate"],
            "방수": ["complexPyeongDetailList", i, "roomCnt"],
            "욕실수": ["complexPyeongDetailList", i, "bathroomCnt"],
            "해당면적_세대수": ["complexPyeongDetailList", i, "householdCountByPyeong"],
            "현관구조": ["complexPyeongDetailList", i, "entranceType"]
        }
        
        for field, path in fields_to_try.items():
            try:
                value = temp
                for key in path:
                    value = value[key]
                temp_data.loc[i, field] = value
            except (KeyError, IndexError):
                temp_data.loc[i, field] = ""
        
        # Tax information
        tax_fields = {
            "재산세": "propertyTax",
            "재산세합계": "propertyTotalTax",
            "지방교육세": "localEduTax",
            "재산세_도시지역분": "cityAreaTax",
            "종합부동산세": "realEstateTotalTax",
            "결정세액": "decisionTax",
            "농어촌특별세": "ruralSpecialTax"
        }
        
        for field, key in tax_fields.items():
            try:
                temp_data.loc[i, field] = temp["complexPyeongDetailList"][i]["landPriceMaxByPtp"]["landPriceTax"][key]
            except KeyError:
                temp_data.loc[i, field] = ""
        
        # Price information
        temp_price = apt_price(apt_list[0], i)
        try:
            temp_data.loc[i, "가격"] = temp_price["marketPrices"][0]["dealAveragePrice"]
        except KeyError:
            temp_data.loc[i, "가격"] = ""
            
        # Maintenance cost and price information
        price_fields = {
            "겨울관리비": ["complexPyeongDetailList", i, "averageMaintenanceCost", "winterTotalPrice"],
            "여름관리비": ["complexPyeongDetailList", i, "averageMaintenanceCost", "summerTotalPrice"],
            "매매호가": ["complexPyeongDetailList", i, "articleStatistics", "dealPriceString"],
            "전세호가": ["complexPyeongDetailList", i, "articleStatistics", "leasePriceString"],
            "월세호가": ["complexPyeongDetailList", i, "articleStatistics", "rentPriceString"],
            "실거래가": ["complexPyeongDetailList", i, "articleStatistics", "rentPriceString"]
        }
        
        for field, path in price_fields.items():
            try:
                value = temp
                for key in path:
                    value = value[key]
                temp_data.loc[i, field] = value
            except KeyError:
                temp_data.loc[i, field] = ""
        
        # School information
        school_fields = {
            "초등학교_학군정보": "schoolName",
            "초등학교_설립정보": "organizationType",
            "초등학교_남학생수": "maleStudentCount",
            "초등학교_여학생수": "femaleStudentCount"
        }
        
        for field, key in school_fields.items():
            try:
                temp_data.loc[i, field] = temp_school['schools'][0][key]
            except (KeyError, IndexError):
                temp_data.loc[i, field] = ""
    
    return temp_data



def get_apt_info_ver2(apt_num):
    response = requests.get(f'https://new.land.naver.com/api/complexes/{apt_num}', params=params, cookies=cookies, headers=headers)
    return json.loads(response.text)


def get_article_data(apt_num, cookies, headers):
    """
    Fetch article data for an apartment complex until no new articles are found
    
    Args:
        apt_num (str): Apartment complex number
        cookies (dict): Request cookies
        headers (dict): Request headers
        
    Returns:
        tuple: (article_list, type_list, sales_num) containing article numbers, 
               their types, and total number of sales
    """
    print("func ver 1")
    article_list = []
    type_list = []
    sales_num = 0
    past_num = 0
    return_content_list=[]
    for page_num in range(1, 10000):
        print("func ver 1 Page {}".format(page_num))
        # Update cookie for pagination
        rev_cookie = cookies.copy()  # Create a copy to avoid modifying original
        rev_cookie['NACT'] = str(page_num)
        
        # Make API request
        response = requests.get(
            f'https://new.land.naver.com/api/articles/complex/{apt_num}?realEstateType=APT%3APRE%3AABYG%3AJGC&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page_num}&complexNo={apt_num}&buildingNos=&areaNos=&type=list&order=rank',
            cookies=rev_cookie,
            headers=headers
        )
        print("func ver 1 Page get  {}".format(page_num))
        # Process response
        price_info = json.loads(response.text)
        content_list = price_info['articleList']
        sales_num += len(content_list)
        
        # Progress logging
        if page_num % 100 == 0:
            print(f'{page_num} DONE')
            
        # Check if we have any content
        if not content_list:
            print(f'Page {page_num} Con num {sales_num} All content End')
            break
        print("Process content")
        print(len(content_list))    
        # Process content
        for content in content_list:
            article_list.append(content['articleNo'])
            type_list.append(f"{content['articleStatus']}_{content['tradeTypeCode']}")
            return_content_list.append(content)
        print(f'Page {page_num} Done')
        
        # Check if we found any new articles
        current_unique_articles = copy.deepcopy(len(set(article_list)))
        #if current_unique_articles == past_num:
        #    print(f'Con num {sales_num} All content End - No new articles found')
        #    break
        past_num = current_unique_articles
        #print(article_list)
        print(current_unique_articles)
    return article_list, type_list, sales_num, return_content_list


def clean_price(price_str):
    """Convert price string like '14억 5,000' to numeric value in thousands"""
    try:
        if not isinstance(price_str, str):
            return None
        # Remove all whitespace
        price_str = price_str.replace(' ', '')
        
        # Split by '억' if exists
        if '억' in price_str:
            parts = price_str.split('억')
            billion = float(parts[0]) * 10000  # 1억 = 10000만
            thousand = float(parts[1].replace(',', '')) if parts[1] else 0
            return billion + thousand
        else:
            # Handle case without '억'
            return float(price_str.replace(',', ''))
    except:
        return None

def process_article_data(temp_content_list, numofsize = None, agg_type = 'APT'):
    # Convert DataFrame if not already
    df = pd.DataFrame(temp_content_list)
    if df.empty:
        return df
    # Clean price data
    df['price_numeric'] = df['dealOrWarrantPrc'].apply(clean_price)
    
    group_by_list = ['articleName', 'tradeTypeName', 'areaName', 'area2']
    
    # Define base aggregation dictionary
    agg_dict = {
        'price_numeric': ['min', 'max', 'count'],
        'dealOrWarrantPrc': ['first', 'last'],
        'articleNo': ['count']
    }
    
    # Add numofroom to aggregation if it exists in the DataFrame
    if 'numofsize' in df.columns:
        agg_dict['numofsize'] = 'first'
    
    # Group by and aggregate
    grouped = df.groupby(group_by_list).agg(agg_dict).round(2)
    
    # Flatten column names
    grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
    
    # Reset index for easier viewing
    grouped = grouped.reset_index()
    if numofsize != None:
        grouped['numofsize'] = numofsize
    return grouped

#매매 : tradeType : A1
#전세 : tradeType : B1
#월세 ; tradeType : B2 

data_list = []
sido_list=get_sido_info()
print(sido_list)
for m in range(len(sido_list)):
    gungu_list=get_gungu_info(sido_list[m])
    gungu_apt_list=[0]*len(gungu_list)
    #print(gungu_list)
    for j in range(len(gungu_list)):#구 마다 하나씩 저장
        dong_list=get_dong_info(gungu_list[j])
        dong_apt_list=[0]*len(dong_list)
        #print(dong_list)
        for k in range(len(dong_list)):#동마다 하나씩 저장
            apt_list=get_apt_list(dong_list[k])
            apt_list_data=[0]*len(apt_list)
            #print(apt_list)
            for n in range(len(apt_list)):#아파트 마다 하나씩 저장
                print('APT {} START'.format(apt_list[n]))
                apt_num=apt_list[n]
                temp = get_apt_info_ver2(apt_num)
                temp_school = get_school_info2(apt_num)
                try:
                    area_list=temp["complexDetail"]["pyoengNames"].split(", ")
                    ex_flag=1
                    print('data_exist')
                except KeyError:   
                    ex_flag=0
                    temp_data=pd.DataFrame(columns=temp_data.columns)
                    print('data_not_exist')
                if ex_flag==1:
                    temp_data = process_apartment_data(temp, temp_school, area_list)
                    if temp_data.iloc[0]['세대수'] > 100:
                        print('Cuurent APT {} > 100'.format(apt_num))
                        article_list, type_list, sales_num, tem_content_list = get_article_data(apt_num, cookies, headers) # 매매, 전세, 월세 모두 가져오기
                        """
                        {'articleNo': '2504869173', 'articleName': '개포래미안포레스트', 'articleStatus': 'R0', 'realEstateTypeCode': 'APT', 'realEstateTypeName': '아파트', 'articleRealEstateTypeCode': 'A01', 'articleRealEstateTypeName': '아파트', 'tradeTypeCode': 'B1', 'tradeTypeName': '전세', 'verificationTypeCode': 'OWNER', 'floorInfo': '8/13', 'priceChangeState': 'SAME', 'isPriceModification': False, 'dealOrWarrantPrc': '14억 5,000', 'areaName': '115A', 'area1': 115, 'area2': 84, 'direction': '남동향', 'articleConfirmYmd': '20250127', 'siteImageCount': 0, 'articleFeatureDesc': '35 구룡초배정 판상형 대중교통편리 장기거주', 'tagList': ['10년이내', '대단지', '방세개', '화장실두개'], 'buildingName': '112동', 'sameAddrCnt': 55, 'sameAddrDirectCnt': 0, 'sameAddrMaxPrc': '15억', 'sameAddrMinPrc': '14억 5,000', 'cpid': 'asil', 'cpName': '아실', 'cpPcArticleUrl': 'https://asil.kr/asil/index.jsp?UID=2504869173', 'cpPcArticleBridgeUrl': 'https://new.land.naver.com/outLink?cpId=asil&articleNo=2504869173', 'cpPcArticleLinkUseAtArticleTitleYn': True, 'cpPcArticleLinkUseAtCpNameYn': True, 'cpMobileArticleUrl': 'https://asil.kr/app/sale_info.jsp?UID=2504869173', 'cpMobileArticleLinkUseAtArticleTitleYn': True, 'cpMobileArticleLinkUseAtCpNameYn': True, 'latitude': '37.479476', 'longitude': '127.054926', 'isLocationShow': False, 'realtorName': '구룡부동산중개', 'realtorId': 'estate_pro', 'tradeCheckedByOwner': False, 'isDirectTrade': False, 'isInterest': False, 'isComplex': True, 'detailAddress': '', 'detailAddressYn': 'N', 'isVrExposed': False}
                        """
                        processed_content_list = []
                        for item in tem_content_list:
                            item_copy = item.copy()  # Create a copy of each dictionary
                            item_copy['numofsize'] = temp_data.iloc[0]['세대수']
                            processed_content_list.append(item_copy)
                        
                        # Extend the data_list with the processed content
                        data_list.extend(processed_content_list)
                        temp_content_list = process_article_data(tem_content_list, temp_data.iloc[0]['세대수'])
                        if not temp_content_list.empty:
                            article_name = tem_content_list[0]['articleName']
                            temp_content_list.to_csv(f"C:/Users/xoxoq/Downloads/content_list_{apt_num}_{article_name}.csv", encoding="CP949")
                        print('article num : {}'.format(len(article_list)))
                        print(len(set(article_list)))
                        apt_list_data[n]=tem_content_list
                        print(apt_list_data[n])
                        pass
                if n > 10:
                    break
            if k > 2:
                break
            #if apt_list_data==[]:
            #    dong_apt_list[k]=pd.DataFrame(columns=temp_data.columns)
            #else:
            #    dong_apt_list[k]=pd.concat(apt_list_data)
        dong_data_list = process_article_data(data_list)
        dong_data_list.to_csv(f"C:/Users/xoxoq/Downloads/content_list_{dong_list[-1]}.csv", encoding="CP949")
        gungu_apt_list[j]=pd.concat(dong_apt_list)
        gungu_apt_list[j].to_csv(temp["complexDetail"]["roadAddressPrefix"]+".csv",encoding="CP949")
    final_data=pd.concat(gungu_apt_list)
    final_data.to_csv(temp["complexDetail"]["roadAddressPrefix"].split()[0]+".csv",encoding="CP949")
