# 작업 커밋 로그 (The Roha Way)



이 문서는 프로젝트의 모든 주요 변경 사항을 기록하는 항해 일지입니다. 모든 커밋은 Conventional Commits 규칙을 따르며, 커밋 직후 이곳에 기록됩니다.



---

### 2025-11-14 12:29:11 KST

**[5aa2e36] refactor(user): user_info API를 확장 버전으로 통합**

- **수정 파일:** `routes/conversion_modules/user_routes.py`, `routes/conversion.py`, `app.py`

- **핵심 내용:** 분산되어 있던 `user_info` 함수를 18개 필드를 반환하는 확장 버전으로 통합하고 중앙화하여, 시스템 전체의 데이터 일관성을 확보함.

---

### 2025-11-14 11:36:59 (KST)

- **[f879301] refactor(conversion): 페이지 렌더링 로직을 page_routes.py로 분리**

  - **수정 파일:** `routes/conversion.py`, `routes/conversion_modules/page_routes.py`, `app.py`

  - **핵심 내용:** `conversion.py`에 남아있던 유일한 페이지 렌더링 함수인 `conversion()`을 독립적인 모듈로 분리함. 약 15줄 감소.

  - 단일 책임 원칙을 강화하고, `conversion.py`가 순수 API 라우트 역할에 집중하도록 구조를 개선함.

  - 새로운 `page_bp` Blueprint를 생성하고 `app.py`에 등록하여 시스템 통합 완료.

### 2025-11-14 11:30:00 (KST)

- **[aba911a] fix(conversion): 219줄의 실행 불가능한 데드 코드 제거**

  - **수정 파일:** `routes/conversion.py`

  - **핵심 내용:** `download_converted()` 함수 정상 종료(return) 이후에 위치하여 절대 실행될 수 없는 코드 블록을 완전히 삭제함. 약 219줄 감소.

  - 코드의 가독성을 높이고 파일 크기를 즉시 감소시킴.

### 2025-11-14 11:19:27 (KST)

- **[f066749] refactor(conversion): 절대지침 검증 모듈 분리**

  - **수정 파일:** `routes/conversion.py`, `app.py`, `routes/conversion_modules/guideline_routes.py`

  - **핵심 내용:** `conversion.py`의 절대지침 관련 2개 함수를 중앙 모듈로 이전하여 중복 제거. 약 50줄 감소.

  - routes/conversion.py에 중복으로 존재하던 절대지침 관련 2개 함수(validate_template_data, get_guidelines_version)를 제거함.

  - 이를 중앙화된 guideline 모듈을 사용하도록 변경하여, 코드 중복을 해소하고 책임 분리 원칙을 강화함.

  - '인간 검증'을 통해 기능적 회귀가 없음을 확인함.

### 2025-11-13 20:14:48 (KST)

- **[1987c6b] refactor(route): conversion.py 보안 모듈 책임 분리 및 Blueprint 등록**

  - **수정 파일:** `routes/conversion.py`, `app.py`

  - **핵심 내용:** `conversion.py`의 보안 관련 함수를 제거하고, 누락되었던 `security_bp`를 `app.py`에 등록하여 버그 수정.

  - conversion.py가 가지고 있던 보안 관련 4개 함수를 제거하고, security_routes에서 import하도록 변경함.

  - 분리 과정에서 발견된, app.py에 security_bp가 등록되지 않았던 버그를 수정함.

  - '하나의 파일, 하나의 책임' 원칙을 준수하고 시스템 안정성을 향상시킴.

  - 기능적 회귀가 없음을 '인간 검증'으로 확인함.

### 2025-11-13 19:47:44 (KST)

- **[591e6a0] refactor(route): conversion.py의 템플릿 관리 책임 분리**

  - **수정 파일:** `routes/conversion.py`

  - **핵심 내용:** `conversion.py`의 템플릿 관련 4개 함수를 제거하고, `template_routes`에서 import 하도록 변경.

  - conversion.py가 부당하게 가지고 있던 템플릿 관리 관련 4개 함수를 제거함.

  - 원래 책임을 담당하던 template_routes 모듈을 import하여 사용하도록 변경함.

  - '하나의 파일, 하나의 책임' 원칙에 따라 리팩토링을 진행함.

  - 기능적 회귀가 없음을 '인간 검증'으로 확인함.

