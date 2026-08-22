# NOTICE — 다음 에이전트를 위한 안내

이 문서는 `real_estate_crawling` 저장소를 처음 맡는 에이전트가 빠르게 맥락을 잡을 수 있도록
현재 코드 상태 + 과거 작업 이력(`WORK_SUMMARY.md`, 2026-07-04)을 종합해 정리한 것이다.
작업 전 반드시 `WORK_SUMMARY.md`도 함께 읽을 것 — 이 문서는 그 이후 상태 변화까지 반영한 최신 스냅샷이다.

## 1. 프로젝트 목적

법원경매 물건을 크롤링해서, (1) SpeedAuction 부가정보와 cross-check하고 (2) 국토교통부
실거래가와 매칭해 "경매 최저가 vs 실제 시세"를 비교하는 파이프라인. 결과는 CSV로 로컬 저장 +
S3 업로드. AWS Fargate(ECS)에서 정기 실행하는 것을 목표로 함.

## 2. 메인 파이프라인 (`src/main.py`)

**2026-08-22 구조 변경**: 원래는 법원경매(Selenium) 크롤링이 1단계이자 실거래가 매칭의
기준 데이터였는데, 다음 두 가지를 실측으로 확인한 뒤 **마이옥션 검색을 기준 데이터로,
법원경매/SpeedAuction은 사건번호 기준 보조정보 병합으로** 구조를 바꿨다:
- 마이옥션 3사 교차검증 결과 마이옥션이 법원경매 사건을 이미 다 포함하고 있어(테스트한
  246건 전부 일치) 별도로 두 번 수집할 필요가 없었음
- 마이옥션은 검색 시점에 물건종류(아파트 등)를 바로 지정할 수 있어, 아파트 실거래만
  제공하는 국토부 API와 궁합이 좋음. 반면 법원경매 크롤링(Step 3, 구 Step 1)은 용도
  필터를 지원하지 않고 Selenium이라 느리고 사이트 변화에 취약함(§9 페이지네이션 버그 참고)

`python src/main.py` 실행 시 5단계로 동작 (엔트리포인트는 이것 하나이며, `Dockerfile`의
`CMD`도 이걸 실행함):

1. **마이옥션 검색** (`MyAuctionCrawler.py`, `crawl_myauction_data()`) — 파이프라인의
   기준 데이터. 로그인 후 `/auction/search_list.php`(회원 전용, 전체 DB)를 물건종류
   필터(기본 아파트)로 조회. `MY_AUCTION_ID`/`PW` 미설정 또는 로그인 실패 시 로그인
   불필요한 `/auction/recommend.php`(추천물건 풀, 좁은 커버리지)로 자동 대체.
2. **국토부 실거래가 매칭** (`CourtTradeMatcher.py` → `AptTradeAPI.py`) — **법원경매/
   SpeedAuction을 기다리지 않고 1단계(마이옥션) 결과를 바로 매칭**한다. 마이옥션 주소
   (`my_주소`)엔 법원경매 주소처럼 `[... NN.NN㎡]` 표기가 없어서, 기존 주소 파싱 로직
   (`parse_court_address()`)이 그대로는 못 씀 — `my_건물면적_평`을 ㎡로 환산해 같은
   표기를 문자열에 덧붙여서 기존 파싱 로직을 재사용하도록 만들었다(`run_trade_matching()`
   내부 `_with_area_bracket()`). 물건주소 파싱(시군구/동/면적) → 법정동코드 변환 →
   국토부 Open API 조회 → 면적 기준 매칭 → 감정가 대비 시세 diff 계산.
3. **법원경매 크롤링(보조)** (`CourtRealestateCrawling.py`) — Selenium으로
   `courtauction.go.kr` 크롤링. `--skip-court`로 건너뛸 수 있음(느림 + Selenium
   의존성). 담당계/유찰횟수/비고 등 마이옥션에 없는 필드 보강용으로만 쓰임 — 매칭
   결과 자체(2단계)에는 영향 없음.
4. **SpeedAuction 크롤링(보조)** (`SpeedAuctionCrawler.py`) — 조회수/특수표시 보강용.
   `--skip-speed`로 건너뛸 수 있음. **현재 이 sandbox에서는 접속 자체가 안 됨 → §8 참고**
   (실패해도 파이프라인은 계속 진행됨).
