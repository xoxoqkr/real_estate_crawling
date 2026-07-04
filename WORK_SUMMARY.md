# 작업 요약 (2026-07-04)

## 1. 자격증명/토큰 분리

코드에 평문으로 박혀있던 자격증명을 `.env`(gitignore 처리)로 분리했다.

- `.env.example` 추가 (값 없는 템플릿), `.gitignore`에 `.env` 추가
- `requirements.txt`에 `python-dotenv` 추가
- `src/main.py`: 국토부 실거래가 API 키, 스피드옥션 계정, S3 버킷명 → `os.environ`에서 로드
- `src/SpeedAuctionCrawler.py`: `__main__` 테스트 블록의 하드코딩 계정 제거
- `src/NaverRealestateCrawling.py`(레거시): 하드코딩된 네이버 쿠키/Bearer 토큰 → env 변수로 이동

**주의**: 이 네이버 쿠키/토큰은 과거 커밋(`0bfa3d6`)에 평문으로 이미 커밋되어 `origin/main`에 푸시된 상태였다. 이번 작업으로 앞으로의 코드에서는 사라지지만 git 히스토리에는 남아있다. 필요시 히스토리 재작성(`git filter-repo`) 검토 필요.

## 2. 직방(Zigbang) API 정식 통합

`src/ZigbangCrawler.py` 신규 작성. 인증 불필요한 공개 엔드포인트로 동작:

- `search_complex(query)` — 단지명 검색 (`apis.zigbang.com/search`)
- `get_danji_items(danji_id)` — 단지 상세페이지(`zigbang.com/home/apt/danjis/{id}`)에 서버사이드 렌더링된 `__NEXT_DATA__` JSON을 파싱해 매매/전세/월세 매물 목록 추출 (별도 REST API 불필요)
- `compare_court_with_zigbang()` — 법원경매 물건주소에서 단지명/면적을 파싱해 직방 매물과 매칭

**실제 검증**: 힐스테이트상도센트럴파크(동작구 상도동, 118.2㎡) 경매 물건으로 테스트 — 경매 최저가 15.36억 vs 직방 매매 호가 20.5억 (약 -25%) 확인.

## 3. 네이버 부동산 크롤링 방법 발견

`src/NaverRealestateCrawler.py` 신규 작성.

**핵심 발견**: `new.land.naver.com`을 비로그인 상태로 방문하면 서버가 응답 HTML(`window.App = {...}`)에 **게스트용 Bearer 토큰을 직접 심어준다** (`isLogin: false`, 유효기간 약 3시간, 특정 계정과 무관). 이 토큰으로 `/api/search`, `/api/complexes/{no}`, `/api/articles/complex/{no}`가 모두 정상 동작함을 확인했다.

기존 레거시 방식(브라우저에서 수동으로 복사한 쿠키/토큰을 코드에 하드코딩 → 몇 시간 뒤 만료)의 근본 문제를 해결한다. 로그인도 계정도 필요 없다.

- `search_complex(keyword)`, `get_complex_detail(complex_no)`, `get_articles(complex_no, trade_type)`
- 토큰 자동 발급/만료 시 자동 재발급, 401 응답 시 1회 재시도
- `compare_court_with_naver()` — `ZigbangCrawler.py`의 주소 파싱 유틸 재사용

**실제 검증**: 동일 물건 기준 매매 145건/전세 13건/월세 40건 조회 성공. 118㎡(105동) 매매 호가가 직방 값(20.5억)과 정확히 일치해 교차검증됨. 전세는 직방에 없던 데이터를 네이버에서 확보(33평형 기준 9.5억).

**참고**: 네이버 이용약관은 자동화 수집을 금지하며, 짧은 시간에 다량 요청 시 IP 제한 가능성을 확인함(조사 중 실제로 한 번 발생). 요청 간 sleep 유지, 과도하게 짧은 주기 실행 지양 권장.

## 4. AWS Fargate 배포 검증

- `.dockerignore` 신규 추가 — `.env`, `awscliv2.zip`(67MB), 실험/디버그 스크립트가 Docker 이미지에 포함되지 않도록 함 (기존에는 `.dockerignore`가 없어 `docker build` 시 `.env`가 이미지에 그대로 박힐 위험이 있었음)
- `src/main.py`: `SAVE_DIR`을 `~/Downloads/`(컨테이너에 존재하지 않음) 하드코딩에서 `SAVE_DIR` 환경변수 + `os.makedirs`로 컨테이너 호환되게 수정
- `Dockerfile`: apt 패키지 목록에서 현재 Debian(trixie)에 존재하지 않는 obsolete 패키지(`software-properties-common`, `libgconf-2-4`, `libappindicator1`, `libayatana-indicator7`) 제거 — 이건 이번 작업과 무관하게 base 이미지 드리프트로 이미 깨져있던 버그
- 로컬 `docker build` 실전 검증 완료 (빌드 성공, 이미지 내 `.env`/민감 파일 미포함 확인)

**아직 다루지 않은 것** (AWS 계정 정보가 필요해 보류): `fargate-task.json`에 `taskRoleArn`(S3 업로드 권한) 부재, 필수 환경변수/Secrets Manager 미연결, 리전(`eu-north-1`)이 한국 사이트 크롤링 대상과 지리적으로 맞지 않아 `ap-northeast-2` 전환 검토 필요.

## 정리 필요 항목 (미결정)

- `src/CourtNaverMatcher.py`(레거시, 네이버 API 매칭)를 새 `NaverRealestateCrawler.py`로 교체할지, `main.py` 파이프라인에 Zigbang/Naver를 5단계로 정식 추가할지 결정 필요
- `src/test_*.py`, `discover_*.py`, `refresh_naver_token*.py` 등 ~40개 실험 스크립트 정리 여부 (이 중 다수가 네이버 쿠키/토큰을 하드코딩하고 있어 git에 커밋하지 않음)