### 2025-01-12

- **[afc153e] refactor(token): 토큰 잔액 조회 로직을 token_service로 통합**

  - **수정 파일:** `routes/conversion.py`, `core/token_service.py`

  - **핵심 내용:** `conversion.py`의 중복 쿼리를 `token_service.get_user_token_status()`로 통합하여 중앙화.

  - routes/conversion.py에 중복으로 존재하던 토큰 잔액 조회 쿼리를 core/token_service.py의 get_user_token_status() 함수로 중앙화함.

  - 코드 중복을 제거하고, 토큰 관련 비즈니스 로직의 책임을 분리함.

  - 기능적 회귀가 없음을 '인간 검증'으로 확인함.

- **[da182af] refactor(core): _row_value 함수를 core.utils로 통합하여 중복 제거**

  - 6개의 다른 파일에 중복으로 정의되어 있던 _row_value 헬퍼 함수를 core/utils.py의 row_value 함수로 통합함.
  - 코드 중복을 제거하고 중앙에서 관리하도록 하여 유지보수성을 향상시킴.
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함.

### 2025-01-12

- **[829a516] docs(tracking): 작업 로그 파일 COMMIT_LOG.md 추가**

  - 프로젝트의 모든 변경 이력을 체계적으로 관리하고 추적하기 위해 COMMIT_LOG.md 파일을 도입.

- **[dc911ff] fix: 토큰 사용량 계산 오류 및 변환 페이지 토큰 상태 표시 수정**

  - TOKEN_RESET_BY_ADMIN의 token_change를 사용량 계산에서 제외하여 정확한 토큰 사용량 표시
  - 변환 페이지에서 activity_logs 기반 정확한 토큰 정보를 표시하도록 API 변경
  - 마이홈 및 관리자 페이지에서 토큰 리셋 시 올바른 잔액 표시 로직 추가
  - 토큰 상태 카드의 초기값을 동적으로 로드하여 서버 사이드 렌더링 오류 방지

- **[250d726] docs(analysis): homepage.css 영향 범위 분석 보고서 생성**

  - 리팩토링 Phase 1의 첫 단계로, homepage.css의 영향 범위를 정밀 분석함
  - 총 219개의 선택자 중 145개가 homepage.html 전용임을 확인
  - 68개의 미사용 선택자(dead code)를 식별함
  - 이 분석 결과를 바탕으로, 가장 안전한 'homepage.html 전용 스타일 분리' 전략을 수립할 수 있게 됨

- **[fb74b46] refactor(css): homepage.html 스타일 분리를 위한 준비 작업 완료**

  - homepage.css의 백업 파일(homepage.css.backup) 생성
  - homepage.html 전용 선택자 145개가 포함된 목록 파일(homepage_specific_selectors.txt) 생성
  - 실제 CSS 파일 수정 없이, 다음 단계인 '스타일 추출'을 위한 도구 준비 완료

- **[2ec9e34] refactor(css): homepage.html 전용 스타일 파일 생성 및 복제**

  - homepage.html 전용 스타일 145개를 담을 homepage_specific.css 파일을 생성함
  - 원본 homepage.css에서 관련 스타일 블록을 모두 '복사'하여 구문 검증까지 완료
  - 이 단계까지 원본 homepage.css는 전혀 수정되지 않았으며, 100% 안전한 상태임

- **[7a219d1] refactor(css): homepage.html에 분리된 CSS 파일 연결**

  - homepage.html에 새로 생성된 homepage_specific.css 파일을 연결함
  - 현재 상태는 원본과 복제본 CSS를 모두 로드하는 중복 상태
  - 서버 환경에서 시각적 변화가 없음을 '인간 검증'으로 확인함
  - 다음 단계인 '원본 스타일 제거'를 위한 안전한 발판을 마련함

- **[09eb853] refactor(css): 원본 homepage.css에서 중복 스타일 제거**

  - homepage.html 전용 스타일 145개 및 관련 규칙을 homepage.css에서 모두 제거함
  - 파일 크기가 약 3,800줄에서 약 1,800줄로 크게 감소함
  - 6개의 공통 스타일은 안전하게 보존됨
  - '강제 검증'을 통해 시각적 회귀(visual regression)가 없음을 최종 확인함

