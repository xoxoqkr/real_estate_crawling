"""
법원경매 주소 → 네이버 부동산 단지 매칭 테스트
"""
import sys, re
sys.path.insert(0, 'src')
import NaverRealestateCrawling as nv
import pandas as pd

# ======== 1. 법원 주소 파싱 ========
court_address = "서울특별시 성북구 정릉동 508-123 1층102호 [집합건물 철근콘크리트조 67.87㎡]"

# 시도/구군/동/지번/면적 추출
def parse_court_address(addr):
    pattern = r'(.+?[시도])\s+(.+?[시군구])\s+(.+?[동가읍면])\s+(\d+(?:-\d+)?)\s+(\d+층\d+호)\s+\[.*?\s+([\d.]+)㎡\]'
    m = re.match(pattern, addr)
    if m:
        return {
            'sido': m.group(1),
            'gungu': m.group(2),
            'dong': m.group(3),
            'jibun': m.group(4),
            'unit': m.group(5),
            'area_m2': float(m.group(6))
        }
    return None

parsed = parse_court_address(court_address)
print('=== 법원 주소 파싱 ===')
print(parsed)

# ======== 2. 네이버 지역 코드 찾기 ========
# 시도 목록을 가져와서 매칭
sido_list = nv.get_sido_info()
print(f'\n시도 코드 목록: {len(sido_list)}개')
print(f'샘플: {sido_list[:3]}')

# 서울특별시 찾기 (cortarNo로 검색해보기)
# cortarNo = "1100000000" 이 서울인지 확인
target_sido = "서울"
target_gungu = "성북구"
target_dong = "정릉동"

# Naver API의 시도 코드는 앞 2자리가 시도 코드
# cortarNo 포맷: 11SSGGDDDDBB (11=시도, SS=시군구, GGGG=읍면동, DDBB=...)
# 서울은 1100000000
sido_code = "1100000000"  # 서울특별시

# 성북구 찾기
gungu_list = nv.get_gungu_info(sido_code)
print(f'\n서울시 구군 코드: {len(gungu_list)}개')
print(f'샘플: {gungu_list[:5]}')

# Naver는 gungu 코드로 정보를 직접 반환하지 않아서,
# dong 리스트를 가져오기 위해 각 gungu 코드를 순회
found_dong_code = None
found_complexes = []
for gungu_code in gungu_list:
    try:
        dong_list = nv.get_dong_info(gungu_code)
        for dong_code in dong_list:
            apt_list = nv.get_apt_list(dong_code)
            if apt_list:
                # 첫 번째 아파트의 정보를 확인해서 지역명 알아내기
                try:
                    info = nv.get_apt_info_ver2(apt_list[0])
                    addr = info.get('complexDetail', {}).get('address', '')
                    if '정릉' in addr or '성북' in addr:
                        found_dong_code = dong_code
                        found_complexes = apt_list
                        print(f'\n=== 매칭된 동 코드: {dong_code} ===')
                        print(f'아파트 수: {len(apt_list)}')
                        break
                except:
                    pass
        if found_dong_code:
            break
    except:
        continue

# ======== 3. 단지 정보 확인 ========
if found_complexes:
    for apt_no in found_complexes[:5]:
        info = nv.get_apt_info_ver2(apt_no)
        cd = info.get('complexDetail', {})
        print(f'\n--- 단지 {apt_no} ---')
        print(f'  단지명: {cd.get("complexName")}')
        print(f'  address: {cd.get("address")}')
        print(f'  detailAddress: {cd.get("detailAddress")}')
        print(f'  roadAddress: {cd.get("roadAddressPrefix", "")} {cd.get("roadAddress", "")}')
        print(f'  latitude: {cd.get("latitude")}, longitude: {cd.get("longitude")}')
        
        # 평형 정보
        pyeongs = cd.get('pyoengNames', '')
        print(f'  평형: {pyeongs}')
        
        # 지번 매칭 시도: detailAddress가 지번인지 확인
        if cd.get('detailAddress'):
            print(f'  detailAddress(지번후보): {cd["detailAddress"]}')
else:
    print('\n정릉동 단지를 찾지 못했습니다. Naver 주소 체계 확인 필요')
    # 직접 dong_list를 순회해보기
    print('\n--- gungu 1162000000 (성북구) dong 목록 ---')
    dong_list = nv.get_dong_info("1162000000")
    print(f'dong 개수: {len(dong_list)}')
    for dc in dong_list[:10]:
        apt_list = nv.get_apt_list(dc)
        print(f'  dong={dc}, apt_count={len(apt_list)}')

print('\n=== 검증 완료 ===')
