# 작업 커밋 로그 (The Roha Way)



이 문서는 프로젝트의 모든 주요 변경 사항을 기록하는 항해 일지입니다. 모든 커밋은 Conventional Commits 규칙을 따르며, 커밋 직후 이곳에 기록됩니다.



---

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