5. **보조정보 병합 + 최종 저장** (`enrich_with_sources()`) — 사건번호 기준으로 3·4단계
   결과를 2단계 매칭 결과에 좌측 병합(left merge). 법원경매 원본 `사건번호` 컬럼은
   법원명이 앞에 붙고(예: `"서울중앙지방법원 2008타경25092 2015타경19958 (중복)"`)
   병합된 사건번호가 여러 개 이어붙기도 해서, 마이옥션 형식("YYYY타경NNNNN", 5자리
   zero-pad, 법원명 없음)과 그대로는 매칭이 안 됨 — `_normalize_case_no()`로 정규화한
   뒤 병합함 (SpeedAuction의 `speed_사건번호_정규`는 처음부터 같은 5자리 zero-pad
   형식이라 정규화 불필요). 최종 결과를 로컬 CSV + S3(`AWSFunction.save_to_s3`)에 저장.

`SAVE_DIR` 환경변수(기본 `~/Downloads/`, 컨테이너에는 없는 경로이므로 실제 배포 시 반드시
설정 필요)에 각 단계 산출물이 CSV로 쌓인다.

**물건종류(용도) 필터 — 기본값은 "아파트"만**: 국토부 실거래가 Open API
(`RTMSDataSvcAptTrade`)가 애초에 아파트 실거래만 제공하기 때문 — 다세대/오피스텔/상가
등 다른 용도를 넣으면 2단계 매칭이 "성공"으로 나와도 실제로는 근처의 **다른 아파트
단지 시세**가 잘못 매칭된 것으로, 신뢰할 수 없다 (2026-08-22 마이옥션 3사 교차검증
작업에서 246건 중 159건이 이런 식으로 "매칭 성공"했지만 아파트가 아닌 146건은 사실상
의미 없는 결과였음을 실측으로 확인함).

CLI에서 물건종류/페이지수/보조단계 스킵 여부를 조절할 수 있다:
```bash
python src/main.py                          # 기본값: 아파트만
python src/main.py --usage 아파트 오피스텔      # 여러 용도 동시 지정 가능
python src/main.py --usage 전체               # 용도 필터 없이 전체 조회 (2단계 정확도 낮아짐 주의)
python src/main.py --max-pages 10            # 마이옥션/법원경매/SpeedAuction 각 단계 페이지 수
python src/main.py --skip-court --skip-speed # 보조 단계 건너뛰고 마이옥션+국토부 매칭만 빠르게
```
`--usage` 값은 `SpeedAuctionCrawler`의 대분류 용도코드(주거용/업무상업/공업/토지,
`USAGE_TO_SPEED_CODE` 매핑)로도 함께 변환되어 SpeedAuction 크롤링에도 적용됨 — 단,
SpeedAuction은 마이옥션만큼 세분화된 용도 구분이 없어 대분류 단위로만 맞출 수 있음.
**법원경매 크롤링(Step 3) 자체는 용도 필터를 지원하지 않음** — `courtauction.go.kr`
검색 폼에 용도 필터가 있긴 하지만 `navigate_to_search_page()`가 아직 이를 노출하지
않음. 다만 이제 법원경매는 보조정보 병합용일 뿐이라 실질적인 영향은 크지 않음(매칭
결과는 이미 마이옥션 기준으로 완성돼 있으므로).

## 3. 모듈 지도 (`src/`)

**파이프라인에 실제로 물려있는 것:**
- `main.py` — 통합 엔트리포인트 (위 5단계)
- `CourtRealestateCrawling.py` — 법원경매 Selenium 크롤러
- `SpeedAuctionCrawler.py` — SpeedAuction 로그인/크롤링/cross-check
- `MyAuctionCrawler.py` — 마이옥션(my-auction.co.kr) 경매 물건 목록 크롤러 (2026-08-22
  작성, 실 계정으로 로그인·검색 전체 플로우 검증 완료 후 `main.py`에 통합). 회원 전용
  `/auction/search_list.php`에 로그인 후 `/auction/search.php` 폼의 전체 필드셋을 그대로
  GET으로 보내면 사이트 전체 경매 DB를 대상으로 한 검색 결과가 반환됨을 확인했다(예:
  서울+아파트 필터 시 248건/13페이지). 필드 일부만 보내면 `alert('error2')`로 거부되므로
  `search_list()`는 전체 필드셋을 채워서 보낸다. 로그인 없이도 같은 파라미터를 받는
  `/auction/recommend.php`(추천경매물건, "추천물건" 풀 ~100~130건만 대상)를 대체 경로로
  남겨뒀다 — `MY_AUCTION_ID`/`PW` 미설정이거나 로그인 실패 시 자동으로 이 경로를 씀.
  로그인은 `/member/login_handle.php`에 표준 base64로 인코딩한 `id`/`pwd`를 POST하는
  방식이며, `Referer` 헤더 없이 호출하면 간헐적으로 `alert('error2')`가 나는 것을 확인해
  헤더를 명시적으로 추가했다. 계정 정보는 `.env`의 `MY_AUCTION_ID`/`MY_AUCTION_PW`.