- **[c74c722] chore(refactor): 리팩토링 임시 파일 및 백업 제거**

  - homepage.css 분리 작업이 성공적으로 완료됨에 따라, 임무를 완수한 임시 파일 및 백업 파일들을 모두 제거함
  - 삭제 파일: homepage.css.backup, homepage_specific_selectors.txt 등
  - 이 커밋을 끝으로 'refactor/css-split' 브랜치의 모든 작업이 완료됨

- **[8082243] refactor(html): admin.html의 헤더 영역을 partial 파일로 분리**

  - admin.html 리팩토링의 첫 단계로, 관리자 헤더 영역을 독립적인 partial 파일(_header.html)로 분리함
  - admin.html 본문은 {% include %} 문으로 대체되어 가독성이 향상됨
  - 시각적 회귀 및 기능 이상이 없음을 '인간 검증'으로 확인함

- **[5dc7211] refactor(html): admin.html의 실시간 업데이트 인디케이터 분리**

  - admin.html의 두 번째 리팩토링 단계로, 실시간 업데이트 인디케이터를 partial 파일(_live_indicator.html)로 분리함
  - admin.html의 가독성을 추가로 개선하고 컴포넌트화를 진행함
  - 시각적 회귀 및 기능 이상이 없음을 '인간 검증'으로 확인함

- **[fefb66c] refactor(html): admin.html의 탭 네비게이션 분리**

  - admin.html의 세 번째 리팩토링 단계로, 탭 네비게이션 영역을 partial 파일(_tabs.html)로 분리함
  - 가독성을 높이고 컴포넌트화를 지속적으로 진행함
  - 시각적 및 기능적(탭 전환) 회귀가 없음을 '인간 검증'으로 확인함

- **[7d6bb07] refactor(html): admin.html의 사용자 목록 테이블 분리**

  - admin.html의 네 번째 리팩토링 단계로, 핵심 기능인 사용자 목록 테이블 영역을 partial 파일(_user_list_table.html)로 분리함
  - 동적 데이터 렌더링 영역의 컴포넌트화를 통해 향후 JavaScript 분리의 기반을 마련함
  - 시각적 및 기능적(버튼 액션) 회귀가 없음을 '인간 검증'으로 확인함

- **[f87c237] refactor(html): admin.html의 통계 카드 섹션 분리**

  - admin.html의 다섯 번째 리팩토링 단계로, '시스템 관리자 관리' 탭의 통계 카드 섹션을 partial 파일(_stat_cards.html)로 분리함
  - admin.html의 구조를 지속적으로 단순화하고 컴포넌트화를 진행함
  - 시각적 회귀가 없음을 '인간 검증'으로 확인함

- **[66521e6] refactor(html): admin.html의 관리자 계정 목록 분리**

  - admin.html의 여섯 번째 리팩토링 단계로, '관리자 계정 목록' 테이블을 partial 파일(_admin_list_table.html)로 분리함
  - admin.html의 HTML 구조 분리 작업을 거의 마무리함
  - 시각적 회귀가 없음을 '인간 검증'으로 확인함

- **[d1e5b09] refactor(css): admin.html의 인라인 CSS를 admin.css 파일로 분리**

  - admin.html 내부에 존재하던 약 600줄의 인라인 CSS를 독립된 admin.css 파일로 완전히 분리함
  - 구조(HTML)와 디자인(CSS)의 책임을 명확하게 분리하여 유지보수성을 크게 향상시킴
  - 시각적 회귀가 없음을 '인간 검증'으로 확인함

- **[5c0495c] refactor(js): admin.html의 첫 번째 JS 함수(updateLastRefreshTime) 분리**

  - admin.html 리팩토링의 마지막 단계인 JavaScript 분리를 시작함
  - 첫 번째 단계로, 가장 독립적이고 안전한 유틸리티 함수인 updateLastRefreshTime()을 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[6e91f31] refactor(js): admin.html의 JS 함수(downloadFile) 분리**

  - JS 분리 리팩토링의 두 번째 단계로, 유틸리티 함수인 downloadFile()을 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀 및 부작용이 없음을 '인간 검증'으로 확인함

