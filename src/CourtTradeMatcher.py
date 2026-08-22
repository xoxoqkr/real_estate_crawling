"""
법원경매 물건 주소 → 국토교통부 실거래가 매칭 → 시세 비교

CourtNaverMatcher.py를 대체 (네이버 API 차단으로 인해)
"""
import re, time
import pandas as pd
from AptTradeAPI import get_lawd_cd, get_trade_prices, match_by_area_and_dong


def parse_court_address(addr: str) -> dict:
    """법원경매 물건주소 파싱 - 핵심: 시군구 + 동 + 면적"""
    addr = addr.strip()

    # 여러 주소가 병합된 경우 첫 번째 대괄호 주소 추출
    parts = re.split(r'\s{2,}', addr)
    if len(parts) > 1:
        addr = next((p for p in parts if '[' in p), addr)

    # 괄호 제거, 연속 공백 제거
    clean = re.sub(r'\s*\([^)]*\)\s*', ' ', addr)
    clean = re.sub(r'\s+', ' ', clean).strip()

    result = {'sido': None, 'gungu': None, 'dong': None,
              'area_m2': None, 'is_land': False}

    # 시도 + 시군구 추출
    sg = re.match(r'(.+?[시도])\s+(.+?[시군구])\s+(.+)', clean)
    if not sg:
        return None
    sido, gungu, rest = sg.group(1), sg.group(2), sg.group(3)

    # 면적 추출: [ ... 84.97㎡ ... ]
    area_m = re.search(r'\[.*?(\d+(?:\.\d+)?)\s*㎡', clean)
    if not area_m:
        return None
    area_m2 = float(area_m.group(1))

    # 토지 여부
    is_land = '토지' in clean.split('[')[-1].split(']')[0]

    # 동명 추출: 첫 번째 토큰 (e.g., 대치동, 길음2동, 동소문동7가, 솔매로8길)
    dong = rest.split()[0].strip()

    # 좌우 한자/숫자 트리밍
    result.update({
        'sido': sido, 'gungu': gungu, 'dong': dong,
        'area_m2': area_m2, 'is_land': is_land,
    })
    return result


def get_recent_trades(api_key: str, gungu: str, dong: str, months_back: int = 12) -> pd.DataFrame:
    """
    법정동의 최근 실거래가 조회.

    2026-08-22: 기존에 AptTradeAPI.get_trade_prices()와 동일한 로직을 이 파일에
    별도로 중복 구현해놓았던 것을 제거하고 그쪽 함수를 재사용하도록 변경함.
    get_trade_prices()가 이후 개선(numOfRows 확대, 구/동/월 단위 캐싱)되면
    match_batch()로 여러 사건을 배치 매칭할 때도 자동으로 그 이득을 받는다
    (배치 매칭 246건 기준 25분 이상 걸리던 것을 이 문제 발견 후 개선함).
    """
    try:
        return get_trade_prices(api_key, gungu, dong, months_back=months_back)
    except ValueError:
        return pd.DataFrame()


def match_court_to_market(api_key: str, court_addr: str, court_gameval_amt: str = None) -> dict:
    """법원경매 주소 → 실거래가 매칭 전체 파이프라인"""
    result = {'court_address': court_addr, 'success': False}
    
    # Step 1: 주소 파싱
    parsed = parse_court_address(court_addr)
    if not parsed:
        result['error'] = '주소 파싱 실패'
        return result
    result['parsed'] = parsed
    
    # Step 2: 토지 제외 (실거래가 API는 아파트/빌라만 제공)
    if parsed['is_land']:
        result['error'] = '토지 매물 (아파트 실거래가 매칭 불가)'
        return result
    
    # Step 3: 법정동 코드 확인
    lawd_cd = get_lawd_cd(parsed['gungu'])
    if not lawd_cd:
        result['error'] = '법정동 코드 없음: ' + parsed['gungu']
        return result
    result['lawd_cd'] = lawd_cd
    
    # Step 4: 실거래가 조회
    df = get_recent_trades(api_key, parsed['gungu'], parsed['dong'], months_back=12)
    if df.empty:
        result['error'] = '실거래가 데이터 없음'
        return result
    result['trade_count_total'] = len(df)
    
    # Step 5: 면적 매칭
    prices = match_by_area_and_dong(df, parsed['area_m2'])
    if prices.empty:
        result['error'] = '면적 매칭 실패'
        return result
    result['market_prices'] = prices.to_dict('records')
    result['success'] = True
    
    # Step 6: 감정가 비교 (감정가는 원 단위 → 만원 변환)
    if court_gameval_amt:
        try:
            raw = str(court_gameval_amt).replace(',', '').replace(' ', '')
            gameval_won = int(float(raw))  # 원 단위
            gameval_man = gameval_won / 10000  # 만원 단위 변환
            avg_price = prices['평균가_만원'].iloc[0]
            result['gameval_amt_won'] = gameval_won
            result['gameval_amt'] = gameval_man
            result['avg_market_price'] = avg_price
            result['diff_ratio'] = round((avg_price - gameval_man) / gameval_man * 100, 1)
            result['diff_text'] = f"{'↑' if result['diff_ratio'] > 0 else '↓'} {abs(result['diff_ratio'])}%"
        except Exception as e:
            result['compare_error'] = str(e)
    
    return result


def match_batch(api_key: str, court_df: pd.DataFrame) -> pd.DataFrame:
    """법원경매 DataFrame 전체를 batch 매칭"""
    # 컬럼명 자동 매핑 (원본/processed 호환)
    addr_col = next((c for c in court_df.columns if c in ('물건주소', 'printSt')), None)
    gameval_col = next((c for c in court_df.columns if c in ('감정가', 'gamevalAmt')), None)

    if not addr_col:
        raise ValueError('주소 컬럼(물건주소/printSt)을 찾을 수 없습니다')

    rows = []
    for _, row in court_df.iterrows():
        r = match_court_to_market(api_key, row.get(addr_col, ''),
                                   row.get(gameval_col) if gameval_col else None)
        rows.append(r)
        time.sleep(0.5)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    # 테스트
    print("법원경매 → 실거래가 매칭 테스트")
    print("="*50)
    print()
    api_key = input("API 키: ").strip()
    
    if api_key:
        test_addr = "서울특별시 강남구 대치동 890-20 1층101호 [집합건물 철근콘크리트조 84.97㎡]"
        print(f'\n테스트 주소: {test_addr}\n')
        result = match_court_to_market(api_key, test_addr, '100,000')
        for k, v in result.items():
            if k == 'market_prices':
                print(f'{k}:')
                for p in v:
                    print(f'  {p}')
            else:
                print(f'{k}: {v}')
