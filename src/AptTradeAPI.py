"""
국토교통부 실거래가 API를 통한 시세 조회 모듈
"""
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
from datetime import datetime, timedelta

# 법정동 코드 (서울시 구 단위, 앞 5자리)
LAWD_CD_MAP = {
    '종로구': '11110', '중구': '11140', '용산구': '11170',
    '성동구': '11200', '광진구': '11215', '동대문구': '11230',
    '중랑구': '11260', '성북구': '11290', '강북구': '11305',
    '도봉구': '11320', '노원구': '11350', '은평구': '11380',
    '서대문구': '11410', '마포구': '11440', '양천구': '11470',
    '강서구': '11500', '구로구': '11530', '금천구': '11545',
    '영등포구': '11560', '동작구': '11590', '관악구': '11620',
    '서초구': '11650', '강남구': '11680', '송파구': '11710',
    '강동구': '11740',
}

# 기타 지역 코드 (필요시 추가)
EXTRA_LAWD_CD = {
    # 경기도
    '수원시장안구': '41111', '수원시권선구': '41113', '수원시팔달구': '41115',
    '수원시영통구': '41117', '성남시수정구': '41131', '성남시중원구': '41133',
    '성남시분당구': '41135', '고양시덕양구': '41281', '고양시일산동구': '41285',
    '고양시일산서구': '41287', '용인시처인구': '41461', '용인시기흥구': '41463',
    '용인시수지구': '41465', '부천시': '41192', '안양시만안구': '41171',
    '안양시동안구': '41173', '남양주시': '41360',
    # 인천
    '중구': '28110', '동구': '28140', '미추홀구': '28177',
    '연수구': '28185', '남동구': '28200', '부평구': '28237',
    '계양구': '28245', '서구': '28260',
}


def get_lawd_cd(gungu_name: str) -> str:
    """구군명 → 법정동코드(앞5자리)"""
    if gungu_name in LAWD_CD_MAP:
        return LAWD_CD_MAP[gungu_name]
    if gungu_name in EXTRA_LAWD_CD:
        return EXTRA_LAWD_CD[gungu_name]
    return None


def fetch_apt_trade(service_key: str, lawd_cd: str, deal_ym: str, 
                     page_no: int = 1, num_of_rows: int = 100) -> dict:
    """
    국토교통부 실거래가 API 호출
    
    Args:
        service_key: data.go.kr API 인증키 (Decoding)
        lawd_cd: 법정동코드 앞 5자리
        deal_ym: 계약년월 (YYYYMM)
        page_no: 페이지 번호
        num_of_rows: 페이지당 건수
    
    Returns:
        API 응답 (딕셔너리)
    """
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    
    params = {
        'serviceKey': service_key,
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ym,
        'pageNo': str(page_no),
        'numOfRows': str(num_of_rows),
    }
    
    resp = requests.get(url, params=params, timeout=15)
    
    if resp.status_code != 200:
        return {'error': f'HTTP {resp.status_code}', 'body': resp.text[:500]}
    
    # XML 파싱
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        return {'error': f'XML parse error: {e}', 'body': resp.text[:500]}
    
    # 결과 코드 확인
    header = root.find('.//header')
    if header is not None:
        result_code = header.findtext('resultCode', '')
        result_msg = header.findtext('resultMsg', '')
        if result_code != '00' and result_code != '000':
            return {'error': f'API error [{result_code}]: {result_msg}'}
    
    # 아이템 파싱
    items = []
    for item in root.findall('.//item'):
        items.append({
            'aptNm': item.findtext('aptNm', ''),           # 아파트명
            'umdNm': item.findtext('umdNm', ''),           # 법정동명
            'excluUseAr': item.findtext('excluUseAr', ''), # 전용면적(㎡)
            'floor': item.findtext('floor', ''),           # 층
            'dealAmount': item.findtext('dealAmount', ''), # 거래금액(만원)
            'dealYear': item.findtext('dealYear', ''),     # 거래년
            'dealMonth': item.findtext('dealMonth', ''),   # 거래월
            'dealDay': item.findtext('dealDay', ''),       # 거래일
            'buildYear': item.findtext('buildYear', ''),   # 건축년도
            'sggCd': item.findtext('sggCd', ''),           # 시군구코드
        })
    
    total_count = root.findtext('.//totalCount', '0')
    
    return {
        'items': items,
        'totalCount': int(total_count) if total_count.isdigit() else 0,
        'pageNo': page_no,
        'numOfRows': num_of_rows,
    }


# 구 단위 조회 결과 캐시: {(lawd_cd, deal_ym): items}
# 같은 구/동에 속한 여러 법원경매 물건을 배치로 매칭할 때(예: CourtTradeMatcher.match_batch)
# 동일한 (법정동코드, 계약년월) 조합을 반복 조회하는 것을 피하기 위함.
# 2026-08-22: 마이옥션 3사 교차검증 작업 중 한 배치(246건) 매칭이 25분 넘게 걸려서 추가함.
_TRADE_CACHE: dict = {}