- `AptTradeAPI.py` — 국토부 실거래가 API 래퍼 + 법정동코드 매핑(서울 25개구 + 일부 경기/인천)
- `CourtTradeMatcher.py` — 법원경매 주소 파싱 + 실거래가 매칭 오케스트레이션
  (docstring에 "`CourtNaverMatcher.py`를 대체(네이버 API 차단으로 인해)"라고 명시되어 있음)
- `AWSFunction.py` — S3 업로드
- `RunFargate.py` — ECS Fargate 태스크를 원격에서 실행 트리거하는 별도 스크립트
  (main.py 파이프라인과는 무관, 로컬에서 `boto3.client("ecs").run_task()`만 호출)

**작성되었지만 아직 `main.py`에 통합 안 된 것** (2026-07-04 작업분):
- `ZigbangCrawler.py` — 직방 공개 엔드포인트로 단지 매매/전세/월세 매물 조회, 인증 불필요.
  `compare_court_with_zigbang()`으로 법원경매 물건과 매칭 가능. 실제 사례로 검증됨.
- `NaverRealestateCrawler.py` — `new.land.naver.com` 비로그인 방문 시 서버가 응답 HTML에
  심어주는 게스트용 Bearer 토큰(유효기간 ~3시간)을 자동 추출해서 사용. 로그인/쿠키 하드코딩
  불필요 — 레거시 방식의 근본 문제(토큰 만료)를 해결한 버전. `compare_court_with_naver()`
  제공. **네이버 이용약관상 자동화 수집 금지, 과도한 요청 시 IP 차단 가능성 있음 확인됨(실제
  발생 이력 있음) → 요청 간 sleep 유지 필수.**

**레거시/사용 안 함 (참고용으로만 남아있음, 삭제 여부 미결정):**
- `CourtNaverMatcher.py` — 네이버 API 기반 매칭, 위 사유로 `CourtTradeMatcher.py`가 대체함
- `NaverRealestateCrawling.py` — 더 오래된 네이버 크롤러, 브라우저에서 수동 복사한
  쿠키/Bearer 토큰을 코드에 박아두는 구조라 몇 시간 뒤 만료되는 근본적 결함이 있었음.
  `NaverRealestateCrawler.py`가 이 문제를 해결한 신버전
- `src/app.py` — `main.py` 이전의 구버전 엔트리포인트. 법원경매 1단계만 실행하고 S3 저장.
  `save_dir`이 `'C:/Users/xoxoq/Downloads/'`로 하드코딩된 Windows 경로라 Linux/컨테이너에서
  그대로 실행 불가. **사실상 죽은 코드로 보임 — 삭제 검토 대상.**
- `src/temp/*.py` — 초기 프로토타입 스크립트 5개
- `src/test_*.py`, `src/discover_*.py`, `src/check_mobile*.py`, `src/refresh_naver_token*.py`,
  `src/analyze_js.py` 등 약 40개 — 네이버/직방 API 리버스엔지니어링 과정에서 만든 1회성
  실험 스크립트. **전부 git에 커밋되어 추적 중.** 이 중 다수가 네이버 쿠키/토큰을 코드에
  하드코딩하고 있을 수 있으니, 열람 시 민감정보 포함 여부를 먼저 확인할 것.

## 4. 환경변수 (`.env`, `.env.example` 참고)

