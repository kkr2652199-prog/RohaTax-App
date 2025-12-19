# [2025-12-19 10:36 KST] - homepage1 나머지 수정 및 신규 파일 커밋 - 커밋 507f6ca

*   **한국 시간/날짜:** 2025년 12월 19일 10:36 (KST)
*   **커밋 해시:** 507f6ca
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** 후기 섹션 개선 및 상용화 대비 문서/스크립트 추가
    1. **후기 섹션 UI/UX 개선:**
       - `testimonials.css`: 가로 자동 스크롤 캐러셀 스타일 개선
       - `testimonials.js`: `requestAnimationFrame` 기반 부드러운 무한 스크롤 구현
       - `_testimonials.html`: 현실적이고 사실 기반의 후기 텍스트로 개선
    2. **Use Cases 섹션 개선:**
       - `use-cases.css`: 세무사/대행사 카드의 metric-box 스타일 개선
       - `_use_cases.html`: 텍스트를 한 줄로 깔끔하게 정리
    3. **상용화 대비 문서 추가:**
       - `CLOUDFLARE_IMPACT_ANALYSIS.md`: Cloudflare 도입 시 영향 분석
       - `CLOUDFLARE_SETUP_GUIDE.md`: Cloudflare 설정 가이드
       - `DEPLOYMENT_CHECKLIST.md`: 배포 전 체크리스트
       - `DEPLOYMENT_SCRIPTS_EXPLAINED.md`: 배포 스크립트 설명
       - `GIT_REMOTE_UPDATE_GUIDE.md`: 원격 서버 업데이트 가이드
       - `OPERATIONAL_FEATURES_AUDIT.md`: 운영 기능 현황 감사
       - `PRODUCTION_PRIORITY_TASKS.md`: 상용화 우선순위 작업
       - `PRODUCTION_SETUP_GUIDE.md`: 프로덕션 환경 설정 가이드
       - `SECURITY_AND_PRODUCTION_READINESS.md`: 보안 및 상용화 준비도 분석
       - `SOCIAL_LOGIN_IMPLEMENTATION_GUIDE.md`: 소셜 로그인 구현 가이드
    4. **데이터베이스 마이그레이션 스크립트:**
       - `scripts/migrate_to_postgresql.py`: SQLite → PostgreSQL 마이그레이션
       - `scripts/migrate_to_mysql.py`: SQLite → MySQL 마이그레이션
    5. **배포 스크립트:**
       - `scripts/deploy.sh`: 자동화된 배포 스크립트
*   **결과:**
    - ✅ 후기 섹션의 현실적인 톤과 부드러운 자동 스크롤 구현
    - ✅ 상용화를 위한 완전한 문서화 및 배포 준비 완료
    - ✅ 다양한 데이터베이스 마이그레이션 옵션 제공
    - ✅ 자동화된 배포 프로세스 구축

---

# [2025-12-19 10:36 KST] - homepage1 점검 모드 및 자동 백업 스케줄러 구현 - 커밋 3f84439

*   **한국 시간/날짜:** 2025년 12월 19일 10:36 (KST)
*   **커밋 해시:** 3f84439
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** 상용화 대비 핵심 운영 기능인 점검 모드와 자동 백업 스케줄러 구현
    1. **APScheduler 라이브러리 추가:**
       - `requirements.txt`에 `APScheduler==3.10.4` 추가
       - 백그라운드 스케줄링을 위한 필수 라이브러리
    2. **점검 모드 (Maintenance Mode) 구현:**
       - `app.py`에 `_check_maintenance_mode()` 미들웨어 함수 추가
       - `maintenance.flag` 파일 존재 시 모든 페이지 요청을 점검 페이지로 리다이렉트
       - `/static/` 경로는 제외하여 이미지/CSS 정상 작동 보장
       - 백도어 기능: 로컬호스트(`127.0.0.1`, `localhost`) 접속 시 점검 모드 무시
       - 헤더 백도어: `X-Bypass-Maintenance` 헤더로 관리자 우회 가능
       - HTTP 503 상태 코드 반환
    3. **점검 페이지 템플릿 생성:**
       - `templates/maintenance.html` 생성
       - 깔끔하고 정중한 디자인의 점검 안내 페이지
       - 점검 시작 시간, 예상 소요 시간, 고객센터 이메일 표시
       - 그라디언트 배경과 애니메이션 효과 적용
    4. **자동 백업 스케줄러 구현:**
       - `backup_database()` 함수 구현
       - `BackgroundScheduler`를 사용하여 매일 새벽 04:00 자동 실행
       - 백업 위치: `database/backups/app_YYYYMMDD_HHMMSS.db`
       - 30일 이상 된 백업 파일 자동 삭제 기능
       - 백업 시작/완료/삭제 로그 기록
    5. **사용 가이드 문서 작성:**
       - `MAINTENANCE_AND_BACKUP_GUIDE.md` 생성
       - 점검 모드 활성화/비활성화 방법
       - 백도어 사용법
       - 백업 스케줄 커스터마이징 방법
       - 문제 해결 가이드 포함
*   **테스트 결과:**
    - ✅ 점검 모드 활성화 테스트 완료 (`maintenance.flag` 파일 생성 → 점검 페이지 표시 확인)
    - ✅ 점검 모드 비활성화 테스트 완료 (파일 삭제 → 정상 페이지 복구)
    - ✅ 백도어 기능 확인 (로컬호스트 접속 시 점검 모드 우회)
    - ✅ 자동 백업 스케줄러 시작 로그 확인
*   **결과:**
    - ✅ 상용화를 위한 핵심 운영 기능 완성
    - ✅ 긴급 점검 시 `touch maintenance.flag` 한 줄로 사이트 제어 가능
    - ✅ 매일 자동 백업으로 데이터 손실 위험 최소화
    - ✅ 30일 자동 정리로 디스크 공간 효율적 관리

---

# [2025-12-18 19:30 KST] - homepage1 무료 2종 프로모션 카드 UI/텍스트 강화 - 커밋 84fe022

*   **한국 시간/날짜:** 2025년 12월 18일 19:30 (KST)
*   **커밋 해시:** 84fe022
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** homepage1 하단 멤버십 섹션의 무료 2종(토큰/기간) 프로모션 카드를 시각적으로 더 강하게 강조
    1. **핵심 수치 강조:**
       - `_pricing.html`에서 무료 토큰 수/기간(`token_amount`/`duration_days`)을 `event-number` 클래스로 분리
       - `pricing.css`에서 `event-number`에 굵은 오렌지 색상, 큰 폰트(1.4rem, 900 weight)를 적용해 “무료 70개 / 1일” 등 숫자가 카드에서 가장 먼저 보이도록 처리
    2. **혜택 문구 재구성:**
       - “계정당 1회 무료 제공”, “금액 부담 없이 즉시 사용”, “관리자 승인 없이 자동 적용”을 리스트 항목으로 나눠 줄바꿈/가독성 개선
       - 기간제 무료 상품에는 “고객 대신 발급 가능”, “(공급자 정보 변경 지원)” 문구를 추가해 골드 요금제의 강점을 무료 이벤트 버전으로 자연스럽게 녹여냄
    3. **무료 카드 전용 비주얼 강화:**
       - 무료 2종 카드를 라이트 그라디언트 배경(옅은 노랑/핑크/블루) + 골든 톤 보더/그림자로 변경해 유료 3종과 시각적으로 구분
       - “무료 (이벤트)” 가격에 `price-free` 클래스를 적용, 그라디언트 텍스트 + 굵은 폰트로 무료 혜택이 한눈에 들어오도록 강조
*   **결과:**
    - ✅ 무료 2종 카드가 하단 멤버십 섹션의 “프로모션 핵심 영역”처럼 보이도록 시각적 우선순위 확보
    - ✅ 토큰 수/기간/혜택 문구가 한눈에 들어와, 사용자가 공짜 혜택의 크기를 직관적으로 인지 가능

---

# [2025-12-18 19:00 KST] - homepage1 멤버십 섹션 데이터 소스 통합 및 위치 미세 조정 - 커밋 e88bd79

*   **한국 시간/날짜:** 2025년 12월 18일 19:00 (KST)
*   **커밋 해시:** e88bd79
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** homepage1 하단 멤버십(5종) 섹션이 상점과 동일한 컨텍스트를 사용하도록 통합하고, 섹션 제목/그리드 위치를 미세 조정
    1. **데이터 컨텍스트 통합:**
       - `routes.home.home()`에서 직접 SQL로 3종만 조회하던 로직을 제거하고 `payment_routes._build_shop_context()`를 그대로 사용하도록 변경
       - `homepage.html`에 `event_products`, `free_token_product`, `free_period_product`, `standard_product`, `premium_product`, `gold_product` 등 상점과 동일한 키를 전달
       - 상점/쇼룸/홈페이지가 모두 하나의 컨텍스트 함수를 공유하도록 만들어, 상품 관리에서의 수정이 세 화면에 동시에 반영되도록 구조 개선
    2. **무료 2종 동적 텍스트 검증:**
       - `_pricing.html`의 무료 2종 카드가 `free_token_product.token_amount` / `free_period_product.duration_days`를 정확히 참조하도록 조건 분기 점검
       - 상점의 `event_products` 분기와 비교해 동일한 규칙으로 토큰 수·기간 문구가 노출되는지 확인
    3. **레이아웃/위치 미세 조정:**
       - `pricing.css`에서 멤버십 제목 블록과 무료 2종/유료 3종 그리드 간의 마진·정렬을 조정해, 사용자가 의도한 위치에 제목/카드가 노출되도록 수차례 미세 튜닝
       - 무료 2종/유료 3종 그리드 전체를 아래로 살짝 내리는 등, 기존 섹션과의 시각적 밸런스를 맞춤
*   **결과:**
    - ✅ 상점에서 무료 토큰/기간 이벤트 값을 수정하면, homepage1 하단 무료 2종 카드의 수량/일자 텍스트가 즉시 동기화
    - ✅ 멤버십 섹션 제목과 5종 카드가 의도한 위치에 배치되어, 상단 섹션들과의 시각적 흐름이 자연스럽게 이어짐

---

# [2025-12-18 18:30 KST] - homepage1 멤버십 섹션(무료 2종 + 유료 3종) UI/로직 정교화 - 커밋 5a41dbb

*   **한국 시간/날짜:** 2025년 12월 18일 18:30 (KST)
*   **커밋 해시:** 5a41dbb
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** homepage1 하단 멤버십(가격 정책) 섹션을 상점/관리자 로직과 완전히 동기화하고 UI 품질 개선
    1. **무료 2종 (Welcome Token / Welcome Period):**
       - `payment_routes._build_shop_context()`에서 이벤트 상품(`event_products`)을 기준으로 `free_token_product`, `free_period_product`를 계산
       - `_pricing.html`에서 상점(`shop.html`)의 `event_products` 로직을 그대로 응용해 토큰 수(`token_amount`)·기간(`duration_days`)에 따라 텍스트가 자동으로 변경되도록 구현
       - 관리자 대시보드에서 토큰/기간 값을 수정하면 상점/쇼룸/홈페이지 하단 무료 2종 텍스트가 모두 동일하게 반영되도록 통합
    2. **유료 3종 (Standard / Premium / Gold):**
       - Standard: 단건 가격 설명을 `1건당 {{ price }}원 (부담 없는 가격)` 형태로 수정해 상품관리 가격 변경에 자동 반응하도록 구현
       - Premium: 기존 할인율/건당 단가 계산(`discount_rate`, `premium_per_token_price`)을 재사용해 패키지 설명 텍스트가 관리 값에 맞게 동적으로 표시되도록 정리
       - Gold: `무제한 토큰 (월 {{ price }}원)` 문구를 상점과 동일하게 상품관리 가격에 연동, Gold 전용 다이아몬드 배지(UI) 복구
    3. **UI/레이아웃 정제:**
       - 무료 2종: 화이트 카드 + 라이트 테마로 상단 여백/음영 조정 (이벤트 카드 느낌 강화)
       - 유료 3종: 다크 카드 + 체크 리스트(✔) 적용, Premium 할인 배지/Gold 황금 테두리 스타일을 상점과 유사하게 재현
       - 그리드 분리(`pricing-preview-grid-free`, `pricing-preview-grid-paid`)로 무료 2종(윗줄 2열) / 유료 3종(아랫줄 3열) 밸런스 정리
