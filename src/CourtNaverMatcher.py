"""
법원경매 물건 주소 → 네이버 부동산 단지 매칭 → 시세(매매가) 조회

Matching strategy:
  1. Parse court auction address into components (sido/gungu/dong/jibun/area)
  2. Find matching Naver region codes via hierarchical API
  3. Get all complexes in that dong
  4. Match by lot address (jibun, detailAddress)
  5. Fetch 매매 articles and filter by area proximity
  6. Return price comparison
"""
import re, copy, time
import pandas as pd
import NaverRealestateCrawling as nv

# ----- 헤더/쿠키 (네이버 크롤러에서 재사용) -----
cookies = nv.cookies
headers = nv.headers


def parse_court_address(addr: str) -> dict:
    """법원경매 물건주소를 구조화된 컴포넌트로 파싱"""
    pattern = (
        r'(.+?[시도])\s+'           # 시/도
        r'(.+?[시군구])\s+'         # 시/군/구
        r'(.+?[동가읍면])\s+'       # 읍/면/동
        r'(\d+(?:-\d+)?)\s+'        # 지번 (번지)
        r'(\d+층\d+호)\s+'          # 층/호
        r'\[.*?\s+([\d.]+)㎡\]'     # 전용면적
    )
    m = re.match(pattern, addr.strip())
    if not m:
        return None
    return {
        'sido': m.group(1),       # 서울특별시
        'gungu': m.group(2),      # 성북구
        'dong': m.group(3),       # 정릉동
        'jibun': m.group(4),      # 508-123
        'unit': m.group(5),       # 1층102호
        'floor': m.group(5).split('층')[0],
        'ho': m.group(5).split('층')[1].replace('호', ''),
        'area_m2': float(m.group(6)),  # 67.87
    }


def find_region_codes(sido_name: str, gungu_name: str, dong_name: str) -> dict:
    """행정구역명 → Naver cortarNo 매핑 (sido → gungu → dong)"""
    sido_list = nv.get_sido_info()
    time.sleep(0.5)
    for sido_code in sido_list:
        gungu_list = nv.get_gungu_info(sido_code)
        time.sleep(0.3)
        for gungu_code in gungu_list:
            dong_list = nv.get_dong_info(gungu_code)
            time.sleep(0.3)
            for dong_code in dong_list:
                # dong_code로 복합정보 확인 (첫 번째 단지의 주소로 지역명 유추)
                apt_list = nv.get_apt_list(dong_code)
                if not apt_list:
                    continue
                try:
                    info = nv.get_apt_info_ver2(apt_list[0])
                    addr = info.get('complexDetail', {}).get('address', '')
                    if dong_name in addr and gungu_name in addr and sido_name[:2] in addr:
                        return {
                            'sido_code': sido_code,
                            'gungu_code': gungu_code,
                            'dong_code': dong_code,
                            'sample_addr': addr
                        }
                except:
                    continue
                time.sleep(0.3)
    return None


def find_complex_by_jibun(dong_code: str, target_jibun: str) -> list:
    """동 코드 내에서 지번으로 단지 검색"""
    apt_list = nv.get_apt_list(dong_code)
    matched = []
    for apt_no in apt_list:
        try:
            info = nv.get_apt_info_ver2(apt_no)
            cd = info.get('complexDetail', {})
            naver_addr = cd.get('address', '')
            naver_detail = cd.get('detailAddress', '')
            # 지번 매칭: detailAddress가 지번과 일치하는지 확인
            if target_jibun == naver_detail or target_jibun.startswith(naver_detail):
                matched.append({
                    'complex_no': apt_no,
                    'name': cd.get('complexName'),
                    'address': naver_addr + ' ' + naver_detail,
                    'road_address': cd.get('roadAddressPrefix', '') + ' ' + cd.get('roadAddress', ''),
                    'latitude': cd.get('latitude'),
                    'longitude': cd.get('longitude'),
                    'total_household': cd.get('totalHouseholdCount'),
                    'pyeong_names': cd.get('pyoengNames', ''),
                    'detail': cd
                })
        except:
            continue
        time.sleep(0.3)
    return matched