def get_trade_prices(service_key: str, gungu: str, dong: str,
                     months_back: int = 6, area_tolerance: float = 5.0,
                     use_cache: bool = True) -> pd.DataFrame:
    """
    특정 동의 최근 실거래가 조회

    Args:
        service_key: API 키
        gungu: 구군명 (예: '성북구')
        dong: 동명 (예: '정릉동') - API에는 없지만 필터용
        months_back: 조회할 과거 개월 수
        area_tolerance: 면적 매칭 허용 오차
        use_cache: True(기본값)면 (법정동코드, 계약년월) 단위로 프로세스 내
            메모리 캐시를 사용 - 같은 구의 다른 동/사건을 연달아 조회할 때
            중복 API 호출을 없애준다. 장시간 실행되는 배치에서 캐시가
            무한정 쌓이는 게 우려되면 False로 끄거나 `clear_trade_cache()` 호출.

    Returns:
        실거래가 DataFrame

    성능 참고 (2026-08-22): 국토부 API는 기본 100건/페이지라 강남구 등
    거래량 많은 구는 한 달에 300~500건씩 나와 페이지를 여러 번 나눠 호출해야
    했다. `numOfRows=1000`으로 올리면 실측상 한 달치가 보통 한 번의 호출로
    끝난다 (한 달에 1000건 넘는 극단적 케이스만 추가 페이지 필요) - 이 함수는
    이제 첫 호출부터 numOfRows=1000을 사용한다.
    """
    lawd_cd = get_lawd_cd(gungu)
    if not lawd_cd:
        raise ValueError(f'구군 코드를 찾을 수 없음: {gungu}')

    NUM_OF_ROWS = 1000
    all_items = []
    today = datetime.now()

    for i in range(months_back):
        # 해당 월 계산
        ym = today - timedelta(days=30 * i)
        deal_ym = ym.strftime('%Y%m')
        cache_key = (lawd_cd, deal_ym)

        if use_cache and cache_key in _TRADE_CACHE:
            all_items.extend(_TRADE_CACHE[cache_key])
            continue

        print(f'  조회: {deal_ym} (법정동코드: {lawd_cd})...')

        # 1페이지 조회 (대용량 페이지 크기로 대부분 한 번에 끝남)
        result = fetch_apt_trade(service_key, lawd_cd, deal_ym, num_of_rows=NUM_OF_ROWS)

        if 'error' in result:
            print(f'    오류: {result["error"]}')
            if use_cache:
                _TRADE_CACHE[cache_key] = []
            continue

        items = result.get('items', [])
        total = result.get('totalCount', 0)
        print(f'    {len(items)}건 (전체: {total}건)')

        # 한 달에 NUM_OF_ROWS건을 초과하는 극단적 케이스에 대한 안전망
        page = 1
        while len(items) < total and len(items) >= NUM_OF_ROWS * page:
            page += 1
            result = fetch_apt_trade(service_key, lawd_cd, deal_ym, page_no=page, num_of_rows=NUM_OF_ROWS)
            if 'error' not in result:
                items.extend(result.get('items', []))
            time.sleep(0.2)

        if use_cache:
            _TRADE_CACHE[cache_key] = items
        all_items.extend(items)

    if not all_items:
        return pd.DataFrame()

    df = pd.DataFrame(all_items)

    # 동 필터
    if dong:
        df = df[df['umdNm'].str.contains(dong, na=False)].copy()

    # 가격 숫자 변환
    df['price'] = df['dealAmount'].str.replace(',', '').astype(float)
    df['area_m2'] = pd.to_numeric(df['excluUseAr'], errors='coerce')

    return df


def clear_trade_cache():
    """`get_trade_prices()`의 (법정동코드, 계약년월) 캐시를 비운다."""
    _TRADE_CACHE.clear()


def match_by_area_and_dong(df: pd.DataFrame, court_area_m2: float, 
                           tolerance: float = 5.0) -> pd.DataFrame:
    """면적 기준 매칭"""
    if df.empty:
        return pd.DataFrame()
    
    df['area_diff'] = (df['area_m2'] - court_area_m2).abs()
    matched = df[df['area_diff'] <= tolerance].copy()
    
    if matched.empty:
        # 가장 가까운 면적으로
        matched = df.loc[df['area_diff'].idxmin()].to_frame().T
    
    # 집계
    result = matched.groupby('area_m2').agg(
        거래건수=('price', 'count'),
        최저가=('price', 'min'),
        최고가=('price', 'max'),
        평균가=('price', 'mean'),
        대표단지=('aptNm', lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
    ).reset_index()
    
    result.columns = ['전용면적_m2', '거래건수', '최저가_만원', '최고가_만원', '평균가_만원', '대표단지']
    result['평균가_만원'] = result['평균가_만원'].apply(lambda x: int(round(x)))
    # 면적 차이순 정렬 (가장 가까운 매칭이 첫 row)
    area_diff_map = matched.groupby('area_m2')['area_diff'].min().to_dict()
    result['면적차이'] = result['전용면적_m2'].map(area_diff_map)
    result = result.sort_values('면적차이').reset_index(drop=True).drop(columns=['면적차이'])
    return result


if __name__ == '__main__':
    # 테스트 (API 키 필요)
    print("국토교통부 실거래가 API 테스트")
    print("="*40)
    print()
    print("API 키를 입력하세요 (data.go.kr에서 발급):")
    api_key = input("> ").strip()
    
    if api_key:
        print(f"\n강남구 최근 3개월 실거래가 조회 중...")
        df = get_trade_prices(api_key, '강남구', '대치동', months_back=3)
        if not df.empty:
            print(f"\n조회 결과: {len(df)}건")
            print(df[['aptNm', 'umdNm', 'area_m2', 'price', 'dealYear', 'dealMonth']].head(10).to_string())
        else:
            print("데이터 없음 (API 키 확인 필요)")
    else:
        print("API 키가 필요합니다.")