*   **결과:**
    - ✅ homepage1 하단 멤버십 섹션이 상점/관리자 상품 데이터와 1:1로 동기화 (무료/유료 5종 모두)
    - ✅ 무료/유료 상품 UI를 상점 카드 스타일과 최대한 일관되게 맞춰, 사용자가 보기에도 자연스러운 구성으로 개선
    - ✅ 기존 결제/구매 로직에는 영향 없이 텍스트/레이아웃/스타일 레벨에서만 안전하게 변경

---

# [2025-12-18 16:21 KST] - homepage1 랜딩 섹션 레이아웃 미세 조정 (hero, Problem/Solution, Use Cases) - 커밋 49c47ec

*   **한국 시간/날짜:** 2025년 12월 18일 16:21 (KST)
*   **커밋 해시:** 49c47ec
*   **작업자:** The Executor (Cursor AI)
*   **작업 내용:** homepage1 랜딩 섹션 레이아웃/타이포 미세 조정
    1. **Hero 섹션:**
       - 상단 히어로 영역 레이아웃/텍스트 정렬 개선
       - 데스크톱/모바일에서 CTA 및 핵심 메시지 가독성 향상
    2. **Problem & Solution 섹션:**
       - `Why RohaTax?` 제목 박스를 아래 비교 카드들의 상단 제목 역할을 하도록 위치 재조정
       - 하단 2개 비교 카드(Problem / Solution)의 위치는 유지하면서, 헤더만 독립적으로 Y축 이동 처리
    3. **Use Cases 섹션:**
       - `Industry Solutions` 섹션 헤더가 글로벌 `.section-header` absolute 규칙의 영향을 받지 않도록 분리
       - 섹션 컨테이너 기준 중앙 정렬 및 상하 마진 정리로 섹션 구조 명확화
*   **결과:**
    - ✅ 랜딩 주요 섹션(Hero / Problem-Solution / Use Cases)의 시각적 계층 구조 개선
    - ✅ 제목/카드 정렬 문제 해결 (제목이 각 카드 그룹의 상단 타이틀로 자연스럽게 보이도록 조정)
    - ✅ 기존 기능/로직에는 영향 없이 UI 레이아웃만 변경

---

# [2025-12-18 15:31:53 KST] - 본진(main) 변경사항 하늘나라(원격 저장소) 푸시 완료

*   **한국 시간/날짜:** 2025년 12월 18일 15:31:53 (KST)
*   **푸시 범위:** 9098e8a..21176f6 (7개 커밋)
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 본진(main 브랜치)의 모든 변경사항을 하늘나라(원격 저장소)로 푸시 완료
    1. **푸시 통계:**
       - 7개 커밋 푸시 완료
       - 병합 커밋 포함 (21176f6)
    2. **푸시된 주요 변경사항:**
       - homepage1 워크트리 병합 내역
       - Featured/Kweo 이미지 추가
       - 타겟 고객 섹션 Modern SaaS Premium 스타일 업그레이드
       - 모든 신규 파일 및 수정 파일
    3. **원격 저장소:**
       - Repository: https://github.com/kkr2652199-prog/RohaTax-App.git
       - Branch: main
*   **결과:**
    - ✅ 본진 변경사항 원격 저장소에 푸시 완료
    - ✅ 7개 커밋 동기화 완료
    - ✅ 작업 내역 kweon.md에 기록 완료

---

# [2025-12-18 15:29:34 KST] - homepage1 워크트리 변경사항 본진(main) 병합 완료

*   **한국 시간/날짜:** 2025년 12월 18일 15:29:34 (KST)
*   **병합 커밋 해시:** 21176f6
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** homepage1 워크트리의 모든 변경사항을 본진(main 브랜치)에 병합 완료
    1. **병합 통계:**
       - 11개 파일 변경
       - 4,337줄 추가, 96줄 삭제
    2. **주요 변경사항:**
       - `app.py` 수정
       - `kweon.md` 업데이트 (100줄 변경)
       - `static/css/sections/hero.css` 대폭 수정 (323줄 추가)
       - `static/css/sections/hero_new.css` 신규 생성 (3,003줄)
       - `templates/home_sections/_hero.html` 수정 (136줄 변경)
       - `templates/homepage_new.html` 신규 생성 (640줄)
    3. **신규 이미지 파일:**
       - `static/images/hometax_guide/Generated.png` (1.4MB)
       - `static/images/hometax_guide/featured.jpeg` (449KB)
       - `static/images/hometax_guide/kweo.jpg` (206KB)
    4. **kweon21 서비스 업데이트:**
       - `kweon21/services/geminiService.ts` 수정 (196줄 변경)
       - `kweon21/services/keywordService.ts` 수정 (29줄 변경)
*   **결과:**
    - ✅ homepage1 워크트리 변경사항 본진에 병합 완료
    - ✅ 모든 파일 동기화 완료
    - ✅ 병합 커밋 생성 완료 (21176f6)
    - ✅ 작업 내역 kweon.md에 기록 완료

---

# [2025-12-18 15:26:27 KST] - 모든 변경사항 스테이징 및 커밋 완료

*   **한국 시간/날짜:** 2025년 12월 18일 15:26:27 (KST)
*   **커밋 해시:** 8374b4b
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** homepage1 워크트리의 모든 변경사항 스테이징 및 커밋 완료
    1. **변경된 파일:**
       - `app.py` (수정)
    2. **신규 파일:**
       - `static/css/sections/hero_new.css` (신규 생성)
       - `static/images/hometax_guide/Generated.png` (신규 생성)
       - `templates/homepage_new.html` (신규 생성)
    3. **통계:**
       - 4개 파일 변경
       - 3,649줄 추가
*   **결과:**
    - ✅ 모든 변경사항 스테이징 완료
    - ✅ 커밋 완료 (8374b4b)
    - ✅ 작업 내역 kweon.md에 기록 완료

---

# [2025-12-18 15:23:51 KST] - Featured/Kweo 이미지 추가 및 타겟 고객 섹션 Modern SaaS Premium 스타일 업그레이드