def get_market_prices(complex_no: str, court_area_m2: float, tolerance: float = 5.0) -> pd.DataFrame:
    """특정 단지의 매매 시세를 조회 (전용면적 기준 매칭)"""
    article_list, type_list, sales_num, content_list = nv.get_article_data(
        complex_no, copy.deepcopy(cookies), headers
    )
    if not content_list:
        return pd.DataFrame()

    df = pd.DataFrame(content_list)
    df['price_numeric'] = df['dealOrWarrantPrc'].apply(nv.clean_price)

    # 매매(A1)만 필터
    df = df[df['tradeTypeCode'] == 'A1'].copy()
    if df.empty:
        return pd.DataFrame()

    # court 면적과 유사한 매물만 필터 (area2 = 전용면적)
    df['area_diff'] = abs(df['area2'].astype(float) - court_area_m2)
    df_near = df[df['area_diff'] <= tolerance].copy()

    if df_near.empty:
        # tolerance 내 매물 없으면 가장 가까운 면적으로
        df_near = df.loc[df['area_diff'].idxmin()].to_frame().T

    result = df_near.groupby('area2').agg(
        매물건수=('price_numeric', 'count'),
        최저매매가=('price_numeric', 'min'),
        최고매매가=('price_numeric', 'max'),
        평균매매가=('price_numeric', 'mean'),
        대표호가=('dealOrWarrantPrc', 'first')
    ).reset_index()
    result.columns = ['전용면적_m2', '매물건수', '최저매매가_만원', '최고매매가_만원', '평균매매가_만원', '대표호가']
    return result


def match_court_to_naver(court_addr: str, court_gameval_amt: str = None) -> dict:
    """법원경매 주소 → 네이버 시세 매칭 전체 파이프라인"""
    result = {'court_address': court_addr, 'success': False}

    # Step 1: 법원 주소 파싱
    parsed = parse_court_address(court_addr)
    if not parsed:
        result['error'] = '주소 파싱 실패'
        return result
    result['parsed'] = parsed

    # Step 2: Naver 지역 코드 찾기
    region = find_region_codes(parsed['sido'], parsed['gungu'], parsed['dong'])
    if not region:
        result['error'] = 'Naver 지역 코드를 찾을 수 없음'
        return result
    result['region'] = region

    # Step 3: 지번으로 단지 매칭
    complexes = find_complex_by_jibun(region['dong_code'], parsed['jibun'])
    if not complexes:
        result['error'] = '지번 매칭 단지 없음'
        return result
    result['matched_complexes'] = complexes

    # Step 4: 첫 매칭 단지의 매매가 조회
    best = complexes[0]
    prices = get_market_prices(best['complex_no'], parsed['area_m2'])
    if prices.empty:
        result['error'] = '매매가 데이터 없음'
        return result
    result['market_prices'] = prices.to_dict('records')
    result['complex_name'] = best['name']
    result['success'] = True

    # Step 5: 감정가와 비교
    if court_gameval_amt:
        try:
            gameval = int(court_gameval_amt.replace(',', ''))
            avg_price = prices['평균매매가_만원'].iloc[0]
            result['gameval_amt'] = gameval
            result['avg_market_price'] = avg_price
            result['diff_ratio'] = round((avg_price - gameval) / gameval * 100, 1)
        except:
            pass

    return result


def match_batch(court_df: pd.DataFrame) -> pd.DataFrame:
    """법원경매 DataFrame 전체를 batch 매칭"""
    rows = []
    for _, row in court_df.iterrows():
        r = match_court_to_naver(row.get('printSt', ''), row.get('gamevalAmt'))
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    # 단일 테스트
    test_addr = "서울특별시 성북구 정릉동 508-123 1층102호 [집합건물 철근콘크리트조 67.87㎡]"
    print(f'=== 매칭 테스트 ===\n{test_addr}\n')
    result = match_court_to_naver(test_addr)
    for k, v in result.items():
        print(f'{k}: {v}')