- **[d0f7160] refactor(js): admin.html의 JS 함수(updateRefreshButtonText) 분리**

  - JS 분리 리팩토링의 세 번째 단계로, DOM을 조작하는 유틸리티 함수인 updateRefreshButtonText()를 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[a05bcf7] refactor(js): admin.html의 JS 함수(logout) 분리**

  - JS 분리 리팩토링의 네 번째 단계로, 인증 관련 함수인 logout()을 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[fc94197] refactor(js): admin.html의 JS 함수(toggleEmailVerification) 분리**

  - JS 분리 리팩토링의 다섯 번째 단계로, '설정' 탭의 UI와 상호작용하는 toggleEmailVerification() 함수를 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[69f2111] refactor(js): admin.html의 JS 함수(stopAutoRefresh) 분리**

  - JS 분리 리팩토링의 여섯 번째 단계로, 전역 변수(autoRefreshInterval)에 의존하는 stopAutoRefresh() 함수를 static/js/admin/utils.js 파일로 분리함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[9184796] refactor(js): admin.html의 JS 함수(startAutoRefresh) 분리**

  - JS 분리 리팩토링의 일곱 번째 단계로, 다른 함수(loadUsers, updateLastRefreshTime)를 호출하는 startAutoRefresh() 함수를 static/js/admin/utils.js 파일로 분리함
  - 외부 파일에서 인라인 스크립트의 함수를 호출하는 의존성 문제를 성공적으로 해결함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[5fd2701] refactor(js): admin.html의 사용자 관리 모듈(10개 함수) 분리**

  - JS 분리 리팩토링의 핵심 단계로, 사용자 관리와 관련된 10개의 함수를 user_management.js 파일로 모듈화함
  - admin.html 파일의 크기를 약 500줄 감소시키고, 기능별 책임 분리를 달성함
  - 모든 관련 기능(CRUD, 토큰 관리 등)에 대한 회귀가 없음을 '인간 검증'으로 확인함

- **[00470d9] refactor(js): admin.html의 대시보드 코어 모듈(4개 함수) 분리**

  - JS 분리 리팩토링의 핵심 단계로, 페이지 초기화 및 새로고침 관련 4개 함수를 dashboard_core.js 파일로 모듈화함
  - admin.html 파일의 핵심 로직을 분리하여 유지보수성을 크게 향상시킴
  - 모든 관련 기능(초기 로드, 새로고침)에 대한 회귀가 없음을 '인간 검증'으로 확인함

- **[348ae3f] refactor(js): admin.html의 통계 모듈(2개 함수) 분리**

  - JS 분리 리팩토링의 일환으로, '통계' 탭 관련 2개 함수를 stats.js 파일로 모듈화함
  - 기능별 책임 분리를 지속적으로 진행하여 유지보수성을 향상시킴
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[aebe470] refactor(js): admin.html의 토큰 히스토리 모듈 분리**

  - JS 분리 리팩토링의 일환으로, '비활성 사용자' 탭 관련 함수(loadTokenHistory)를 token_history.js 파일로 모듈화함
  - 기능별 책임 분리를 지속적으로 진행함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[c84456c] refactor(js): admin.html의 관리자 관리 모듈 분리 및 개선**

  - JS 분리 리팩토링의 일환으로, '관리자 관리' 관련 3개 함수를 admin_management.js 파일로 모듈화함
  - 분리 과정에서 발견된 중복 코드를 제거하여 파일 크기를 50% 감소시키고 코드 품질을 향상시킴
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[268a5c0] refactor(js): admin.html의 활동 로그 모듈 분리**

  - JS 분리 리팩토링의 일환으로, '통합 관제실' 관련 함수(loadActivityLogs)를 activity_log.js 파일로 모듈화함
  - 기능별 책임 분리를 지속적으로 진행함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

- **[e8230b4] refactor(js): admin.html의 이메일 인증 설정 모듈 분리 및 버그 수정**

  - JS 분리 리팩토링의 일환으로, '설정' 탭 관련 3개 함수를 email_settings.js 파일로 모듈화함
  - 분리 과정에서 발견된 '비활성화 저장 불가' 버그를 수정함. (원인: unchecked checkbox가 FormData에 포함되지 않음)
  - .checked 속성을 명시적으로 확인하여 '1'/'0' 값을 전송하도록 로직을 개선함
  - 기능적 회귀가 없음을 '인간 검증'으로 확인함

