import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
import numpy as np
import re

def setup_webdriver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

def navigate_to_search_page(driver):
    driver.get("https://www.courtauction.go.kr/")
    driver.switch_to.frame("indexFrame")
    wait = WebDriverWait(driver, 10)
    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='qk_srch_link_1']/a")))
    search_button.click()

def set_search_criteria(driver, input_data, building_codes):
    setCourt = Select(driver.find_element(By.ID, 'idJiwonNm'))
    setCourt.select_by_value(input_data['jiwon'])

    setAPT = Select(driver.find_element(By.NAME, 'lclsUtilCd'))
    setAPT.select_by_value("0000802")
    setAPT = Select(driver.find_element(By.NAME, 'mclsUtilCd'))
    setAPT.select_by_value("000080201")
    setAPT = Select(driver.find_element(By.NAME, 'sclsUtilCd'))
    setAPT.select_by_value(building_codes[input_data['building']])

    time_textbox = driver.find_element(By.NAME, 'termStartDt')
    time_textbox.clear()
    time_textbox.send_keys(input_data['start_date'])
    time_textbox = driver.find_element(By.NAME, 'termEndDt')
    time_textbox.clear()
    time_textbox.send_keys(input_data['end_date'])

    driver.find_element(By.XPATH, '//*[@id="contents"]/form/div[2]/a[1]/img').click()

def change_items_per_page(driver):
    if driver.find_elements(By.ID, 'ipage'):
        setPage = Select(driver.find_element(By.ID, 'ipage'))
        setPage.select_by_value("default40")
    else:
        driver.find_element(By.XPATH, '//*[@id="contents"]/div[4]/form[1]/div/div/a[4]/img').click()

def extract_table_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find('table', attrs={'class': 'Ltbl_list'})
    table_rows = table.find_all('tr')
    row_list = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        row_list.append(row)
    return pd.DataFrame(row_list).iloc[1:]

def navigate_pages(driver, aution_item):
    page = 1
    while True:
        aution_item = pd.concat([aution_item, extract_table_data(driver)], ignore_index=True)
        page2parent = driver.find_element(By.CLASS_NAME, 'page2')
        children = page2parent.find_elements(By.XPATH, '*')
        if page == 1:
            if len(children) == page:
                break
            else:
                children[page].click()
        elif page <= 10:
            if len(children) - 1 == page:
                break
            else:
                children[page + 1].click()
        else:
            if len(children) - 2 == (page % 10):
                break
            else:
                children[(page % 10) + 2].click()
        page += 1
    driver.find_element(By.XPATH, '//*[@id="contents"]/div[4]/form[1]/div/div/a[4]/img').click()
    return aution_item

def clean_table_data(aution_item):
    aution_item = aution_item.iloc[:, 1:]
    col_list = ['사건번호', '물건번호', '소재지', '비고', '감정평가액', '날짜']
    aution_item.columns = col_list
    for col in col_list:
        aution_item[col] = aution_item[col].str.replace('\t', '')
        aution_item[col] = aution_item[col].apply(lambda x: re.sub(r"\n+", "\n", x))

    aution_item['법원'] = aution_item['사건번호'].str.split('\n').str[1]
    aution_item['사건번호'] = aution_item['사건번호'].str.split('\n').str[2]
    aution_item['용도'] = aution_item['물건번호'].str.split('\n').str[2]
    aution_item['물건번호'] = aution_item['물건번호'].str.split('\n').str[1]
    aution_item['내역'] = aution_item['소재지'].str.split('\n').str[2:].str.join(' ')
    aution_item['소재지'] = aution_item['소재지'].str.split('\n').str[1]
    aution_item['비고'] = aution_item['비고'].str.split('\n').str[1]
    aution_item['최저가격'] = aution_item['감정평가액'].str.split('\n').str[2]
    aution_item['최저비율'] = aution_item['감정평가액'].str.split('\n').str[3].str[1:-1]
    aution_item['감정평가액'] = aution_item['감정평가액'].str.split('\n').str[1]
    aution_item['유찰횟수'] = aution_item['날짜'].str.split('\n').str[3].str.strip()
    aution_item['유찰횟수'] = np.where(aution_item['유찰횟수'].str.len() == 0, '0회', aution_item['유찰횟수'].str.slice(start=2))
    aution_item['날짜'] = aution_item['날짜'].str.split('\n').str[2]

    aution_item = aution_item[['날짜', '법원', '사건번호', '물건번호', '용도', '감정평가액', '최저가격', '최저비율', '유찰횟수', '소재지', '내역', '비고']]
    aution_item = aution_item[~aution_item['비고'].str.contains('지분매각')].reset_index(drop=True)
    return aution_item

def encode_to_euc_kr_url(korean_text):
    euc_kr_encoded = korean_text.encode('euc-kr')
    return urllib.parse.quote(euc_kr_encoded)

def create_url(row):
    court_name_encoded = encode_to_euc_kr_url(row["법원"])
    sa_year, sa_ser = row["사건번호"].split("타경")
    url = f"https://www.courtauction.go.kr/RetrieveRealEstDetailInqSaList.laf?jiwonNm={court_name_encoded}&saYear={sa_year}&saSer={sa_ser}&_CUR_CMD=InitMulSrch.laf&_SRCH_SRNID=PNO102014&_NEXT_CMD=RetrieveRealEstDetailInqSaList.laf"
    return url

def main(input_data, building_codes):
    driver = setup_webdriver()
    navigate_to_search_page(driver)
    set_search_criteria(driver, input_data, building_codes)
    change_items_per_page(driver)
    aution_item = pd.DataFrame()
    aution_item = navigate_pages(driver, aution_item)
    aution_item = clean_table_data(aution_item)
    aution_item["URL"] = aution_item.apply(create_url, axis=1)
    driver.quit()
    return aution_item

# Streamlit UI
st.title('법원 경매 검색')

# Input form
with st.form(key='search_form'):
    jiwon = st.selectbox('지원', ['서울중앙지방법원', '서울동부지방법원', '서울서부지방법원'])
    building = st.selectbox('건물 유형', ["단독주택", "다가구주택", "다중주택", "아파트", "연립주택", "다세대주택", "기숙사", "빌라", "상가주택", "오피스텔", "주상복합"])
    start_date = st.date_input('시작 날짜')
    end_date = st.date_input('종료 날짜')
    submit_button = st.form_submit_button(label='검색')

if submit_button:
    input_data = {
        'jiwon': jiwon,
        'building': building,
        'start_date': start_date.strftime('%Y.%m.%d'),
        'end_date': end_date.strftime('%Y.%m.%d')
    }

    building_codes = {
        "단독주택": "00008020101",
        "다가구주택": "00008020102",
        "다중주택": "00008020103",
        "아파트": "00008020104",
        "연립주택": "00008020105",
        "다세대주택": "00008020106",
        "기숙사": "00008020107",
        "빌라": "00008020108",
        "상가주택": "00008020109",
        "오피스텔": "00008020110",
        "주상복합": "00008020111"
    }

    auction_data = main(input_data, building_codes)
    st.dataframe(auction_data)