`load_dotenv()`가 `main.py`에서 로드함. 필요한 키:
- `MOLIT_API_KEY` — 국토부 실거래가 API 서비스키 (data.go.kr)
- `SPEED_AUCTION_ID` / `SPEED_AUCTION_PW` — SpeedAuction 로그인 계정
- `MY_AUCTION_ID` / `MY_AUCTION_PW` — 마이옥션(my-auction.co.kr) 로그인 계정. 실 계정으로
  로그인 검증 완료(2026-08-22). 미설정 시 `MyAuctionCrawler`는 로그인 없이 동작하는
  `/auction/recommend.php`(추천물건 풀, 좁은 커버리지)로 자동 대체됨 — 파이프라인이
  죽지는 않지만 커버리지가 크게 줄어드니 유의할 것.
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` / `AWS_S3_BUCKET_NAME` — S3 업로드용
- `NAVER_COOKIES_JSON` / `NAVER_BEARER_TOKEN` — 레거시 `CourtNaverMatcher.py`/
  `NaverRealestateCrawling.py`에서만 쓰임 (신규 `NaverRealestateCrawler.py`는 이 값들 불필요)
- `SAVE_DIR` — 미설정 시 `~/Downloads/`로 fallback (컨테이너에서는 반드시 명시적으로 설정할 것)

`.env`는 gitignore 처리되어 있고 실제 값이 로컬에 존재함 (`.env` 파일 자체는 이 대화에서
내용을 노출하지 않았음 — 필요 시 직접 확인).

## 5. AWS 배포 — EventBridge 주간 스케줄 + 이미지 재빌드까지 완료 (2026-08-22)

이전에 여기 적혀 있던 "RunFargate.py와 fargate-task.json 리전 불일치" 문제는 실제
AWS 계정을 열어보니 이미 해소되어 있었다(`ap-northeast-2`에 클러스터/ECR/태스크 정의가
전부 정상 존재 — 로컬 `fargate-task.json` 파일만 옛날 `eu-north-1`을 가리키는 채로
방치되어 실제 상태와 안 맞았던 것). 파일은 이번에 실제 등록된 태스크 정의 내용으로
갱신해뒀다.

**이번에 한 작업 — 매주 월요일 새벽 3시(KST) 자동 실행 설정**:
- **Secrets Manager**: `real-estate-crawling/env` (ARN:
  `arn:aws:secretsmanager:ap-northeast-2:730335187691:secret:real-estate-crawling/env-urpo8O`)
  — `.env`의 민감값(API 키/사이트 로그인 비밀번호/AWS 키 등)을 여기 저장. 태스크 정의에
  평문으로 넣지 않고 여기서 안전하게 참조하도록 함(사용자가 보안을 이유로 이 방식을 선택함).
- **IAM**: `ecsTaskExecutionRole`에 위 secret을 읽을 수 있는 인라인 정책
  (`RealEstateCrawlingSecretsAccess`) 추가. EventBridge가 ECS 태스크를 실행할 수 있도록
  새 역할 `real-estate-crawling-eventbridge-role`(신뢰 주체: `events.amazonaws.com`)을
  만들고 `ecs:RunTask` + `iam:PassRole`(ecsTaskExecutionRole 대상) 인라인 정책
  (`RunECSTaskPolicy`)을 붙임.
- **ECS 태스크 정의**: `real_estate_crawling:2` (revision 1은 `environment: []`로
  아무 환경변수도 없어서 실행하면 즉시 `KeyError`로 죽는 상태였음 — main.py가
  `MOLIT_API_KEY`/`SPEED_AUCTION_ID`/`SPEED_AUCTION_PW`를 `os.environ[...]`로 필수
  요구하기 때문). revision 2는 위 Secrets Manager를 `secrets`로 참조하고,
  컨테이너 `command`를 `["python", "src/main.py", "--skip-court", "--skip-speed"]`로
  오버라이드해서 마이옥션+국토부 매칭만 도는 빠른 경로로 고정함(사용자 선택).
- **EventBridge**: 규칙 `real-estate-crawling-weekly`, 스케줄
  `cron(0 18 ? * SUN *)`(UTC 기준 — 월요일 03:00 KST = 일요일 18:00 UTC), 타겟은
  `fargate-cluster`에서 `real_estate_crawling:2`를 FARGATE로 실행 (서브넷
  `subnet-0ff952eb6ed7ef300`, 보안그룹 `sg-0710391540fef28fc`, 기존 `RunFargate.py`와
  동일한 네트워크 설정 재사용).

**이미지 재빌드/푸시 — AWS CodeBuild로 원격 빌드 완료 (2026-08-22)**: 발견 당시 ECR의
`latest` 이미지는 2026-08-18에 푸시된 것이라 그날 이후 작업(마이옥션 크롤러, 새
`main.py` 구조, 법원경매 페이지네이션 수정 등)이 전혀 반영되어 있지 않았다 — 실제로
새 태스크 정의로 테스트 실행했더니 `--skip-court --skip-speed`를 줬는데도 **죽은 코드인
`src/app.py`(§3 "레거시/사용 안 함" 참고)가 실행되는 로그**("크롤링 종료",
`court_data/raw/...` S3 경로)가 찍혀서 알아챔. 이 sandbox엔 Docker가 없어서 로컬
빌드가 불가능했고, 사용자가 "AWS CodeBuild로 원격 빌드"를 선택해서 다음을 새로 만들었다:
- S3 버킷 `real-estate-crawling-codebuild-730335187691`(ap-northeast-2) — CodeBuild
  소스용. **주의**: 기존 `odtest01` 버킷은 `eu-north-1`에 있어서 `ap-northeast-2`의
  CodeBuild가 소스를 못 읽음(`BucketRegionError`로 실패 — 리전이 다른 S3 버킷을
  CodeBuild 소스로 못 쓰는 것을 실측으로 확인) — 그래서 별도 버킷을 만듦.
- IAM 역할 `real-estate-crawling-codebuild-role` — CloudWatch Logs 쓰기(로그 그룹
  `/aws/codebuild/real-estate-crawling-image-build*` — 처음에 `/codebuild/...`로
  잘못 지정해서 `AccessDenied`로 한 번 실패했음, CodeBuild 기본 로그 그룹 경로는
  `/aws/codebuild/`로 시작함), S3 소스 버킷 읽기, ECR push/pull 권한.
- CodeBuild 프로젝트 `real-estate-crawling-image-build` — 소스는 S3 zip
  (`.venv`/`.git`/`aws/`/`awscliv2.zip`/실험 스크립트 등 제외하고 압축), 환경은
  `privilegedMode: true`(도커 빌드에 필수), buildspec은 인라인으로 ECR 로그인 →
  `docker build` → `docker push` 3단계.
- 프로젝트/소스 zip은 재사용 가능하게 남겨둠 — 다음에 코드 변경 후 다시 이미지를
  갱신하려면: 최신 소스로 zip을 새로 만들어 같은 S3 키에 덮어쓰고
  `aws codebuild start-build --project-name real-estate-crawling-image-build --region ap-northeast-2`
  만 실행하면 됨 (프로젝트 재생성 불필요).

**실제 검증 완료**: 새 이미지 푸시 후 `real_estate_crawling:2`로 수동 `run-task` 실행 →
CloudWatch 로그에 "[1/5] 마이옥션 검색"부터 "[5/5]"까지, 처리 이력 필터링(§6)까지 전부
새 코드대로 정상 동작하는 것을 실제 로그로 확인함(서울 아파트 200건 검색, 국토부 매칭
171건 성공, S3 저장 성공, `exitCode: 0`). 이 실행 결과로 `court_data/seen_cases.json`에
186건이 실제로 기록되었으므로, 다음 주 첫 스케줄 실행부터는 이미 이 186건을 제외한
신규 매물만 처리한다.

CI/CD(예: GitHub Actions로 push 시 자동 빌드/푸시)는 여전히 없음 — 코드가 바뀔 때마다
위 CodeBuild 프로젝트를 수동으로 다시 트리거해야 한다는 뜻. 필요하면 다음에 GitHub
연동 자동 트리거 설정 검토.

이전에 지적됐던 `taskRoleArn`(S3 업로드용) 부재는 여전히 그대로지만, 실제로는 문제가
안 됨 — `AWSFunction.save_to_s3()`가 IAM 태스크 역할이 아니라 `AWS_ACCESS_KEY_ID`/
`AWS_SECRET_ACCESS_KEY` 환경변수(이번에 Secrets Manager로 주입)로 직접 인증하기
때문. 다만 이는 컨테이너 안에 사실상 루트 계정 액세스 키를 넣는 셈이라 보안상 이상적이지
않음 — 장기적으로는 `taskRoleArn`에 S3 권한을 주고 `save_to_s3()`가 boto3 기본
자격증명(IAM 역할)을 쓰도록 바꿔서 AWS 키 자체를 컨테이너에 넣지 않는 방향이 더 나음
(이번엔 범위상 하지 않음).

## 6. 주간 반복 실행 대비 — 중복 방지 + 타임아웃 (2026-08-22)

EventBridge로 매주 자동 실행하게 되면서 다음 두 가지를 `main.py`에 추가했다:

- **처리 이력 기반 중복 방지**: `AWSFunction.py`에 `load_seen_cases()`/`save_seen_cases()`
  추가 — S3 `court_data/seen_cases.json`에 지금까지 처리한 마이옥션 사건번호 집합을
  누적 저장한다. `main()`은 마이옥션 검색 직후, 국토부 매칭에 넘기기 전에 이미 처리한
  사건번호를 걸러낸다(기본 동작, `skip_seen=True`). **주의**: 완전히 건너뛰는 방식이라,
  이미 처리한 매물이 그 사이 유찰되어 최저가가 바뀌어도 반영되지 않는다 — 가격 변동까지
  추적하려면 `--no-skip-seen`으로 꺼야 함. 이번 실행에서만 이력을 무시하고 전체
  재처리하려면 `--reset-seen`(이력 자체는 이번 결과로 계속 갱신됨). 이력을 완전히
  지우려면 S3에서 `court_data/seen_cases.json`을 직접 삭제.
- **타임아웃 워치독**: `_start_timeout_watchdog()` — 데몬 스레드로 구현, 지정 시간(분,
  기본 30, `--timeout-minutes`로 조절)을 넘기면 `os._exit(1)`로 프로세스를 강제
  종료한다. `signal.alarm`을 안 쓴 이유는 Windows에서 지원 안 되기 때문(레거시 코드에
  `C:/Users/xoxoq/...` 로컬 개발 흔적이 있어 플랫폼 무관하게 구현). 실측으로 (a) 타임아웃
  초과 시 강제 종료되는 것, (b) 정상 완료 시 `watchdog.cancel()`로 타이머가 취소돼
  안전한 것 둘 다 확인했다. 과거 §9에서 chromedriver가 죽었을 때 스크립트가 무한
  대기했던 사례가 실제로 있었기 때문에 추가함.

두 기능 모두 기본값이 켜져 있어서 별도 설정 없이 `python src/main.py`만 돌려도 적용됨.
ECS 태스크 정의(`real_estate_crawling:2`)의 커맨드는 이미 `--skip-court --skip-speed`만
지정하고 있어 그대로 두 기능(30분 타임아웃, 이력 기반 중복 방지)이 기본값으로 적용된다 —
**단, ECR 이미지가 아직 이 코드 반영 전이라(§5 참고) 재빌드/재푸시 전에는 무의미함.**

## 7. 저장소 위생 문제 (정리 후보)

git에 커밋되어 있는데 프로젝트 코드가 아닌 파일들:
- **`awscliv2.zip` (약 67MB)** — AWS CLI v2 설치 파일 자체가 통째로 git에 커밋되어 있음.
  `.dockerignore`에는 제외되어 있어 Docker 이미지에는 안 들어가지만, 저장소 자체를 심각하게
  무겁게 만들고 있음. 이 zip을 풀어놓은 `aws/` 디렉토리(`aws/install`, `aws/README.md`,
  `aws/THIRD_PARTY_LICENSES`)도 프로젝트 코드가 아니라 AWS CLI 설치 산출물임 — 실수로
  커밋된 것으로 보임.
- `docker_build.log` (약 140KB) — 로컬 docker build 로그가 그대로 커밋되어 있음.
- `speed_*.html` (8개, 수백KB) — SpeedAuction/직방 리버스엔지니어링 과정에서 저장한
  디버그용 HTML 덤프. 루트 디렉토리에 그대로 위치.
- 위 파일들 모두 `git rm` + `.gitignore` 추가 검토 대상. (필요시 `git filter-repo`로 히스토리
  자체에서 제거하는 것도 고려 가능하나, 이건 파괴적 작업이므로 사용자 승인 필요.)
- 참고: 과거 커밋(`0bfa3d6`)에 네이버 쿠키/Bearer 토큰이 평문으로 커밋되어 `origin/main`에
  푸시된 이력이 있음 — 이후 코드에서는 제거됐지만 git 히스토리에는 남아있음. 히스토리
  재작성 필요 여부는 아직 미결정.

## 8. SpeedAuction 접속 불가 (2026-08-22 확인)

이 개발 환경(sandbox)에서 `SpeedAuctionCrawler.py`를 실제로 실행해본 결과, **로그인 이전
TCP 연결 단계에서부터 막힘**을 확인했다.

- `new.speedauction.co.kr` (IP `211.233.62.4`) — 포트 443, 80 모두 연결 시도 시 응답 없이
  타임아웃 (RST/거부가 아니라 완전 블랙홀). `requests.get(BASE)` 단계, 즉
  `SpeedAuctionCrawler.login()`의 첫 줄에서부터 걸림.
- 같은 sandbox에서 비교 테스트한 결과:
  - `courtauction.go.kr`(이 프로젝트가 크롤링하는 법원경매 사이트) — 정상 연결
  - `apis.data.go.kr`(국토부 실거래가 API) — 정상 연결
  - `naver.com`, `google.com` — 정상 연결
  - → sandbox 자체의 아웃바운드 네트워크가 전반적으로 막힌 것이 **아니고**, SpeedAuction
    서버만 특정해서 응답이 없는 상태

**결론이 아니라 관찰 사실로 남겨둠**: 이 증상만으로는 (a) SpeedAuction이 이 sandbox의
아웃바운드 IP 대역을 차단한 것인지, (b) SpeedAuction 서버/네트워크 자체가 그 시점에
장애·다운 상태였는지 구분할 수 없다 (둘 다 TCP 레벨에서는 동일하게 "완전 무응답"으로
나타남). 확인하려면 다른 네트워크(사용자 로컬 PC, 실제 Fargate 배포 환경 등)에서 동일하게
`python src/SpeedAuctionCrawler.py`를 실행해 같은 증상이 재현되는지 대조해볼 것.

재현 방법:
```bash
curl -v -m 10 https://new.speedauction.co.kr/    # 다른 사이트와 비교 시 타임아웃 여부 확인
.venv/bin/python src/SpeedAuctionCrawler.py       # .env에 SPEED_AUCTION_ID/PW 필요
```

## 9. 법원경매 크롤러 페이지네이션 버그 — 발견 및 수정 완료 (2026-08-22)

`CourtRealestateCrawling.py`의 `paginate_and_extract()`가 **몇 페이지를 넘기든 항상 같은
사건 하나만 반복 수집**하는 심각한 버그를 발견해서 수정했다. 마이옥션 3사 교차검증 작업
중 우연히 발견함 (자세한 경위: 법원경매 15페이지를 긁었는데 전부 `2008타경25092`
사건 하나만 나왔음).

**원인**: `click_button()`이 다음 페이지 버튼을 네이티브 `button.click()`(실패 시
ActionChains)으로 클릭했는데, 이 사이트(w2ui 계열 그리드)에서는 이 방식이 **예외 없이
"성공"하면서도 실제로는 사이트의 페이지 전환 핸들러를 트리거하지 못했다** — 버튼의
선택 상태(class)는 `w2pageList_label_selected`로 정상적으로 바뀌는데 그리드 데이터는
그대로였음. `driver.execute_script("arguments[0].click();", button)`(JS로 직접 클릭)만
안정적으로 실제 페이지 전환을 트리거함을 실측으로 확인했다.

추가로 페이지 갱신 감지 로직도 부실했다: 기존 코드는 클릭 후
`presence_of_element_located((By.CLASS_NAME, "grid_body_row"))`만 기다렸는데, 이 그리드는
페이지 전환 시 `<tr>` DOM 노드를 새로 만들지 않고 **기존 노드를 재사용해 셀 텍스트만
갱신**하는 것으로 보인다 (`staleness_of()`로 감지를 시도해도 노드가 재사용되므로
staleness 자체가 발생하지 않아 매번 타임아웃남 — 실측으로 확인). 그래서 클릭이 정상
작동하더라도 이 대기 방식으로는 새 데이터가 실제로 그려지기 전에 추출해버릴 위험이 있었음.

**수정 내용** (`src/CourtRealestateCrawling.py`):
1. `click_button()` — JS `execute_script` 클릭을 우선 시도하도록 순서 변경 (네이티브
   클릭/ActionChains는 fallback으로만 남김)
2. `paginate_and_extract()` — DOM staleness 대신, 클릭 전후로 **(사건번호, 물건번호)
   조합의 지문(fingerprint)이 실제로 바뀌었는지**를 재추출해서 직접 확인하는 방식으로
   교체 (최대 5회 재시도, 3초 간격). 이 프레임워크가 DOM 노드를 재사용하는지 여부와
   무관하게 "화면에 실제로 보이는 데이터가 바뀌었는가"를 직접 검증하므로 더 신뢰할 수 있음.
3. `setup_webdriver()` — chromedriver 프로세스가 죽는 등 비정상 상황에서 selenium의 HTTP
   클라이언트가 무한 대기(hang)하는 것을 방지하기 위해
   `driver.command_executor.set_timeout(30)` 추가. (크롤링 디버깅 중 실제로 chrome 프로세스가
   죽은 뒤 스크립트가 응답 없이 멈추는 것을 겪었음 — `kill -9`로 강제 종료해야 했음.)

**검증**: 수정 후 서울중앙지방법원 6페이지 크롤링 시 사건번호 25개가 서로 다르게
정상 수집됨을 확인했다 (수정 전에는 6페이지 내내 사건번호 1개만 반복). `main.py`의
`crawl_court_data()` → `process_court_data()` 전체 흐름으로도 재검증 완료 — 주소/감정가가
사건별로 올바르게 분리되어 나옴. `process_court_data()` 자체는 버그가 없었음 (별도
단위 테스트로 확인) — 입력이 전부 같은 사건이라 1행으로 병합된 것이 정상 동작이었을 뿐,
문제는 순전히 페이지네이션 쪽이었음.

이 버그가 언제부터 있었는지(사이트 개편 때문인지, 원래부터 안 됐는지)는 알 수 없음 —
git blame 상 `paginate_and_extract`는 초기 커밋부터 거의 그대로였음.

## 10. 국토부 실거래가 매칭 성능 개선 (2026-08-22)

마이옥션 3사 교차검증(법원경매 × 마이옥션 × 국토부실거래가)을 246건 규모로 돌리던 중,
`CourtTradeMatcher.match_batch()`(main.py Step 5가 실제로 쓰는 배치 매칭 함수)가
**246건 처리에 25분 넘게 걸리는** 것을 발견해서 개선했다.

**원인 2가지** (`src/AptTradeAPI.py`, `src/CourtTradeMatcher.py`):
1. 국토부 API를 페이지당 100건(`numOfRows` 기본값)으로만 호출하고 있었는데, 강남구·서초구
   같은 거래량 많은 구는 한 달에 300~500건씩 나와서 사건 하나당(최대 6~12개월 × 여러
   페이지) API 호출이 수십 번씩 발생했음. 실측 결과 `numOfRows=1000`으로 올려도 API가
   정상적으로 응답하며(강남구 한 달 222건을 1회 호출로 전부 받음), 한 달에 1000건을
   넘는 경우는 사실상 없어 대부분 월당 API 호출이 1회로 줄어듦.
2. `CourtTradeMatcher.py`의 `get_recent_trades()`가 `AptTradeAPI.py`의
   `get_trade_prices()`와 **완전히 동일한 로직을 독립적으로 중복 구현**하고 있었음.
   `match_batch()`로 여러 사건(흔히 같은 구/동에 몰려있음)을 배치 처리할 때도 매번
   처음부터 다시 API를 호출해, 같은 구의 같은 달 데이터를 사건 수만큼 반복 조회하고
   있었음.

**수정 내용**:
- `AptTradeAPI.py`의 `fetch_apt_trade()` 호출을 전부 `numOfRows=1000`으로 상향
  (`get_trade_prices()` 내부)
- `get_trade_prices()`에 `(법정동코드, 계약년월)` 단위 프로세스 내 메모리 캐시
  (`_TRADE_CACHE`, `clear_trade_cache()`로 초기화 가능) 추가 — 같은 구를 여러 번
  조회해도 실제 API 호출은 한 번만 발생
- `CourtTradeMatcher.get_recent_trades()`의 중복 구현을 제거하고
  `AptTradeAPI.get_trade_prices()`를 호출하도록 변경 — `match_batch()`가 자동으로
  위 두 개선 효과를 받음

**검증**: 동일한 246건 매칭을 수정 전/후로 비교 — **25분+ → 135.9초(2.3분)**로 단축,
성공 건수(159/246)는 완전히 동일해 결과 정확성도 유지됨을 확인했다.

주의: `_TRADE_CACHE`는 프로세스 메모리에만 있는 캐시라 스크립트를 재실행하면 초기화된다
(별도 캐시 무효화 로직 없음 — 같은 프로세스 내에서 구 데이터가 몇 시간 안에 바뀔 일은
없다고 보고 단순하게 유지함). 장시간 떠 있는 프로세스(예: 서버)에서 이 모듈을 쓴다면
그 점을 고려할 것.

## 11. 결정이 필요한 항목 (WORK_SUMMARY.md에서 이월)

1. `ZigbangCrawler.py` / `NaverRealestateCrawler.py`를 `main.py` 파이프라인에 정식 편입할지
   (마이옥션은 2026-08-22에 이미 3단계로 편입 완료 — §2/§3 참고), 아니면 별도 온디맨드
   도구로 둘지
2. 위 §3/§7에서 언급한 죽은 코드·실험 스크립트·저장소 위생 문제 정리 여부와 범위
3. `fargate-task.json` 리전 불일치 수정 + `taskRoleArn`/Secrets Manager 연결

이 문서는 스냅샷이므로, 작업을 진행하며 위 결정 사항이 해소되면 이 파일도 함께 갱신할 것.
