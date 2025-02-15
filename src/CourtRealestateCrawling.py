import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup



def setup_webdriver_old():
    """
    Chrome 웹드라이버를 설정하고 반환하는 함수입니다.

    Returns:
        webdriver.Chrome: 다음 옵션들이 설정된 Chrome 웹드라이버:
            - headless 모드 활성화 (브라우저 UI 없이 실행)
            - no-sandbox 모드 활성화 (보안 샌드박스 비활성화)
            - disable-dev-shm-usage (공유 메모리 사용 비활성화)
            - implicit wait 시간 10초 설정

    설정 과정:
        1. Chrome 옵션 설정 (headless, no-sandbox, disable-dev-shm-usage)
        2. ChromeDriver 서비스 생성 및 자동 설치
        3. WebDriver 생성 및 implicit wait 설정

    예시:
        >>> driver = setup_webdriver()
        >>> driver.get("https://example.com")
        >>> driver.quit()
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def setup_webdriver():
    options = Options()
    
    # 운영체제 확인
    import platform
    is_windows = platform.system() == 'Windows'
    
    if not is_windows:  # Linux 환경
        options.binary_location = "/usr/bin/google-chrome"
    
    # 공통 옵션 설정
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1024")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        # ChromeDriver 자동 설치 및 설정
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"ChromeDriver 설정 중 오류 발생: {e}")
        raise


def navigate_to_search_page(driver, court_name :str = None, area_name :str = None):
    """
    법원 경매 데이터를 처리하여 같은 사건번호를 가진 행들의 물건주소를 병합하는 함수입니다.

    Args:
        df (pd.DataFrame): 원본 법원 경매 데이터프레임. 다음 컬럼들을 포함해야 합니다:
            - checkBox: 선택 체크박스
            - printCsNo: 사건번호 
            - maemulSer: 물건번호
            - printSt: 물건주소
            - mapBtn: 지도 아이콘
            - mulBigo: 비고
            - gamevalAmt: 감정가
            - jpDeptNm: 담당계
            - dspslUsgNm: 주용도
            - notifyMinmaePrice1: 최저가
            - yuchalCnt: 유찰횟수

    Returns:
        pd.DataFrame: 처리된 데이터프레임으로 다음과 같은 특징을 가집니다:
            - 컬럼명이 한글로 변경됨
            - 필요한 컬럼만 선택됨 ('사건번호', '물건주소', '비고', '감정가', '담당계', '최저가', '유찰횟수')
            - 같은 사건번호를 가진 행들의 물건주소가 병합됨
            - 사건번호가 없는 행의 물건주소는 이전 사건번호의 물건주소에 병합됨

    처리 과정:
        1. 컬럼명을 한글로 변경
        2. 필요한 컬럼만 선택
        3. 사건번호가 없는 행의 물건주소를 이전 사건번호의 데이터에 병합
        4. 같은 사건번호를 가진 행들의 물건주소를 병합

    예시:
        >>> df = pd.DataFrame({...})  # 원본 데이터
        >>> processed_df = process_court_data(df)
        >>> print(processed_df)  # 처리된 데이터
    """
    driver.get("https://www.courtauction.go.kr/pgj/index.on")
    wait = WebDriverWait(driver, 10)
    
    # 법원 선택
    if court_name != None:
        court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
        court_select.select_by_visible_text(court_name)
    #지역 선택
    if area_name != None:
        court_select = Select(driver.find_element(By.ID, "mf_sbx_rletRpdtCortLst"))
        court_select.select_by_visible_text(area_name)
    """
    mf_sbx_rletRpdtSggLst 는 시/도 하위의 행정구역(주로 시/군/구)을 의미함.
    """
    # 검색 버튼 클릭
    search_button = wait.until(EC.element_to_be_clickable((By.ID, "mf_btn_quickSearchGds")))
    #search_button.click()
    click_button(driver, search_button)

def extract_results(driver, loading_wait_time_sec :int = 3):
    """
    웹드라이버로부터 법원 경매 데이터를 추출하여 DataFrame으로 반환하는 함수입니다.

    Args:
        driver (webdriver.Chrome): 법원 경매 페이지가 로드된 Chrome 웹드라이버
        loading_wait_time (int): 페이지 로딩 대기 시간 단위 초 (기본값: 3초)
    Returns:
        pd.DataFrame: 추출된 경매 데이터를 포함하는 DataFrame으로 다음과 같은 특징을 가집니다:
            - 각 행은 하나의 경매 물건 정보를 나타냄
            - 'printCsNo'(사건번호)가 없는 행은 제거됨
            - 같은 물건에 대한 추가 정보는 하나의 행으로 병합됨

    처리 과정:
        1. 페이지 로딩을 위해 3초 대기
        2. BeautifulSoup을 사용하여 HTML 파싱
        3. 'grid_body_row' 클래스를 가진 모든 행 추출
        4. 각 셀(td)의 data-col_id 속성을 키로 하여 데이터 추출
        5. 사건번호('printCsNo')가 있는 행을 기준으로 데이터 병합
        6. 결과를 DataFrame으로 변환

    예시:
        >>> driver = setup_webdriver()
        >>> driver.get("https://www.courtauction.go.kr/...")
        >>> df = extract_results(driver)
        >>> print(df.columns)  # 추출된 컬럼 확인
        >>> driver.quit()
    """
    time.sleep(loading_wait_time_sec)  # 페이지 로딩 대기
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    results = []
    temp_row = {}
    
    for row in soup.find_all('tr', class_='grid_body_row'):
        case_info = {}
        
        for td in row.find_all('td'):
            col_id = td.get('data-col_id')
            if col_id:
                case_info[col_id] = ' '.join(td.stripped_strings)
        
        if 'printCsNo' in case_info:
            if temp_row:
                results.append(temp_row)
            temp_row = case_info  # 새 사건 정보 시작
        else:
            for key, value in case_info.items():
                if key in temp_row:
                    temp_row[key] += f" {value}"  # 기존 값과 합치기
                else:
                    temp_row[key] = value
    
    if temp_row:
        results.append(temp_row)
    
    df = pd.DataFrame(results)
    df = df.dropna(subset=['printCsNo'])  # Drop rows where 'printCsNo' is NaN
    return df


def click_button(driver, button):
    try:
        # 버튼이 보일 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "w2pageList_col_next"))
        )
        
        # 버튼이 화면에 보이도록 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        
        # 버튼이 클릭 가능할 때까지 대기
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "w2pageList_col_next"))
        ).click()
    
    except:
        try:
            # 만약 클릭이 막히면 ActionChains로 클릭
            actions = ActionChains(driver)
            actions.move_to_element(button).click().perform()
        except:
            # 그래도 클릭이 안 되면 JavaScript를 사용한 강제 클릭
            driver.execute_script("arguments[0].click();", button)


def paginate_and_extract(driver, max_pages : int = 100, loading_wait_time_sec :int = 3):
    all_results = pd.DataFrame()
    current_page = 1
    while True:
        try:
            # 데이터 추출 전에 페이지 로딩 대기 추가
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "grid_body_row"))
            )
            
            result_df = extract_results(driver, loading_wait_time_sec)
            
            # 데이터 유효성 검사 추가
            if result_df.empty or 'printCsNo' not in result_df.columns:
                print(f"페이지 {current_page}에서 유효한 데이터를 찾을 수 없습니다.")
                break
                
            print(result_df[['printCsNo','maemulSer']])
            all_results = pd.concat([all_results, result_df], ignore_index=True)
            
            # 다음 페이지 버튼 클릭 전 대기 시간 추가
            time.sleep(loading_wait_time_sec)
            
            print('current page : {}'.format(current_page))
            next_page = current_page + 1
            
            if next_page % 10 == 1:
                try:
                    next_list_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "w2pageList_col_next"))
                    )
                    click_button(driver, next_list_button)
                except Exception as e:
                    print(f"다음 목록 버튼 클릭 중 오류 발생: {e}")
                    break
            else:
                try:
                    next_page_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, f"mf_wfm_mainFrame_pgl_gdsDtlSrchPage_page_{next_page}"))
                    )
                    click_button(driver, next_page_button)
                except Exception as e:
                    print(f"페이지 {next_page} 이동 중 오류 발생: {e}")
                    break
            
            current_page += 1
            if current_page >= max_pages:
                break
                
        except Exception as e:
            print(f"페이지 {current_page} 처리 중 오류 발생: {e}")
            break
    
    return all_results


def process_court_data(df : pd.DataFrame, save_dir : str, uuid : str):
    """
    법원 경매 데이터를 처리하여 같은 사건번호를 가진 행들의 물건주소를 병합하고 중간 결과를 저장하는 함수입니다.

    Args:
        df (pd.DataFrame): 원본 법원 경매 데이터프레임. 다음 컬럼들을 포함해야 합니다:
            - checkBox: 선택 체크박스
            - printCsNo: 사건번호 
            - maemulSer: 물건번호
            - printSt: 물건주소
            - mapBtn: 지도 아이콘
            - mulBigo: 비고
            - gamevalAmt: 감정가
            - jpDeptNm: 담당계
            - dspslUsgNm: 주용도
            - notifyMinmaePrice1: 최저가
            - yuchalCnt: 유찰횟수
        save_dir (str): 중간 결과 파일을 저장할 디렉토리 경로
        uuid (str): 파일명에 사용될 고유 식별자

    Returns:
        pd.DataFrame: 처리된 데이터프레임으로 다음과 같은 특징을 가집니다:
            - 컬럼명이 한글로 변경됨
            - 필요한 컬럼만 선택됨 ('사건번호', '물건주소', '비고', '감정가', '담당계', '최저가', '유찰횟수')
            - 같은 사건번호를 가진 행들의 물건주소가 병합됨
            - 사건번호가 없는 행의 물건주소는 이전 사건번호의 물건주소에 병합됨

    처리 과정:
        1. 컬럼명을 한글로 변경하고 필요한 컬럼 선택
        2. 연속된 같은 사건번호를 가진 행들의 물건주소 병합
        3. 중간 결과를 CSV 파일로 저장
        4. 저장된 파일을 다시 로드하여 추가 처리
        5. 사건번호가 없는 행의 물건주소를 이전 사건번호의 데이터에 병합
        6. 최종 결과 생성

    파일 저장:
        - 중간 결과가 '{save_dir}court_Data_step1_{uuid}.csv' 형식으로 저장됨

    예시:
        >>> df = pd.DataFrame({...})  # 원본 데이터
        >>> save_dir = "data/"
        >>> uuid_str = "12345"
        >>> processed_df = process_court_data(df, save_dir, uuid_str)
        >>> print(processed_df)  # 처리된 데이터
    """
    # Rename columns
    column_mapping = {
        'checkBox': '선택',
        'printCsNo': '사건번호',
        'maemulSer': '번호',
        'printSt': '물건주소',
        'mapBtn': '지도icon',
        'mulBigo': '비고',
        'gamevalAmt': '감정가',
        'jpDeptNm': '담당계',
        'dspslUsgNm': '주용도',
        'notifyMinmaePrice1': '최저가',
        'yuchalCnt': '유찰횟수'
    }
    df = df.rename(columns=column_mapping)
    merged_result_df = df[['사건번호', '물건주소', '비고', '감정가', '담당계', '최저가', '유찰횟수']]
    
    # Step 1: Merge rows without case numbers
    combined_rows = []
    previous_row = None

    for ite, row in merged_result_df.iterrows():
        if previous_row is None:
            previous_row = row.copy()
            continue

        if row['사건번호'] == previous_row['사건번호']:
            # 같은 사건번호인 경우 물건주소만 합치기
            if pd.notna(row['물건주소']):
                if pd.notna(previous_row['물건주소']):
                    previous_row['물건주소'] = f"{previous_row['물건주소']} {row['물건주소']}"
                else:
                    previous_row['물건주소'] = row['물건주소']
        else:
            # 다른 사건번호를 만나면 이전 row 저장하고 새로운 row 설정
            combined_rows.append(previous_row)
            previous_row = row.copy()

    # 마지막 row 처리
    if previous_row is not None:
        combined_rows.append(previous_row)

    # 새로운 DataFrame 생성
    merged_result_df = pd.DataFrame(combined_rows)
    saved_name = f'{save_dir}court_Data_step1_{uuid}.csv'
    merged_result_df.to_csv(saved_name)
    merged_result_df = pd.read_csv(saved_name)
    case_dict = {}
    previous_row = None
    for ite, row in merged_result_df.iterrows():
        case_no = row['사건번호']
        if previous_row is None:
            previous_row = row.copy()
            case_dict[case_no] = row.copy()
            continue
        #print(row)
        if pd.isna(row['사건번호']):
            #print('case1')
            case_no = previous_row['사건번호']
            case_dict[case_no]['물건주소'] = f"{case_dict[case_no]['물건주소']}  {row['물건주소']}"
        elif row['사건번호'] in case_dict:
            #print('case2')
            case_dict[case_no]['물건주소'] = f"{case_dict[case_no]['물건주소']}  {row['물건주소']}"
        else:
            #print('case3')
            case_dict[case_no] = row.copy()
            previous_row = row.copy()
    # 딕셔너리를 DataFrame으로 변환
    merged_result_df = pd.DataFrame(list(case_dict.values()))

    return merged_result_df

#각 링크에 해당 물건의 url을 넣는 방법

"""
if __name__ == "__main__":
    save_dir = 'C:/Users/xoxoq/Downloads/'
    driver = setup_webdriver()
    navigate_to_search_page(driver, court_name = "서울중앙지방법원") # area_name = "서울특별시" #함수를 수정해서 원하는 법원 이름을 넣으면 됨.
    merged_result_df = paginate_and_extract(driver, max_pages=40)
    try:
        merged_result_df.to_csv(f'{save_dir}court_Data_org.csv')
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
    merged_result_df = process_court_data(merged_result_df, save_dir, uuid) #중간에 저장되는 데이터 프레임의 저장 위치를 조심할 것.
    #merged_result_df = process_court_data2(merged_result_df)
    try:
        merged_result_df.to_csv(f'{save_dir}court_Data_porcessed.csv')
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
    #result_df = extract_results(driver)
    driver.quit()
    print("크롤링된 종료")
"""
    