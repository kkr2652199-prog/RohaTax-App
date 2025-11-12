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