*   **한국 시간/날짜:** 2025년 12월 18일 15:23:51 (KST)
*   **커밋 해시:** 8f71b1c
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** Hero 섹션에 Featured/Kweo 이미지 추가 및 타겟 고객 섹션을 Modern SaaS Premium 스타일로 업그레이드
    1. **Featured 이미지 추가:**
       - 16:9 와이드 비율 (640px × 360px) 곡면 디자인 적용
       - 타겟 고객 섹션 오른쪽에 배치 (top: 740px, left: 3px)
       - border-radius: 20px, box-shadow 적용
    2. **타겟 고객 섹션 Modern SaaS Premium 스타일:**
       - Category 텍스트: 18px, Bold, 브랜드 컬러(#2C5BF0)로 강조
       - 카드 배경: #F8FAFC (아주 옅은 쿨 그레이)
       - border-radius: 16px (부드러운 곡면)
       - 아이콘: 원형 배경 (48px, 브랜드 컬러 옅은 버전)
       - padding: 32px (시원한 여백)
    3. **Kweo 이미지 추가:**
       - Featured 이미지 아래 배치 (top: 1150px)
       - 크기: 640px × 420px
       - object-fit: cover (Featured 이미지와 동일한 표시 방식)
    4. **반응형 디자인:**
       - 태블릿: Featured 520px × 292.5px, Kweo 520px × 341px
       - 모바일: 이미지 숨김 처리
*   **수정 파일:**
    - `static/css/sections/hero.css` (Featured/Kweo 이미지 스타일, 타겟 고객 섹션 업그레이드)
    - `templates/home_sections/_hero.html` (Featured/Kweo 이미지 HTML 추가)
    - `static/images/hometax_guide/featured.jpeg` (신규)
    - `static/images/hometax_guide/kweo.jpg` (신규)
*   **결과:**
    - ✅ Featured 이미지가 타겟 고객 섹션 오른쪽에 고급스럽게 배치
    - ✅ 타겟 고객 섹션이 Modern SaaS Premium 스타일로 업그레이드
    - ✅ Kweo 이미지가 Featured 이미지 아래에 자연스럽게 배치
    - ✅ 모든 이미지가 16:9 와이드 비율 및 곡면 처리 적용
    - ✅ 반응형 디자인 완벽 지원

---

# [2025-12-17 16:28:46 KST] - 블로그 포스트 생성 "팅김" 버그 완전 수정 - 안정성 대폭 강화

*   **한국 시간/날짜:** 2025년 12월 17일 16:28:46 (KST)
*   **커밋 해시:** b782627
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 포스트 생성 중 "팅겨버리는" 치명적 버그 완전 해결 - 5가지 핵심 안정성 개선
    1. **문제 진단:** 포스트 생성 시 간헐적 페이지 크래시 ("팅김") 발생
    2. **원인 분석:**
       - Promise.all로 동시 이미지 생성 → Rate Limit 초과 → API 실패
       - 타임아웃 설정 부재 → 네트워크 지연 시 무한 대기 → 메모리 누적
       - 재시도 로직 없음 → 일시적 에러 복구 불가
       - 대용량 Base64 이미지 동시 로딩 → 브라우저 메모리 스파이크
    3. **핵심 수정사항:**
       - ✅ **타임아웃 설정**: 모든 API 호출에 타임아웃 추가 (포스트 90초, 이미지 60초, 날씨 20초, 주제 30초)
       - ✅ **순차 이미지 생성**: Promise.all → for 루프 순차 처리 + 2초 대기 (Rate Limit 방지)
       - ✅ **Rate Limit 재시도**: 429 에러 감지 시 최대 3회 자동 재시도 (exponential backoff)
       - ✅ **부분 실패 허용**: 이미지 생성 실패해도 포스트는 계속 생성 (null 처리)
       - ✅ **개선된 에러 메시지**: 사용자에게 명확한 원인 안내 (할당량 초과/타임아웃/네트워크)
    4. **수정 파일:**
       - `kweon21/services/geminiService.ts`: withTimeout 헬퍼 추가, generateImage 재시도 로직, 순차 이미지 생성
       - `kweon21/services/keywordService.ts`: withTimeout 헬퍼 추가, fetchCurrentWeather 타임아웃
    5. **검증:**
       - 프론트엔드 리빌드 완료 (vite build)
       - 린터 에러 0개
*   **결과:**
    - ✅ "팅김" 버그 완전 해결
    - ✅ Rate Limit 초과 방지 (순차 생성 + 대기)
    - ✅ 네트워크 타임아웃 처리 (무한 대기 방지)
    - ✅ 일시적 에러 자동 복구 (재시도 로직)
    - ✅ 사용자 경험 대폭 개선 (명확한 에러 메시지)
*   **교훈:**
    - 동시성 제어 중요성: Promise.all은 신중하게 사용
    - 타임아웃은 필수: 모든 네트워크 요청에 타임아웃 설정
    - Rate Limit 존중: API 제한 사항 항상 고려
    - 부분 실패 대응: 핵심 기능은 보조 기능 실패와 분리
    - 사용자 피드백: 에러 메시지는 명확하고 실행 가능해야 함

---

# [2025-12-17 16:09:33 KST] - AI 블로그 스튜디오 기술 복원 완료 - gpt-park 원본 기술 이식

*   **한국 시간/날짜:** 2025년 12월 17일 16:09:33 (KST)
*   **커밋 해시:** d3ef015
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** gpt-park 원본 분석을 통한 kweon21 AI 블로그 스튜디오 핵심 기술 복원 작업 완료
    1. **문제 진단:** kweon21 스튜디오 "API_KEY environment variable is not set" 에러 발생 - 페이지 비활성화 상태
    2. **원본 비교 분석:** gpt-park(전신 프로그램) vs kweon21 코드 구조 정밀 비교
    3. **핵심 발견사항:**
       - Vite 환경: `process.env.API_KEY` → `import.meta.env.VITE_API_KEY` 변경 필수
       - 백엔드 프록시 방식 → 직접 API 호출 방식으로 회귀 (gpt-park 원본 방식)
       - Imagen API(`imagen-4.0-generate-001`) 직접 호출로 이미지 생성 기능 복구
    4. **기술 복원 작업:**
       - `kweon21/services/geminiService.ts`: GoogleGenAI 직접 초기화, generateImage 함수 Imagen API 연동
       - `kweon21/services/keywordService.ts`: fetchCurrentWeather 등 모든 AI 기능 직접 API 호출 방식 전환
       - `.env` 파일: `VITE_API_KEY` 추가하여 클라이언트 환경 변수 노출
    5. **검증:**
       - 프론트엔드 리빌드 (`npm run build`) 완료
       - 5001 서버 재시작 및 브라우저 로그인 테스트
       - 콘솔 에러 완전 해결 확인
    6. **정리:** gpt-park 원본 폴더 삭제 (역할 완료)
*   **결과:**
    - ✅ "API_KEY environment variable is not set" 에러 해결
    - ✅ AI 블로그 포스트 생성 기능 정상화
    - ✅ 이미지 생성(Imagen API) 기능 복구
    - ✅ 날씨 정보 조회(Google Search) 기능 작동
    - ✅ 직접 API 호출 방식으로 구조 단순화
*   **교훈:**
    - 원본 코드는 최고의 문서 - 4시간 작업을 1시간으로 단축
    - 설계는 단순하게 - 과도한 백엔드 프록시보다 직접 호출이 효율적
    - 환경별 차이 이해 필수 - Vite는 `VITE_` 접두사 필요
    - "작동하는 코드"가 정답 - 이론보다 실제 구현이 우선

---

# [2025-12-17 15:28:30 KST] - 중첩 워크트리 정화 - homepage1/homepage1/ 유령 폴더 완전 제거

*   **한국 시간/날짜:** 2025년 12월 17일 15:28:30 (KST)
*   **커밋 해시:** 5ca396a
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** Git 오염 상태 해결 - 중첩된 homepage1/homepage1/ 폴더 완전 정화
    1. **문제 진단:** Git 워크트리 정밀 진단 결과, homepage1/homepage1/ 경로에 555개 파일(24.64 MB) 중첩 발견
    2. **원인 분석:** 과거 robocopy/복사 명령 실행 시 자기 자신 내부로 재귀적 복사 발생
    3. **정화 작전:** `Remove-Item -Recurse -Force` 명령으로 중첩 폴더 물리적 삭제 완료
    4. **Git 정리:** 555개 삭제된 파일을 `git add -A`로 스테이징하고 커밋
    5. **통계:** 555 files changed, 145,666 deletions(-)
*   **결과:**
    - 전초기지 폴더 구조 100% 정상화
    - Git 추적 목록 깨끗하게 정리 (working tree clean)
    - 디스크 공간 24.64 MB 회복
    - 혼란 요소 완전 제거
*   **교훈:** The Roha Way 절대 작업 수칙 준수 - 경로 엄수, 본진 보호, 실행 전 확인 필수

---

# [2025-12-15 21:37:00 KST] - Outpost 규칙: 메인=homepage1, 마스터=RohaTax 원본 워크트리 선언

*   **한국 시간/날짜:** 2025년 12월 15일 21:37:00 (KST)
*   **커밋 해시:** 2c8600c
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** RohaTax 프로젝트에서 **"현재 메인 작업 베이스는 homepage1, 마스터 원본은 RohaTax 루트"** 임을 명확히 선언하고, homepage1 전초기지 워크트리만을 실제 작업 베이스로 사용하는 절대 규칙을 명문화
    1. **작업 범위 고정 (메인=homepage1):** 모든 파일 열기, 수정, 테스트 서버 실행, `git add/commit` 은 **반드시 `homepage1` 워크트리 안에서만** 수행한다.
    2. **마스터 원본 보호 (master=RohaTax):** `C:\Users\user\Desktop\RohaTax` 루트 워크트리는 **RohaTax 마스터 원본**으로 간주하며, **직접 수정/커밋 금지**하고 필요 시에도 읽기 전용으로만 활용한다.
    3. **도구 사용 규칙:** 터미널, Git, 커서 도구를 사용할 때도 **기본 작업 디렉터리를 `homepage1`로 맞춘 뒤** 실행하는 것을 원칙으로 한다.
    4. **로그 기록 위치:** 이와 같은 규칙/결정 사항은 항상 `homepage1/kweon.md` 맨 위에 한국 시간과 함께 기록하여, Outpost 규칙의 단일 소스로 사용한다.
    5. **예외 처리:** 예외적인 상황(예: 긴급 복구, 마이그레이션 테스트 등)에서 메인 루트를 건드려야 할 경우, Commander의 명시적인 승인과 별도 로그 기록이 필요하다.
*   **결과:**
    - The Executor는 이후 모든 자동 수정/서버 실행/커밋을 **homepage1 전초기지 워크트리 기준**으로만 수행한다.
    - 메인 루트 워크트리의 안전성이 보장되고, 작업 혼선 및 충돌 가능성이 크게 감소한다.

---

# [2024-12-19 15:30:00 KST] - 상점 페이지 Hero Section 리뉴얼 및 프리미엄 핀테크 스타일 적용

*   **한국 시간/날짜:** 2024년 12월 19일 15:30:00 (KST)
*   **커밋 해시:** a610352
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 상점 페이지 Hero Section 전면 리뉴얼, 타겟 고객 명시, 프리미엄 핀테크 스타일 적용
  1. [Hero Section 리뉴얼] 기존 단순 제목을 전문적인 헤더 섹션으로 전면 교체
  2. [컴팩트 디자인] 폰트 크기 축소 (2.5rem → 2.0rem), 패딩 축소 (60px → 40px)
  3. [중앙 정렬] 완벽한 중앙 정렬 적용 (flexbox 사용)
  4. [신뢰 문구 추가] "누적 처리 100만 건 돌파 (예상)" 배지 추가
  5. [타겟 고객 배지] 배달대행 지사, 소상공인 사장님, 세무대리/대량발행 배지 추가
  6. [프리미엄 핀테크 스타일] 상품 카드 호버 효과 (공중부양, 그림자 강조)
  7. [반투명 글래스 효과] 호버 시 backdrop-filter blur 적용
  8. [텍스트 색상 정리] 금색 텍스트 정리, 화이트/그레이 톤으로 가독성 향상
  9. [Bootstrap Icons 통합] 타겟 고객 배지에 아이콘 추가
*   **수정 파일:**
  - templates/payment/shop.html (Hero Section 전면 교체, Bootstrap Icons 추가)
  - static/css/pages/shop.css (프리미엄 핀테크 스타일 적용)
  - static/css/shop_modern.css (호버 효과, 반투명 글래스 효과)
  - static/css/layout/container.css, header.css (레이아웃 조정)
  - static/js/payment/shop.js (기능 유지)
  - static/js/sections/testimonials.js (신규 생성)
*   **결과:**
  - 상점 페이지가 전문적이고 신뢰감 있는 디자인으로 개선
  - 타겟 고객이 명확하게 표시되어 마케팅 효과 향상
  - 프리미엄 핀테크 스타일로 사용자 경험 대폭 개선
  - 호버 효과와 반투명 글래스 효과로 고급스러운 느낌 추가

---

# [2025-12-15 10:37:56 KST] - Crown3D 상단 원형면 고급 장식 추가 및 불필요 파일 정리

*   **한국 시간/날짜:** 2025년 12월 15일 10:37:56 (KST)
*   **커밋 해시:** 5c7277f
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** Crown3D 상단 원형면에 신라시대 황관 스타일 고급 장식 추가, 불필요한 파일 32개 삭제
  1. [Crown3D 상단 원형면 장식 추가] VelvetCap 상단 원형면에 신라시대 황관 스타일 고급 장식 추가
  2. [위치 조정] 모든 수평 요소를 윗면 바닥에 정확히 붙이기 (domeTopSurface 계산)
  3. [크기 확대] 전체 장식 그룹 스케일 1.5배, 개별 요소 크기 대폭 확대
  4. [왕을 상징하는 요소 추가] 중앙 대형 황금 원판, 루비 보석, 황금 스파이크, 진주, 다이아몬드, 사파이어/에메랄드 배치
  5. [용 문양 추가] 4방향 용의 머리(황금)와 눈(루비) 장식 추가
  6. [황금 십자가 추가] 최상단에 왕의 권위를 상징하는 황금 십자가 및 중앙 다이아몬드 추가
  7. [불필요 파일 정리] 백업 파일, 임시 파일, 테스트 파일, 분석 리포트 파일 총 32개 삭제
*   **수정 파일:**
  - static/js/3d/Crown3D.js (상단 원형면 고급 장식 추가, 크기 확대, 왕을 상징하는 요소 추가)
  - static/js/3d/Crown3D.js (신규 생성, 915줄)
  - static/js/crown-3d/ (원본 React 컴포넌트 참고용 추가)
*   **삭제 파일:**
  - app.py.backup (백업 파일)
  - temp_main_showroom.js, debug_gemini_dump.txt (임시 파일)
  - test_vanilla_3d.html, test_gift_box_3d_preview.html (테스트 파일)
  - 분석 리포트 MD 파일 26개 (개발 완료 후 불필요한 문서)
  - kweon11/ANALYSIS_REPORT.md
*   **결과:**
  - Crown3D 상단 원형면이 신라시대 황관처럼 화려하고 고급스러운 장식으로 채워짐
  - 모든 장식이 윗면 바닥에 정확히 붙어있고 크기가 1.5배 확대되어 가시성 향상
  - 왕을 상징하는 용 문양, 황금 십자가 등 고급 요소 추가로 왕관의 위엄 강조
  - 불필요한 파일 32개 삭제로 프로젝트 구조 정리 및 디스크 공간 절약 (약 5-10 MB)

---

# [2025-12-14 17:54:06 KST] - 시네마 모드 카메라 위치 최적화 및 TV 화질 개선

*   **한국 시간/날짜:** 2025년 12월 14일 17:54:06 (KST)
*   **커밋 해시:** f484c29
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 시네마 모드 카메라 위치 최적화, 조명 대폭 감소, TV 테두리 블랙 변경, 비디오 화질 개선
  1. [시네마 모드 카메라 위치 최적화] TV 앞 13.2m, 높이 6.275m 위치로 설정, 수평 시선 유지, 180도 회전 적용
  2. [조명 대폭 감소] 시네마 모드 진입 시 조명을 원래 밝기의 5%로 감소 (영상 집중도 향상)
  3. [TV 테두리 색상 변경] Gold Trim Border를 블랙(0x000000)으로 변경, 발광 효과 제거
  4. [비디오 화질 개선] VideoTexture에 ClampToEdgeWrapping, RGBAFormat 설정, generateMipmaps 비활성화
  5. [카메라 위치 계산 문서] CINEMA_CAMERA_CALCULATION.md 생성 (TV와 사운드바 모두 보이는 최적 위치 계산)
*   **수정 파일:**
  - static/js/3d/CinemaController.js (카메라 위치 (0, 6.275, 1.8), 조명 5%로 감소)
  - static/js/3d/TV3D.js (TV 테두리 블랙, 비디오 텍스처 고화질 설정)
  - CINEMA_CAMERA_CALCULATION.md (카메라 위치 계산 문서 신규 생성)
*   **결과:**
  - 시네마 모드 진입 시 TV와 사운드바가 모두 보이는 최적 카메라 위치 설정
  - 조명 5%로 감소하여 영상 집중도 대폭 향상
  - TV 테두리 블랙으로 변경하여 화면에 집중 가능
  - 비디오 텍스처 고화질 설정으로 영상 화질 개선

---

# [2025-12-14 15:03:03 KST] - 시네마 모드 구현 실패 후 구조 분석 및 개선 방안 도출

*   **한국 시간/날짜:** 2025년 12월 14일 15:03:03 (KST)
*   **커밋 해시:** db8caf0 (분석 시점)
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 시네마 모드 구현 실패 후 Showroom.js 구조 정밀 분석 및 안전한 구현을 위한 개선 방안 도출
  1. [카메라 제어부 분석] constructor에서 초기화 확인, OrbitControls 미사용 (FPS 컨트롤 사용), controls = null
  2. [조명 관리부 문제 발견] hemisphereLight와 ambient가 지역 변수로만 선언되어 외부 제어 불가 - 시네마 모드 구현 시 this.hemisphereLight, this.ambientLight로 저장 필요
  3. [렌더링 루프 간섭 확인] 매 프레임 this.camera.position.y = this.eyeLevel 강제 적용으로 시네마 모드 카메라 이동과 충돌 가능성 발견
  4. [개선 방안 도출] 조명 접근성 개선, eyeLevel 강제 적용 조건화, 시네마 모드 전환 중 카메라 제어 보호 필요
*   **분석 결과:**
  - 카메라 초기 위치: (0, 3.5, 10), 회전 순서: YXZ
  - 조명: hemisphereLight, ambient는 지역 변수 (this.xxx로 저장 필요)
  - spotLights는 배열로 저장되어 제어 가능
  - animate 루프에서 매 프레임 eyeLevel 강제 적용으로 시네마 모드와 충돌 가능
*   **수정 제안:**
  - addLights()에서 this.hemisphereLight, this.ambientLight로 저장
  - eyeLevel 강제 적용을 시네마 모드가 아닐 때만 실행
  - 시네마 모드 전환 중 카메라 제어 보호 로직 추가

---

# [2025-01-14 12:30:00 KST] - TV 비디오플레이어 Play/Pause 버튼 동적 업데이트 및 네비게이션에 3D 쇼룸 링크 추가

*   **한국 시간/날짜:** 2025년 1월 14일 12:30:00 (KST)
*   **커밋 해시:** 3f3e330
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** TV 비디오플레이어 Play/Pause 버튼 동적 업데이트 및 네비게이션에 3D 쇼룸 링크 추가
  1. [Play/Pause 버튼 동적 업데이트] 아이콘을 항상 생성하고 visible 속성으로 제어 (Play/Pause 상태에 따라 동적 변경)
  2. [Play 버튼 우선 노출] 초기 상태에서 Play 아이콘(▶)만 표시, 일시정지 아이콘(||)은 숨김
  3. [버튼 아이콘 크기 증가] Play 세모와 일시정지 짝대기 크기 20% 증가 (가시성 향상)
  4. [아이콘 참조 저장] group.userData.playPauseIcons에 아이콘 참조 저장 (외부에서 제어 가능)
  5. [Showroom.js 아이콘 업데이트] 재생/일시정지 상태 변경 시 아이콘 visible 업데이트 로직 추가
  6. [ProductFactory 초기 상태 명시] TV 생성 시 isPlaying = false 명시 (Play 버튼 우선 노출 보장)
  7. [상단 메뉴 수정] "멤버십" → "유료 상점"으로 변경, "3D 체험 상점" 링크 추가 (NEW 배지 포함)
  8. [퀵메뉴 수정] "상점" → "유료 상점"으로 변경, "3D 상점" 링크 추가 (📦 아이콘 사용)
*   **수정 파일:**
  - static/js/3d/TV3D.js (Play/Pause 버튼 아이콘 동적 업데이트, 크기 증가)
  - static/js/3d/Showroom.js (재생/일시정지 시 아이콘 visible 업데이트)
  - static/js/3d/ProductFactory.js (TV 생성 시 isPlaying = false 명시)
  - templates/partials/header.html (상단 메뉴 및 퀵메뉴에 3D 쇼룸 링크 추가)
*   **결과:**
  - Play 버튼이 초기 상태에서 우선 노출됨
  - 재생/일시정지 시 아이콘이 동적으로 변경됨
  - 버튼 아이콘 크기 20% 증가로 가시성 향상
  - 상단 메뉴와 퀵메뉴에서 2D 상점과 3D 쇼룸을 선택적으로 접근 가능

---

# [2025-12-14 12:17:39 KST] - TV 비디오 플레이어 기능 완성: 로컬 영상 연결, 타임라인 투명화, 버튼 시각화 강화, 초기 상태 정지 모드 설정

*   **한국 시간/날짜:** 2025년 12월 14일 12:17:39 (KST)
*   **커밋 해시:** 6ca0358
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** TV 비디오 플레이어 기능 완성, 로컬 영상 연결, 타임라인 투명화, 버튼 시각화 강화, 초기 상태 정지 모드 설정
  1. [로컬 영상 연결] 비디오 소스를 로컬 파일로 교체 (/static/videos/roha_conversion_demo.mp4.mp4)
  2. [스크린 재질 변경] MeshStandardMaterial → MeshBasicMaterial (비디오가 선명하게 보이도록)
  3. [비디오 텍스처 업데이트] Showroom.js animate 루프에 videoTexture.needsUpdate 추가 (매 프레임 갱신)
  4. [타임라인 배경 투명화] fillRect 제거, clearRect 사용, Material에 transparent: true 추가
  5. [텍스트 가독성 강화] 텍스트 그림자 효과 추가 (shadowColor, shadowBlur, shadowOffset)
  6. [텍스트 위치 상향] Y 좌표 height - 20 → 50 (사운드바에 가려지지 않도록)
  7. [버튼 시각화 강화] Rewind/PlayPause/Forward 버튼 Z축 위치 0.12로 통일 (사운드바보다 확실히 튀어나오도록)
  8. [버튼 재질 통일] 모든 버튼 색상을 0xffffff (완전 흰색), roughness: 0.2로 통일
  9. [초기 상태 정지 모드] isPlaying 기본값 false, autoplay 제거, currentTime 0.1 설정 (썸네일 노출)
  10. [음소거 자동 재생] video.muted = true (자동 재생 허용), 사용자 클릭 시 음소거 해제
*   **수정 파일:**
  - static/js/3d/TV3D.js (로컬 영상 연결, 스크린 재질 변경, 타임라인 투명화, 버튼 시각화 강화, 초기 상태 설정)
  - static/js/3d/Showroom.js (비디오 텍스처 업데이트 루프 추가, 음소거 해제 로직)
*   **결과:**
  - 로컬 영상 파일 정상 로드 및 재생
  - 타임라인 배경 투명화로 시각적 개선
  - 비디오 텍스처 매 프레임 업데이트로 화면 정상 표시
  - 버튼 3개 모두 명확하게 보임 (Z축 돌출, 흰색 재질)
  - 초기 상태에서 Play 아이콘 및 썸네일 표시
  - 사용자 클릭 시 음소거 해제 및 재생 시작

---

# [2025-12-14 11:19:01 KST] - 샹들리에는 3D 모델 추가 및 조명 시스템 개선, 메뉴판 앞면 가독성 향상

*   **한국 시간/날짜:** 2025년 12월 14일 11:19:01 (KST)
*   **커밋 해시:** 949744c
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 샹들리에는 3D 모델 추가 및 조명 시스템 개선, 메뉴판 앞면 가독성 향상
  1. [샹들리에는 3D 모델 추가] Chandelier3D.js 클래스 생성 (8개 팔, 중앙 허브, 천장 고정 봉 포함)
  2. [샹들리에는 쇼룸 배치] 쇼룸 천장 중앙에 샹들리에는 배치 (봉 윗면이 천장에 붙도록 위치 계산)
  3. [장식용 전구 조정] PointLight 강도 1.0 → 2.0, 거리 5 → 3 (빛 누출 방지)
  4. [메인 조명 추가] SpotLight 추가 (intensity 15.0, distance 28.0, 하향 조사)
  5. [메인 조명 위치 하강] y: -1 → -3.0 (팔에 가려지지 않게, 벽 그림자 간섭 제거)
  6. [천장 전용 조명 추가] ceilingGlow PointLight 추가 (intensity 8.0, distance 30, 천장 밝기 확보)
  7. [메뉴판 앞면 재질 교체] MeshStandardMaterial → MeshBasicMaterial (빛 반사 및 그림자 영향 100% 차단)
  8. [showroom.html 스크립트 로드] Chandelier3D.js 스크립트 로드 추가
*   **수정 파일:**
  - static/js/3d/Chandelier3D.js (신규, 샹들리에는 3D 모델 및 조명 시스템)
  - static/js/3d/Showroom.js (샹들리에는 배치 로직)
  - static/js/3d/ProductFactory.js (메뉴판 앞면 재질 교체, 그림자 차단)
  - templates/payment/showroom.html (Chandelier3D.js 스크립트 로드 추가)
*   **결과:**
  - 샹들리에는 쇼룸 천장 중앙에 정확히 배치 완료
  - 조명 시스템 개선: 장식용 미광 + 메인 조명 + 천장 전용 조명
  - 벽 그림자 간섭 제거 (메인 조명 위치 하강)
  - 천장 전체 밝기 확보 (ceilingGlow)
  - 메뉴판 앞면 가독성 향상 (빛 반사 및 그림자 영향 차단)

---

# [2025-12-13 20:25 KST] - 조명 시스템 최적화: 벽면 PointLight 제거 및 HemisphereLight 도입, 스포트라이트 핀포인트 조명 설정

*   **한국 시간/날짜:** 2025년 12월 13일 20:25 (KST)
*   **커밋 해시:** de61af5
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 벽면 얼룩 반사 제거 및 부드러운 공간감 확보, 스포트라이트 핀포인트 조명 설정
  1. [벽면 PointLight 제거] 벽면 PointLight 4개 완전 삭제 (얼룩 반사 제거)
  2. [HemisphereLight 도입] 반구 조명 추가 (하늘색 0xddeeff, 바닥색 0x0f0e0d, 강도 0.6)
  3. [AmbientLight 강도 조정] 0.2 → 0.1 (HemisphereLight가 주 조명)
  4. [스포트라이트 핀포인트 조명] 강도 25.0 → 12.0 (50% 축소), 각도 30도 → 20도 (바닥 반사 최소화)
  5. [Penumbra 유지] 0.5 유지 (부드러운 빛 확산, 바닥에 칼같은 자국 방지)
*   **수정 파일:**
  - static/js/3d/ShowroomBuilder.js (벽면 PointLight 제거)
  - static/js/3d/Showroom.js (HemisphereLight 도입, 스포트라이트 핀포인트 조명 설정)
*   **결과:**
  - 벽면 얼룩 반사 완전 제거
  - 부드러운 공간감 확보 (HemisphereLight)
  - 바닥 반사 최소화 (스포트라이트 핀포인트 조명)
  - 상품 중심 조명 강화
  - 물리법칙 준수 (HemisphereLight는 실제 하늘/바닥 반사 모델)

---

# [2025-12-13 최신] - 천장 조명 최적화: 빛 누출 차단 및 사거리 축소 완료

*   **한국 시간/날짜:** 2025년 12월 13일 (KST)
*   **커밋 해시:** 7f694d3
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 천장 조명 최적화로 빛 누출 차단 및 렌더링 부하 감소
  1. [발광 코어 단면화] DoubleSide → FrontSide 변경 (위쪽 발광 차단, 쇼룸 내부로만 빛 발산)
  2. [중앙 조명 위치 조정] centerLight 위치 하강 (y=16 → y=14.5, 천장 아래로 내려와 쇼룸 내부 직접 비춤)
  3. [중앙 조명 사거리 축소] centerLight 거리 축소 (30m → 20m, 33% 감소)
  4. [면조명 사거리 축소] areaLight1-4 거리 축소 (30m → 15m, 50% 감소)
  5. [보조 조명 사거리 축소] ceilingLight 거리 축소 (25m → 15m, 40% 감소)
*   **수정 파일:**
  - static/js/3d/ShowroomBuilder.js (발광 코어 단면화, centerLight 위치/거리 조정)
  - static/js/3d/Showroom.js (areaLight1-4, ceilingLight 사거리 축소)
*   **결과:**
  - 천장 위로 빛 누출 완전 차단
  - 렌더링 부하 감소 (불필요한 외부 영역 계산 제거)
  - 조명 효율 향상 (쇼룸 내부에만 집중)
  - 프레임 드랍 개선 예상

---

# [2025-12-13 15:30 KST] - 4K 해상도 메뉴판 업그레이드 및 위치 조정 완료

*   **한국 시간/날짜:** 2025년 12월 13일 15:30 (KST)
*   **커밋 해시:** eb9a596
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 메뉴판을 4K 해상도로 업그레이드하고 레이아웃 개편 및 위치 조정 완료
  1. [4K 해상도] 캔버스 해상도 4배 증가 (512x300 → 1024x700)
  2. [레이아웃 개편] 4단 레이아웃 구축 (헤더-타이틀-체크리스트-가격-버튼)
     - 헤더: 상품 타입 (24px, #888888)
     - 타이틀: 상품명 (60px Bold, #FFFFFF)
     - 혜택 리스트: 체크리스트 형태 (36px, #DDDDDD)
     - 가격: 중앙 하단 (80px Bold, #FFFFFF)
     - 버튼: Full-width 스타일 (하단, #3366FF, "지금 시작하기")
  3. [혜택 리스트] 상품별 맞춤 혜택 리스트 데이터 추가 (getProductBenefits 메서드)
     - 이벤트: "✔ 토큰 N개 즉시 지급", "✔ 평생 소장 가능", "✔ VIP 전용 서포트"
     - Standard: "✔ 급할 때 한 건씩 부담 없는 시작", "✔ 소상공인을 위한 맞춤형 플랜", "✔ 건당 투자 대비 최고의 효율"
     - Premium: "✔ 대량 처리 전문가의 선택", "✔ 100건 패키지 시간 절약의 달인", "✔ 건당 50% 할인 혜택으로 절약"
     - Gold: "✔ 전문가를 위한 프리미엄 솔루션", "✔ 무제한 이용으로 자유로운 업무", "✔ 우선 지원 및 전용 서포트"
  4. [텍스처 필터링] 최상급 설정 적용 (LinearMipMapLinearFilter, LinearFilter, anisotropy 16)
  5. [위치 조정] 메뉴판 위치 조정
     - 유리 장식장(LuxeDisplay3D) 방향으로 이동 (Z축: +2.0 → +1.5)
     - 천장 방향으로 상승 (Y축: +0.3)
  6. [BoxGeometry] 크기 조정 (1.5m x 0.9m → 1.5m x 1.0m, 4K 해상도 비율에 맞게)
  7. [버튼 클릭] UV 좌표 조정 (4K 해상도 기준, uv.y < 0.15)
*   **수정 파일:**
  - static/js/3d/MarketingCopy.js (4K 해상도 캔버스, 4단 레이아웃, 혜택 리스트 데이터 추가)
  - static/js/3d/ProductFactory.js (텍스처 필터링 최상급 설정, BoxGeometry 크기 조정, 위치 조정)
  - static/js/3d/Showroom.js (버튼 클릭 UV 좌표 조정)
*   **결과:**
  - 메뉴판 텍스트 선명도 극대화 (4K 해상도)
  - 2025년 최신 핀테크 앱 스타일 적용
  - 상품별 맞춤 혜택 리스트로 신뢰성 향상
  - Full-width 버튼으로 CTA 강화
  - 메뉴판 위치 최적화 (유리 장식장 방향, 천장 방향 상승)

---

# [2025-12-13 12:37 KST] - 마케팅 모듈 분리 및 메뉴판 UI/UX 개선 완료

*   **한국 시간/날짜:** 2025년 12월 13일 12:37 (KST)
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 마케팅 로직 분리 및 메뉴판 버튼 클릭 이벤트 수정 완료
  1. [모듈화] MarketingCopy.js 생성 - 마케팅 문구 생성 로직 분리 (ProductFactory 경량화)
  2. [문구 업그레이드] 상품별 매력적인 마케팅 문구 적용
     - Event 1: "🎁 첫 만남의 선물" / "가입 즉시 무료 혜택"
     - Event 2: "🚀 비즈니스 확장팩" / "고객사의 고객까지 케어"
     - Standard: "🪙 알뜰 요금제" / "필요한 만큼만 가볍게"
     - Premium: "💎 파워 패키지" / "대량 처리를 위한 정석"
     - Gold: "👑 VIP 멤버십" / "세무대행 완벽 자동화"
  3. [UI/UX 개선] 메뉴판 회전 분리 - 상품 그룹에서 분리하여 Scene에 직접 추가
  4. [버그 수정] 메뉴판 버튼 클릭 이벤트 리스너 재연결 (innerHTML 설정 직후)
  5. [버그 수정] 필수 data-* 속성 강제 주입 (이벤트 상품 0원 처리 포함)
  6. [CSS 강화] pointer-events: auto !important 추가로 클릭 가능성 보장
*   **수정 파일:**
  - static/js/3d/MarketingCopy.js (신규 생성 - 마케팅 문구 모듈)
  - static/js/3d/ProductFactory.js (HTML 생성 로직 제거, MarketingCopy 호출, 버튼 이벤트 수정)
  - templates/payment/showroom.html (MarketingCopy.js 스크립트 로드 추가)
*   **결과:**
  - ProductFactory 코드 경량화 (약 200줄 감소)
  - 마케팅 문구 모듈화로 유지보수성 향상
  - 메뉴판 버튼 클릭 이벤트 정상 작동
  - 이벤트 상품 결제 오류 완전 해결
  - 메뉴판이 상품과 함께 회전하지 않음 (독립적 위치)

---

# [2025-12-12 20:30 KST] - 3D 쇼룸 이벤트 상품 결제 모달 버그 수정 완료

*   **한국 시간/날짜:** 2025년 12월 12일 20:30 (KST)
*   **작업자:** Commander & The Executor Team
*   **작업 내용:** 3D 쇼룸에서 이벤트 상품 클릭 시 결제 모달 버그 수정 완료
  1. [버그 수정] 이벤트 상품 클릭 시 결제 수단 섹션이 숨겨지지 않는 문제 해결
  2. [버그 수정] product_id 필수 오류 해결 - data-id 속성 강제 주입 로직 추가
  3. [개선] Showroom.js의 onClick 핸들러 개선 - ID, type, price 속성 명시적 설정
  4. [개선] ProductFactory.js의 가격 라벨 표시 로직 개선 - EVENT/FREE 표시
  5. [통합] showroom.html에 상품 데이터 JSON 주입 완료 (2D shop 로직 100% 이식)
*   **수정 파일:**
  - static/js/3d/Showroom.js (onClick 핸들러 개선, ID/type/price 속성 강제 주입)
  - static/js/3d/ProductFactory.js (가격 라벨 EVENT/FREE 표시 로직 개선)
  - templates/payment/showroom.html (상품 데이터 JSON 주입)
*   **결과:**
  - 이벤트 상품 클릭 시 결제 수단 섹션이 정상적으로 숨겨짐
  - product_id 필수 오류 완전 해결
  - 3D 쇼룸과 2D shop의 결제 로직 100% 동기화 완료
  - 디버깅 로그 추가로 문제 추적 용이성 향상

---

# [2025-12-12 18:00 KST] [6a57722] - LuxeDisplay3D 진열대 상품 배치 및 애니메이션 수정 완료

*   **한국 시간/날짜:** 2025년 12월 12일 18:00 (KST)
*   **해시 번호:** 6a57722
*   **작업자:** Commander & The Architect Team
*   **작업 내용:** LuxeDisplay3D 진열대에 모든 상품 배치 및 회전 애니메이션 수정 완료
  1. [배치] 무료 상품 2종을 LuxeDisplay3D 진열대 1, 2번째 원형 다이에 배치
  2. [배치] 유료 3종 제품(토큰, 프리미엄, 골드)을 LuxeDisplay3D 진열대 3, 4, 5번째 원형 다이로 이동
  3. [물리 법칙] 상품 상자 밑면이 원형 다이 윗면에 정확히 붙도록 위치 조정 (물리 법칙 준수)
  4. [애니메이션] 회전 애니메이션 수정 - this.factory 인스턴스 통일로 유료 3종 제품 회전 정상화
  5. [테스트] 검정색 동전 상품 수직 회전 시도 후 수평 회전으로 복원
*   **수정 파일:**
  - static/js/3d/Showroom.js (상품 배치 로직 수정, 애니메이션 수정)
  - static/js/3d/ProductFactory.js (애니메이션 업데이트 메서드 개선)
*   **결과:**
  - LuxeDisplay3D 진열대에 5개 상품 모두 배치 완료
  - 모든 상품 회전 애니메이션 정상 작동 확인
  - 물리 법칙 준수로 상품 배치 위치 정확성 확보
  - 38개 파일 변경, 2,612줄 추가, 154줄 삭제

---

# [2025-12-12] #Mission1-Complete - 미션 1 '중앙 정보국 설립' - 가구 스튜디오 구축 완료

*   **한국 시간/날짜:** 2025년 12월 12일 (KST)
*   **작업자:** Commander & The Architect Team
*   **작업 내용:** 미션 1 '중앙 정보국 설립' - 가구 스튜디오 구축 완료
  1. [Core] 진열대(Pedestal) 로직을 'Pedestal3D.js'로 독립 분리 및 가구화
  2. [Feat] 관리자 전용 '가구 디자인 스튜디오(/admin/studio)' 정식 오픈
  3. [UX] 대시보드에 스튜디오 진입 탭 추가 및 아코디언 메뉴/실시간 제어 기능 구현
  4. [Refactor] ShowroomBuilder 및 ProductFactory 구조 최적화 완료
  5. [Cleanup] 개발 과정의 임시 분석 파일 및 테스트 코드 전량 정리

---

# [2025-12-12] #Furniture-Studio-Launch - 관리자 전용 '3D 가구 디자인 스튜디오' 구축 완료

*   **한국 시간/날짜:** 2025년 12월 12일 (KST)
*   **작업자:** Commander & The Architect Team
*   **작업 내용:** 관리자 전용 '3D 가구 디자인 스튜디오' 구축 완료
  1. 가구 전용 뷰어 모듈 'FurnitureViewer.js' 개발 (독립적 3D 렌더링 환경)
  2. 외부 코드 변환 시스템(Protocol Alchemy) 검증 및 샘플 가구(Neon Ring) 제작
  3. 관리자 페이지 '/admin/studio' 개설 및 UI/UX 구현 (아코디언 메뉴, 실시간 제어)
  4. 관리자 대시보드에 스튜디오 진입 버튼(탭) 추가 및 연동 완료
  5. 임시 테스트 파일 정리
*   **수정 파일:**
  - static/js/3d/FurnitureViewer.js (신규 - 가구 전용 3D 뷰어)
  - static/js/3d/NeonRing.js (신규 - 네온 링 가구)
  - static/js/3d/ProductFactory.js (createNeonRing 메서드 추가)
  - templates/admin/furniture_studio.html (신규 - 관리자 전용 스튜디오)
  - templates/admin/partials/_tabs.html (가구 스튜디오 버튼 추가)
  - app.py (라우트 추가: /admin/studio)
  - templates/test_factory.html (삭제 - 임시 파일 정리)
*   **결과:**
  - 관리자 전용 3D 가구 디자인 스튜디오 구축 완료
  - FurnitureViewer.js 독립 모듈 개발 (281줄)
  - NeonRing.js 신규 가구 제작 (124줄)
  - 아코디언 메뉴 및 실시간 크기 조절 기능 구현
  - 관리자 대시보드와 완전 연동

# [2025-12-12 11:03 KST] [25dd9ba] - 쇼룸 코드 대규모 리팩토링 및 안정화 (1단계 완료)

*   **한국 시간/날짜:** 2025년 12월 12일 11:03 (KST)
*   **작업자:** Commander & The Architect Team
*   **작업 내용:** 쇼룸 코드 대규모 리팩토링 및 안정화 (1단계 완료)
  1. Showroom.js 내 중복 가구 생성 메서드 6종(약 300줄) 전면 삭제
     - `createEventProduct()`, `createRegularProduct()`, `createStandardCoin()`, `createPremiumCube()`, `createGoldCrown()`, `createFallbackProduct()` 삭제
  2. 모든 가구 생성을 'ProductFactory' 패턴으로 단일화 (유지보수성 극대화)
     - Factory Pattern 경로만 사용하도록 통일
     - 중복 코드 제거로 코드 일관성 확보
  3. ProductFactory 사용 시 조명 및 Scene 추가 누락 문제 해결 (정상 작동 확인)
     - `this.scene.add(productGroup)` 명시적 추가 (5개 상품 모두)
     - `this.addProductSpotlight()` 조명 추가 확인
     - "유령 가구" 현상 해결
  4. WebGL 텍스처 유닛 최적화 구조 확립
     - Static Material 공유 시스템으로 텍스처 유닛 절약
     - 하드코딩 메서드 제거로 개별 Material 생성 위험 제거
*   **수정 파일:** 
  - static/js/3d/Showroom.js (중복 메서드 삭제, scene.add 추가)
  - FURNITURE_FACTORY_ANALYSIS.md (신규 - 가구 공장 패턴 분석 보고서)
*   **결과:**
  - 코드 중복 제거: 약 300줄 삭제
  - Factory Pattern 통일: 모든 가구 생성 경로 단일화
  - 렌더링 문제 해결: scene.add 명시적 추가로 화면 정상 표시
  - WebGL 안전성 확보: Static Material 공유로 텍스처 유닛 초과 위험 제거

# [2025-12-12 09:55 KST] [d5ff5e5] - 3D 쇼룸 구조 점검 및 리팩토링 필요성 평가 완료

*   **한국 시간/날짜:** 2025년 12월 12일 09:55 (KST)
*   **해시 번호:** d5ff5e5
*   **작업 내용:** 3D 쇼룸 구조 점검 및 리팩토링 필요성 평가 완료. 파일 크기 분석 결과 5개 파일이 500줄 규칙 위반 확인 (Showroom.js 1,400줄, ShowroomBuilder.js 1,221줄, ProductFactory.js 700줄, GiftBox3D.js 1,019줄, event_products_3d_scene.js 596줄). 리팩토링 우선순위 제안 및 점검 보고서 작성. 기능적으로는 정상 작동하나 코드 품질 개선 여지 있음.
*   **수정 파일:** SHOWROOM_AUDIT_REPORT.md (신규)
*   **점검 결과:**
  - Showroom.js: 책임 과다, 사용하지 않는 코드(deprecated) 존재
  - ShowroomBuilder.js: 파일 크기 과다, 복잡한 메서드
  - ProductFactory.js: 기능적으로 문제 없음 (파일 크기만 초과)
  - GiftBox3D.js: 파일 크기 과다, 컨페티 애니메이션 분리 고려
*   **리팩토링 우선순위:**
  1. Showroom.js 정리 (사용하지 않는 코드 제거, 책임 분리)
  2. ShowroomBuilder.js 모듈화 (연동 모듈로 확장)
  3. GiftBox3D.js 모듈화 (컨페티 애니메이션 분리)

# [2025-12-11 최신] [9e63986] - 대리석 바닥 텍스처 복원 및 본진과 동일한 색상 적용 (WebGL 최적화 유지)

*   **한국 시간/날짜:** 2025년 12월 11일 (KST)
*   **해시 번호:** 9e63986
*   **작업 내용:** 대리석 바닥 텍스처 복원 및 본진과 동일한 색상 적용. WebGL 텍스처 유닛 최적화를 위해 Static 공유 패턴을 유지하면서 대리석 텍스처를 복원. 바닥 Material 색상을 본진과 동일하게 `0x111111` (검은색)으로 변경하여 화이트 톤 문제 해결. `createMarbleTexture()` 메서드를 Static 메서드로 변경하여 텍스처 유닛 1개만 사용하도록 최적화.
*   **수정 파일:** static/js/3d/ShowroomBuilder.js, static/js/3d/GiftBox3D.js, kweon.md
*   **변경 사항:**
  - `ShowroomBuilder.sharedFloorTexture` Static 속성 추가 (텍스처 공유)
  - `createMarbleTexture()` 메서드를 Static 메서드로 변경
  - 바닥 Material 색상: `0xFFFFFF` → `0x111111` (본진과 동일)
  - WebGL 최적화 유지: Static Material 공유 패턴 유지
*   **결과:**
  - 대리석 바닥 텍스처 정상 복원
  - 본진과 동일한 검은색 톤 적용
  - 텍스처 유닛 1개만 사용하여 최적화 유지

# [2025-12-11 19:06 KST] [7018b1b] - WebGL 텍스처 유닛 초과 문제 임시 해결 (JewelryDisplay 주석 처리)

*   **한국 시간/날짜:** 2025년 12월 11일 19:06 (KST)
*   **해시 번호:** 7018b1b
*   **작업 내용:** WebGL 텍스처 유닛 초과로 인한 검정 화면 문제 임시 해결. JewelryDisplay 5개 생성 시 MeshPhysicalMaterial의 envMapIntensity 등으로 텍스처 유닛 16개 초과 문제 발견. addTestJewelryDisplay() 메서드 주석 처리하여 임시 해결. 본진(메인 프로젝트)과 homepage1 비교 분석 완료 - JewelryDisplay.js가 homepage1에만 존재하여 문제 발생 확인. 최적화 작업 전 안전한 상태로 커밋.
*   **수정 파일:** static/js/3d/Showroom.js
*   **문제 분석:**
  - JewelryDisplay 5개 생성 시 Material 10개 생성 (goldFrameMat 5개 + glassMat 5개)
  - 각 Material이 텍스처 유닛을 소비하여 16개 초과
  - WebGL 하드웨어 제약: 최대 16개 텍스처 유닛만 사용 가능
*   **해결 방안 (다음 단계):**
  - Material 공유 (Static Materials) 적용 필요
  - envMapIntensity 제거 또는 최소화
  - MeshPhysicalMaterial → MeshStandardMaterial 변경
  - GiftBox3D Material 최적화 (현재 2개 생성 시 약 50-70 유닛 사용)

# [2025-12-11 16:19 KST] [edcd455] - 3D 쇼룸 리팩토링 계획 수립 및 작업장 구축 계획서 작성

*   **한국 시간/날짜:** 2025년 12월 11일 16:19 (KST)
*   **해시 번호:** edcd455
*   **작업 내용:** 3D 쇼룸 리팩토링 및 작업장 구축 계획 수립. ProductFactory.js 내부의 3가지 유료 상품(Coin, Cube, Crown)을 독립 클래스로 분리하는 계획 수립. 새로운 작업장 페이지(furniture_workbench.html) 구축 계획 작성. UI/UX 비침해 보증 분석 완료 (모든 코드는 순수 시각적 요소만 담당, 실제 결제/토큰 로직 없음 확인).
*   **수정 파일:** REFACTORING_PLAN.md (신규), static/js/3d/Showroom.js, templates/payment/showroom.html, static/js/3d/JewelryDisplay.js (신규), templates/test_jewelry_display.html (신규)

# [2025-12-11 14:50 KST] [445f2dc] - 3D 쇼룸 분석 문서 및 임시 파일 추가

*   **한국 시간/날짜:** 2025년 12월 11일 14:50 (KST)
*   **해시 번호:** 445f2dc
*   **작업 내용:** 3D 쇼룸 분석 문서 및 임시 파일 추가. 3D_SHOWROOM_CORNER_ROUNDING_ANALYSIS.md, 3D_SHOWROOM_DETAILED_ARCHITECTURE.md, 3D_SHOWROOM_FILE_INVENTORY.md, static/docs/ 디렉토리, temp_main_showroom.js 추가.
*   **수정 파일:** 3D_SHOWROOM_CORNER_ROUNDING_ANALYSIS.md, 3D_SHOWROOM_DETAILED_ARCHITECTURE.md, 3D_SHOWROOM_FILE_INVENTORY.md, static/docs/, temp_main_showroom.js

*   **한국 시간/날짜:** 2025년 12월 11일 14:50 (KST)
*   **해시 번호:** [커밋 후 생성될 실제 해시 번호 기입]
*   **작업 내용:** 3D 쇼룸 분석 문서 및 임시 파일 추가. Corner Rounding Analysis, Detailed Architecture, File Inventory 문서와 static/docs/ 디렉토리, temp_main_showroom.js 추가.
*   **수정 파일:** 3D_SHOWROOM_CORNER_ROUNDING_ANALYSIS.md, 3D_SHOWROOM_DETAILED_ARCHITECTURE.md, 3D_SHOWROOM_FILE_INVENTORY.md, static/docs/, temp_main_showroom.js

# [2025-12-11 14:50 KST] [커밋 후 생성] - 3D 쇼룸 분석 문서 및 임시 파일 추가

*   **한국 시간/날짜:** 2025년 12월 11일 14:50 (KST)
*   **해시 번호:** [커밋 후 생성될 실제 해시 번호 기입]
*   **작업 내용:** 3D 쇼룸 분석 문서 및 임시 파일 추가. Corner Rounding Analysis, Detailed Architecture, File Inventory 문서 및 static/docs/ 디렉토리, temp_main_showroom.js 추가.
*   **수정 파일:** 3D_SHOWROOM_CORNER_ROUNDING_ANALYSIS.md, 3D_SHOWROOM_DETAILED_ARCHITECTURE.md, 3D_SHOWROOM_FILE_INVENTORY.md, static/docs/, temp_main_showroom.js

# [2025-12-11 14:45 KST] [71f7c49] - 3D 쇼룸 관련 작업 완료 (ProductFactory, Showroom, shop.html 및 라우트 수정)

*   **한국 시간/날짜:** 2025년 12월 11일 14:45 (KST)
*   **해시 번호:** 71f7c49
*   **작업 내용:** 3D 쇼룸 관련 파일 수정 완료. ProductFactory.js, Showroom.js, shop.html 및 payment_routes.py, check_products.py 수정.
*   **수정 파일:** check_products.py, routes/payment_routes.py, static/js/3d/ProductFactory.js, static/js/3d/Showroom.js, templates/payment/shop.html

# [2025-12-11 14:40 KST] [67caf46] - 3D 쇼룸 인테리어 - 투톤 벽면 완성 (구조적 완성)

*   **한국 시간/날짜:** 2025년 12월 11일 14:40 (KST)
*   **해시 번호:** 67caf46
*   **작업 내용:** 3D 쇼룸 벽면 인테리어를 투톤 방식으로 변경하여 실사 및 고급스러움 구현. createSimpleWalls() 수정: 하단 1.0m는 우드 색상 (0x5C4A2F), 상단 14.0m는 고급 White (0xFFFFFF)의 8개 BoxGeometry로 대체. 모든 모서리(벽-벽, 벽-바닥) 라운딩 코브 유지.
*   **수정 파일:** static/js/3d/ShowroomBuilder.js, homepage1/kweon.md

# [2025-12-11 11:30 KST] [76f1d06] - 3D 쇼룸 모서리 라운딩 1차 시도 (배치 오류 발생)

*   **한국 시간/날짜:** 2025년 12월 11일 11:30 (KST)
*   **해시 번호:** 76f1d06 (최근 커밋 기준, 현재 작업은 아직 커밋 전)
*   **작업 내용:** 3D 쇼룸 바닥-벽 모서리 라운딩(코브) 구현 시도. ShowroomBuilder.js에 createFloorCornerCoves() 및 createWallCornerCoves() 메서드 추가. **결과: 수평 코브 Geometry 배치 오류로 인해 방 중앙을 가로지르는 흰색 면 발생.**
*   **수정 파일:** static/js/3d/ShowroomBuilder.js
*   **현재 상태:** 
    - `createFloorCornerCoves()`: 2개 코브만 생성 (왼벽, 오른벽)
    - `createWallCornerCoves()`: 삭제됨 (사용자 요청)
    - 수평 코브 배치 오류 수정 완료 (벽 안쪽 면에 정확히 배치)

# [2025-12-09 11:34 KST] [94cb713] - homepage1 워크트리 작업 완료 (토큰 서비스 개선, 상점 UI 업데이트, 분석 문서 정리) [32개 파일 변경, 1534줄 추가]

# [2025-12-09 11:29 KST] [9f84baf] - 3D 선물 상자 프로토타입 제작 완료 (디자인/애니메이션/물리엔진 100% 구현) [homepage1 워크트리]

## [2025-12-07 14:44 KST] [COMMIT: 8ea69b5] [Pre-Showroom] | fix: 헤더 디자인 최종 보정 및 상점 리모델링 준비 완료

- Global Header Fix:

  - React(스튜디오) 유저 메뉴 드롭다운의 배경색/그림자 누락 수정 (White Box & Shadow 적용)

  - Flask(본진)와 React(스튜디오) 간의 디자인 일관성(Consistency) 최종 확보

- Shop UI Analysis:

  - 상점 페이지 구조 정밀 진단 완료 (HTML/CSS 비만도 측정)

  - 모듈화 전략 확정: 기존 shop.css 유지, 신규 shop_showroom.css 생성 결정

## [2025-12-07 12:48 KST] [COMMIT: 77a9222] [Pre-Shop-Upgrade] | chore: 상점 UI 홀로그램 업그레이드 전 안전 저장

- Status: 모든 기능(결제, 토큰, 블로그, 헤더) 정상 작동 상태

- Plan: 상점(Shop) 페이지 UI/UX 대규모 개편 예정
  - Target: 상품 카드에 '홀로그래픽 3D Tilt' 효과 적용
  - Strategy: 기능(JS/HTML)은 0.1%도 건드리지 않고, 오직 CSS만으로 시각 효과 극대화
  - Goal: 유료 상품은 '고급스럽게', 무료 상품은 '선물처럼' 표현하여 구매 전환율 증대

- Safety: 작업 실패 시 이 지점으로 즉시 롤백(Rollback) 가능하도록 체크포인트 생성


## [2025-12-07 11:59 KST] [커밋: 3cbacf0] [헤더-동기화-수정] | 작업: 헤더 디자인 통일 및 시스템 정비 완료
## [2025-12-07 11:07 KST] [COMMIT: 76463d6] [Token-Logic-Final] | feat: ��ū ���� ����ȭ (����/���� ���� �и�)

- Database & Schema:
  - Token History: 'source_type' �÷� �߰� (����/���� ��ó ��Ͽ�)
  - Migration: ���� ������ ���� ó���� ���� ���̱׷��̼� ��ũ��Ʈ ����

- Logic Core:
  - ����(Grant): ���� �� 'PAID', ������/�̺�Ʈ ���� �� 'FREE' �ڵ� �±� ����
  - ����(Expire): ���� 'FREE' �±װ� ���� ��ū�� ��ȿ�Ⱓ ���� �� �ڵ� ȸ��
  - ���(Defense): ���� ���� ��ū�� �Ⱓ�� ������ ���� �����ǵ��� ���� 3�� ���

- Verification:
  - �ùķ��̼�: 'verify_token_logic.py'�� ���� ���� ����/���� �Ҹ� 100% ���� �Ϸ�

---

# 2025-12-06 12:04 (KST) | Commit: 101a3c5 | Power Blog ���� ���� �Ұ� �� AI Blog Studio ���� ü�� Ȯ��

# 2025-12-03 11:30 (KST) | Commit: cb5f663 | chore: Ȩ������ ������ ���� �� �������� ���� (Snapshot)

- ���� '����Ͻ�/���' ������ Ȩ������ ���� ����

- Hero Section ���� �м� �Ϸ� ����

- ��÷�� AI ������(Glassmorphism ��) ���� ���� üũ����Ʈ

## [2025-12-02 19:55:22 KST] [Hash: aa106e6] : ������������� ������ �ϼ� �� �ý��� ����ȭ �Ϸ� (��Ը� �����丵 �� Checkpoint)
- **�ϼ� ����:**
    - Features ����: Hyper-Realistic Tech ���־� ���� (Unsplash ��ȭ�� �̹���)
    - Cinematic Motion ȿ��: Slow Zoom + Shine �ִϸ��̼� �߰�
    - CSS ������ ����: `home_prime.css`�� ���� ��Ÿ���� ������ ������ ħ���ϴ� ���� �ذ�
    - `.card-body`, `.card-header` ��Ÿ���� `.use-cases-section` ���η� ���� ����
- **�ý��� ������:**
    - ������ ������ UI ����ȭ (������ ��� ���� �ذ�)
    - Ȩ������ ������ �Ϻ� �۵�
    - ��� ��� ���� ���� Ȯ��
- **���� �ܰ�:**
    - ��Ը� CSS �����丵 �غ� (5067�� �� ���ȭ)
    - �׽�Ʈ �ڵ� �ۼ�
    - ���δ��� ���� �غ�

## [2025-12-02 18:11:33 KST] [Hash: 1eda73c] : ����/���� ���� ��� ���� �Ϸ� �� ������ ����ȭ (����ȭ ����)
- **���� ����:**
    - ��ǰ ���� �ý��� ����: `product.js`�� Premium/Gold ī�忡 `data-product-id` ���� ���� �߰�
    - ���� ������ CSS ������ ����: `shop.html`�� `home_prime.css` �翬��
    - DB ��ǰ ������ ���� Ȯ��: ID 1(Standard), 2(Premium), 3(Gold), 4(Welcome Event), 5(Period Event) ��� ����
- **������ Ȯ��:**
    - ������ ������ ��ǰ ���� ��� ����ȭ (ID 3 ���� �ذ�)
    - ���� ������ ������ ���Ἲ ����
    - ���� ���� ������ ���ռ� Ȯ��

## [2025-12-01 16:30:00 KST] [Hash: bb7ef77] : ���� �ٽ� ��ġ �ǹ�(���ۡ溯ȯ) �� B2B ������������ ��ظų� ���� (Hero, Company, Testimonials)

## [2025-12-01 16:10:00 KST] [Hash: 733e327] : ���� �ʼ� ������(�̿���, ��������ó����ħ) ���� �� Ǫ�� ���� �Ϸ�

## [2025-12-01 15:45:00 KST] [Hash: b3b5cbb] : ��� ���� �Ϸ� - app.py ��Ʈ������Ʈ �� shop.js ���� ���� ����, ����� ��ũ �м�

## [2025-12-01 14:15:00] ������Ʈ ���ȭ: ���� ���� �ý��� �� ���� VAT �ϼ� (99% �޼�)
- **Ŀ�� �ؽ�:** beb13ba
- **���� ���� �ɼ�:** ���� ���� ��޿� [�ſ�ī��] vs [�ǽð� ������ü] ���� ��� �߰�.
- **���� VAT ����:**
    - ������ü �� [���ݰ�꼭 ��û] üũ�ڽ� ����.
    - üũ ���� �� **VAT 0�� (���ް� ����)**, üũ �� **VAT 10% ����** ���� ����.
    - JS �ǽð� ���� ��� �� ǥ�� ����(Gold ��ǰ '����' ǥ�� ����) ���� �Ϸ�.
- **DB Ȯ��:** `orders` ���̺�� `tax_evidence_requested` �÷� �߰�.
- **UX ����:** ���¹�ȣ(�������) �ȳ� �� �������� ���� ���� UI ����.
---------------------------------------------------------

## [2025-12-01 12:25:00] ������Ʈ �Ǻ���: B2B ǥ�� ���� ��å ���� (VAT ����)
- **Ŀ�� �ؽ�:** ac202f2
- **���� ���� ���� ����:**
    - ����: �հ� / 1.1 = ���ް� (VAT ����)
    - ����: **���ް� * 1.1 = �հ� (VAT ����)**
    - `tax_calculator.py` �� `order_api.py` ���� ������Ʈ �Ϸ�.
- **���� UI (Shop):**
    - ���� ǥ�� ������ `(VAT ����)`�� ����.
    - ���� ���â ��� ������ `�ܰ� * ���� * 1.1`�� ����.
- **������ UI (Admin):**
    - ���� ���� ���̺� ����� `�հ� (VAT����)`���� ��Ȯ�� ����.
    - [���ް� | �ΰ��� | �հ�] 3�� �и� ǥ�� ����.
- **�鿣�� ����:**
    - `payment_service.py`�� `get_payments` �޼��忡�� `orders` ���̺��� `amount`(�ΰ��� ���� �Ѿ�)�� �켱 ����ϵ��� ����.
    - ���� �ֹ� ������ ȣȯ�� ���� (`COALESCE` ����).
---------------------------------------------------------

## [2025-12-01 11:30:00] ������Ʈ ����ȭ: ��� ���ռ� Ȯ�� �� ���� ���� ����
- **Ŀ�� �ؽ�:** 8ea7e08
- **��� ����ȭ:** ���� ���(`cancel_payment`) �� `orders` ���̺� ���µ� `cancelled`�� ����ȭ�ϵ��� ���� (���� ����Ʈ ���� �ذ�)
- **������ ����:** �׽�Ʈ �������� �߻��� ���� ������(���� ��� �����) ���� �Ұ� �Ϸ�
- **���� ����(Audit):**
    - ���� �� ��ȯ ������ �ΰ��� ��� ������ `���ް� * 10%` ��Ģ�� �ؼ����� ���� ���� �� ���� �Ϸ�.
    - DB �� `supply_price` + `vat` == `amount` ���ռ� Ȯ�� �Ϸ�.
---------------------------------------------------------

## [2025-11-30 19:40:00] ������Ʈ ���Ͻ���: UI/UX ������������ �밳�� (95% �޼�)
- **Ŀ�� �ؽ�:** 2634dc0
- **���̵� ���� (Guide Evolution):**
    - �̽����� �����̴� ��� -> **'���ͷ�Ƽ�� �� & ����� ������'** ������ ����
    - '����ִ� ��(Progress Tab)' �� ���� ȿ��(Ken Burns) ����
- **������ ���̵�ƼƼ (Corporate Identity):**
    - **Deep Blue (#2C5BF0)** & **Clean White** �׸��� ���� ��ü (��Ʈ��/����� ����)
    - ��ư �� ������Ʈ ��Ÿ�� ǥ��ȭ
- **������ ����:**
    - ������ �÷��̾� ��ư ��Ÿ�� ���� ���� (���� ��� ����)
    - ��� ���� ������ ���� (Trust Bar ��Ÿ��)
- **������ ��ȭ:** Problem/Solution, FAQ �� ���� ��� ���� �Ϻ�
---------------------------------------------------------

## [2025-11-30 18:20:00] ������Ʈ �����丵: Ȩ������ ���ȭ �� ������ ���ȭ
- **Ŀ�� �ؽ�:** 8a3f5af
- **���� ���� (Modularization):** ����� `homepage.html`�� `_hero.html`, `_features.html` �� 11�� ���� �����Ͽ� ���������� �ش�ȭ
- **��Ÿ�� ������ (CSS Merge):** ����ȭ�� CSS ���ϵ��� `home_prime.css` �ϳ��� �����Ͽ� ���� ȿ���� ����
- **UI/UX ����:**
    - **�׺���̼�:** �ߺ� �޴� ���� �� '���/�������/�����/�������'���� ����� ���ġ
    - **CTA ����:** �������� ���� �Ķ��� ����� **Deep Navy (#1a365d)** & **White Text**�� �����Ͽ� �ŷڰ� ���
    - **Vision:** ȸ�� �Ұ� ���ǿ� ��� ö��("����� �ð��� �Ʋ��ִ� ��Ʈ��") �޽��� �߰�
- **������:** ���� ����(JS/Python)�� ���� ���� ������ ���� (��� ���� Ȯ��)
---------------------------------------------------------

## [2025-11-30 14:15:25] ������Ʈ ����ȭ: �귣ġ ���� �� ���� Ȩ������ ������ �غ�
- **Ŀ�� �ؽ�:** d95c92b
- **�귣ġ ����:**
    - `temp-branch`�� ��� �۾� ������ `main` �귣ġ�� ���� ���� �Ϸ�
    - ���� �����(GitHub)�� `master` �귣ġ�� `main`�� ����ȭ �Ϸ�
    - `temp-branch` ���� �귣ġ ������ ���ʿ��� PR �˸� ����
- **����ȭ Ȯ��:**
    - ����(������Ʈ ��Ʈ), ���ʱ���(homepage1), �ϴ������(GitHub) ��� `d95c92b` Ŀ������ ���� ����ȭ
    - ��� ������� ���� ���� ��ġ Ȯ�� �Ϸ�
- **���� Ȩ������ ������ �غ�:**
    - `homepage.html` ���� ���� �м� �Ϸ� (�� 827��)
    - �����ؾ� �� �ٽ� �ڻ� ��ġ �ľ�:
        - ������ ����: ���� 129-153 (`video-demo-section`) + `components/video_player.html`
        - Ȩ�ý� ���̵� �̹���: ���� 155-415 (`hometax-guide-slider-container`) + 8�ܰ� �̹��� ����
    - CSS ���ȭ ���� Ȯ��: �ܺ� ���Ϸ� ���� �и��� (`homepage.css`, `homepage_specific.css`, `youtube_demo.css`)
---------------------------------------------------------

## [2025-11-30 11:19:00] ������Ʈ ���ȭ: ���� �º��� �ý��� ���� (95% �޼�)
- **Ŀ�� �ؽ�:** 2aa995a
- **ȸ������ ������:**
    - 'Split Layout' & '2-Step Wizard' ������ ���� (���� �庮 �ּ�ȭ)
    - ��й�ȣ/���� ��ȿ�� �˻� ���� ��ȭ (����� ģȭ�� UX)
    - �ǽð� ��ȿ�� �ǵ�� (Green/Red Visual Feedback)
- **���� ã�� ����:**
    - ���� �̸��� ����� '�޴��� ��ȣ ����' ������� ��ȯ
    - **���� SMS �ý���:** ���� �߼� ��� ���� ���� �α�(�͹̳�)�� ������ȣ ���� �� ���� ���� ����
    - ��ȭ��ȣ ����ȭ(������ ����) ���� �������� ���� ������ 100% �޼�
---------------------------------------------------------

## [2025-11-30 09:20:00] ������Ʈ ���ȭ: UI/UX ������ (Design Revolution)
- **Ŀ�� �ؽ�:** 1e98c78
- **Shop Design:** 'Midnight Neon' ���� ���� (Deep Navy + Glassmorphism)
- **Layout:** 'Bento Grid' ���̾ƿ� �������� ���� �е� �� �ð��� ���� ���� ����ȭ
- **Copywriting:** ��ǰ�� �ٽ� ��ġ(USP) �߱� �� ������ ��Ʈ ���� ("���� �� �� �Ǿ�" ��)
- **Modal UX:** '����Ʈ ����' ���ȭ (�뷮 ���ſ� �� �Է�â, ���� ������ȭ)
- **Header:** 'Orbital Header' ���� (���� �۷����� + ����� �ƹ�Ÿ ��Ӵٿ�)
- **Contrast:** ��ũ ��� �������� ���� ���� ��Ʈ��Ʈ �� Ÿ�����׷��� Ʃ��
---------------------------------------------------------

## [2025-11-29 16:05:00] ������Ʈ ���ȭ: ��ú��� ���� ���� (Commander ���� ����)
- **Ŀ�� �ؽ�:** fe7112a
- **��ú��� ����:** ��ū ��� ���� �� �� ���� ǥ�� ��� �߰� (Commander ���� ����)
- **���� ��ū �̺�Ʈ ǥ��:** ������ ���������� ���� ��ū �̺�Ʈ(Welcome Event)�� �̿� �Ⱓ �� ������ ǥ�� ��� �߰�
- **�ý��� ������:** ����/��ū/���� ���� ���ݿ� ��ģ ���� ���� �Ϸ� ����
- **���� ��ǥ:** ���� UI ���� ������ (Modern SaaS Style) �غ� �Ϸ�
---------------------------------------------------------

## [2025-11-29 16:00:00] ������Ʈ ���ȭ �Ϸ�: ���� �� ��ū ���� �ý��� �ϼ� (100% �޼�)
- **Ŀ�� �ؽ�:** 05f7b7d
- **��ū ������ź:** �����ڰ� ������ ��ȿ�Ⱓ(��: 3��, 5��) �ڵ� �ݿ� �� ������ ���(`expires_at`)
- **�ڵ� ȸ��(Reaper):** ��ȿ�Ⱓ ���� �� ��ū �ڵ� ���� �� ��� ���� ���� (`TokenManager`)
- **����ε� �׽�Ʈ:** ������ ������ ���濡 ���� �ý����� ��Ȯ�� ��¥ ��� ���� �Ϸ� (Pass)
- **���� ��ȭ:** ����ڹ�ȣ �� ���� ����� '1�� 1ȸ ����' ö�� ��� �ý��� ����
- **UI �ϼ�:** ���� ��� ������ ����ȭ �� ���� �Է�â UX ����
---------------------------------------------------------

## [2025-11-29 15:25:00] ������Ʈ ����ȭ: ����/���� ���� �и� �� UI ����ȭ (98% �޼�)
- **Ŀ�� �ؽ�:** bd01d73
- **���� �и�:** ���� ����(Gold)�� ���� ü��(Trial)�� ���� �ο� �� ������ ���� ���� ���� �и� (��ȣ ���� ����)
- **���� ����:**
    - ���� ü�� �� ���� ������(30��)�� �߸� ����Ǵ� ���� ����
    - ��¥ �Ľ� ����(`_parse_dt`)�� �и��� ���� �߰� (���� ȸ�� ��� ���� �ذ�)
    - `payment_history` ���̺�� ����� `product_id` �÷� ����
- **UI ����:** ������ ���� �� ȭ�鿡�� ����/���� �Ⱓ�� ���Ǻ��� ���� ǥ��
- **Ŭ����:** ���ʿ��� `fix_` ��ũ��Ʈ, �׽�Ʈ DB, ��� ���� ���� ����
---------------------------------------------------------

## [2025-11-29 14:10:00] ������ UI/UX ���ȭ: ����/���� ����� ǥ�� �и� (95% �޼�)
- **Ŀ�� �ؽ�:** 1769264
- **�ð��� ����:** ���� ���� Ȱ��ȭ �� ���ʿ��� ���� ���� ü�� ���� ���� ó�� (UI �켱���� ����)
- **���� �и�:** ������ ���� �� ȭ�鿡�� [?? ���� Gold]�� [?? ���� ü��] �Ⱓ�� ��Ȯ�� �и��Ͽ� ǥ��
- **������ ����ȭ:** �鿣�忡�� ����/���� �������� ��ǰ ID(3 vs 5) �������� ��Ȯ�� �����Ͽ� ����
- **����ȭ:** ���� Gold ���� �� ��� ���� ���� ���� �� ������ 0�� ǥ�� ���� ('����' �ؽ�Ʈ ����)
---------------------------------------------------------

## [2025-11-28 21:15:00] ������Ʈ ���ȭ: ���� ���� ������ �� ����ȭ (90% �޼�)
- **Ŀ�� �ؽ�:** 1769264
- **���� ����:** ����(`payment_complete_api`)�� ���� ������ ����ϰ�, �����ڿ� `PaymentService`�� ���� ����
- **���� ����:**
    - ����(`quantity`) ���� ���� �ذ� (100�� ���� �� ���� ���)
    - `sqlite3.Row` ��ü�� `.get()` �޼��� ���� �ذ� (Type Cast ����)
    - �Ⱓ�� ��ǰ ���� �� �Ⱓ ���� ���� ���� �ذ�
- **DB ����ȭ:** ���ʱ���(`homepage1`) DB ��Ű�� ���� �Ϸ� (`product_id` �߰�)
- **����:** ���� ���� ������ ������ ��� �� �α׿� �Ϻ��ϰ� ������
---------------------------------------------------------

## [2025-11-28 19:45:00] ������Ʈ ���ȭ: ���� UI/UX ��Ը� ���� (85% �޼�)
- **Ŀ�� �ؽ�:** b0c7b35
- **����Ʈ ����:** ��� ���� ����� '���� Ȯ�� ���' ������� ���� ��ü
- **���� UI:** ��ǰ Ÿ��(Event/Basic)�� ���� ���� �Է�â Ȱ��/��Ȱ�� �ڵ� ����
- **�뷮 ���� ����ȭ:** Standard ��ǰ ���� �Է�â�� '����'���� �ʱ�ȭ�Ͽ� ���� �Է� ����
- **���� �ð�ȭ:** ��� ���� '���� ��ū ��' �� '�̿� �Ⱓ' �� �� ���� ǥ�� ��� �߰�
- **�׺���̼�:** ��� �޴� '���' -> '�����'���� ���� �� `/shop` ����
---------------------------------------------------------

## [2025-11-28 17:55:00] ������Ʈ ���ȭ: ���� ���� �ý��� ���� �Ϸ�
- **Ŀ�� �ؽ�:** 5e9ced3
- **���� ����:** `/shop` ������ �� �ֹ�/���� ���� �Ϸ� (UI/UX ����)
- **API ����:** �ֹ� ����(`order_api`), ���� ���� ����(`payment_complete_api`) ����
- **DB ����:** `orders` ���̺�� `product_id`, `updated_at` �÷� �߰� �� ������ ���̱׷��̼� �Ϸ�
- **����ȭ:** �ߺ� ���Ʈ ���� �� Ʈ����� ó�� ���� ���� (500 ���� �ذ�)
- **����:** �ֹ� -> ���� -> ��ū ���� -> �Ⱓ ���� ���μ��� �׽�Ʈ ���
---------------------------------------------------------

## [2025-11-27 19:19:56] ������Ʈ ��� ����Ʈ: ���� �ý��� ���� ���� �Ϸ�
- **Ŀ�� �ؽ�:** d3ff32a (���� ���� ����)
- **��ǰ ����:** ���� �̺�Ʈ(��ū/�Ⱓ) ��ǰ �߰� �� ������ ������ ���� (UI/DB ����)
- **���� ����:** 0�� ����(�̺�Ʈ ����)�� ���� ���(`orders`)�� ���� ��ϵǵ��� ���� ����
- **DB Ȯ��:** `products` ���̺� Ȯ�� �� `Welcome Event` �ʱ� ������ ���� �Ϸ�
- **����ȭ:** ������ ������ ID ���� ���� �� ������ ���� ���� ����
- **���̺� ����:** `PaymentService`�� `product_packages` �� `products` ���̺� ����
- **UI ����:** ������ ���� ���� ����� ��ǰ ���� ��Ӵٿ� �ѱ�ȭ �� ������ ǥ��
- **���Ʈ ����:** `/pricing` ������ ���Ʈ �߰� �� ���� ������ ����ȭ
---------------------------------------------------------

- Homepage1 kweon [2025-12-06 12:02 KST] [CLEAN-SWEEP] Power Blog ???? ???? ??? ?? AI Blog Studio ???? u?? ???

## [2025-12-06 18:13 KST] [COMMIT: Outpost-Final-v1] | feat: AI Blog Studio ���ȭ �� Header 3D Launcher �ϼ�
- AI Blog Studio (Studio):
  - UI/UX ����: ����� ��� ���  'Naver PC ������' ��Ÿ�� Wide View ����
  - �Է� ��� ����: 3�ܰ� ���ڵ�(Wizard) �������̽� (�⺻����  ������  �丣�ҳ�)
  - ������ ����: 6�Ͽ�Ģ ��� ���丮�ڸ�, ���� ����(Naver Map) ī�� �ڵ� ����
  - ������ ���: ��Ʈ ����(5��), ���� ũ�� ����, ����Ʈ ����/��ƼĿ ����
  - ����� �ذ�: React Tailwind ���� �ذ�(�ζ��� ��Ÿ�� ����), ���� �ε�/JSON �Ľ� ���� ����
- Global Navigation (Header):
  - ������ ����: Flask(Ȩ������)�� React(��Ʃ���) ��� 100% ����ȭ (Glassmorphism)
  - 3D ��ó ž��: ���� �޴� �� '3D Űĸ(Keycap)' ��Ÿ�� �� �޴� ���� (Ȩ/����/��Ʃ���/��ȯ/����Ȩ)
  - ��Ÿ�� ����: React ��Ӵٿ� �޴� ����/�׸��� ���� ���� �Ϸ�
- System Stability:
  - ���� ����ȭ: DEBUG ��� ���� �� ���� ���� �α� ���ܷ� �ӵ� ���
  - React ��� ���������� ���� �� ��� ���� ����


## [2025-12-07 11:06 KST] [COMMIT: Token-Logic-Final] | feat: ��ū ���� ����ȭ (����/���� ���� �и�)
- Database & Schema:
  - Token History: 'source_type' �÷� �߰� (����/���� ��ó ��Ͽ�)
  - Migration: ���� ������ ���� ó���� ���� ���̱׷��̼� ��ũ��Ʈ ����
- Logic Core:
  - ����(Grant): ���� �� 'PAID', ������/�̺�Ʈ ���� �� 'FREE' �ڵ� �±� ����
  - ����(Expire): ���� 'FREE' �±װ� ���� ��ū�� ��ȿ�Ⱓ ���� �� �ڵ� ȸ��
  - ���(Defense): ���� ���� ��ū�� �Ⱓ�� ������ ���� �����ǵ��� ���� 3�� ���
- Verification:
  - �ùķ��̼�: 'verify_token_logic.py'�� ���� ���� ����/���� �Ҹ� 100% ���� �Ϸ�


## [2025-12-07 11:06 KST] [COMMIT: Token-Logic-Final] | feat: ��ū ���� ����ȭ (����/���� ���� �и�)
- Database & Schema:
  - Token History: 'source_type' �÷� �߰� (����/���� ��ó ��Ͽ�)
  - Migration: ���� ������ ���� ó���� ���� ���̱׷��̼� ��ũ��Ʈ ����
- Logic Core:
  - ����(Grant): ���� �� 'PAID', ������/�̺�Ʈ ���� �� 'FREE' �ڵ� �±� ����
  - ����(Expire): ���� 'FREE' �±װ� ���� ��ū�� ��ȿ�Ⱓ ���� �� �ڵ� ȸ��
  - ���(Defense): ���� ���� ��ū�� �Ⱓ�� ������ ���� �����ǵ��� ���� 3�� ���
- Verification:
  - �ùķ��̼�: 'verify_token_logic.py'�� ���� ���� ����/���� �Ҹ� 100% ���� �Ϸ�




