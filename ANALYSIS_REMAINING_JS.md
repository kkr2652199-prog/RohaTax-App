# admin.html 남은 JavaScript 코드 분석 및 분리 전략 보고서

## 📊 남은 함수 목록 (총 24개)

### 1. 유틸리티 함수 (1개)
- `csrfToken()` - CSRF 토큰 조회

### 2. 초기화 및 세션 관리 (2개)
- `checkAdminSession()` - 관리자 세션 확인
- `showDashboard()` - 대시보드 표시

### 3. 대시보드 새로고침 (2개)
- `refreshDashboard()` - 대시보드 전체 새로고침
- `toggleAutoRefresh()` - 자동 새로고침 토글

### 4. 사용자 관리 기능 (9개)
- `loadUsers()` - 사용자 목록 로드
- `renderUsers()` - 사용자 목록 렌더링
- `loadUserConversionHistory()` - 사용자별 변환 이력 로드
- `grantTokens()` - 토큰 지급
- `resetTokens()` - 토큰 초기화
- `approveUser()` - 사용자 승인
- `deleteUser()` - 사용자 삭제
- `restoreUser()` - 사용자 복구
- `purgeUser()` - 사용자 완전 삭제
- `changeUserPlan()` - 사용자 플랜 변경

### 5. 토큰 히스토리 기능 (1개)
- `loadTokenHistory()` - 비활성 사용자 목록 로드

### 6. 통계 기능 (2개)
- `loadStats()` - 통계 데이터 로드
- `updateStatsContent()` - 통계 콘텐츠 업데이트

### 7. 관리자 관리 기능 (3개)
- `loadAdminUsers()` - 관리자 사용자 목록 로드
- `loadAdminDashboardStats()` - 관리자 대시보드 통계 로드
- `updateAdminDashboardStats()` - 관리자 대시보드 통계 업데이트

### 8. 활동 로그 기능 (1개)
- `loadActivityLogs()` - 통합 관제실 활동 로그 로드

### 9. 이메일 인증 설정 기능 (3개)
- `loadEmailVerificationSettings()` - 이메일 인증 설정 로드
- `renderEmailVerificationSettings()` - 이메일 인증 설정 렌더링
- `saveEmailSettings()` - 이메일 설정 저장

---

## 🔗 함수 호출 관계도 (Call Graph)

```
[초기화 흐름]
checkAdminSession()
  └─> showDashboard()
  └─> loadUsers()
  └─> loadTokenHistory()
  └─> loadStats()
  └─> updateLastRefreshTime() (utils.js)

[대시보드 새로고침]
refreshDashboard()
  └─> loadUsers()
  └─> loadTokenHistory()
  └─> loadStats()
  └─> updateLastRefreshTime() (utils.js)

toggleAutoRefresh()
  └─> stopAutoRefresh() (utils.js)
  └─> startAutoRefresh() (utils.js)
  └─> updateRefreshButtonText() (utils.js)

[사용자 관리 모듈]
loadUsers()
  └─> renderUsers()
      └─> loadUserConversionHistory() (각 사용자마다)
          └─> downloadFile() (utils.js)

grantTokens()
  └─> loadUsers()

resetTokens()
  └─> loadUsers()

approveUser()
  └─> loadUsers()

deleteUser()
  └─> loadUsers()

restoreUser()
  └─> loadUsers()

purgeUser()
  └─> loadUsers()

changeUserPlan()
  └─> loadUsers()

[통계 모듈]
loadStats()
  └─> updateStatsContent()

[관리자 관리 모듈]
loadAdminUsers()
  (독립적)

loadAdminDashboardStats()
  └─> updateAdminDashboardStats()

[활동 로그 모듈]
loadActivityLogs()
  (독립적, 필터링 기능 포함)

[이메일 인증 설정 모듈]
loadEmailVerificationSettings()
  └─> renderEmailVerificationSettings()

saveEmailSettings()
  └─> loadEmailVerificationSettings()

[탭 클릭 이벤트 핸들러]
탭 클릭 시:
  - 'users' → loadUsers()
  - 'admin-management' → loadAdminUsers() + loadAdminDashboardStats()
  - 'token-history' → loadTokenHistory()
  - 'control-deck' → loadActivityLogs()
  - 'stats' → loadStats()
  - 'settings' → loadEmailVerificationSettings()
```

---

## 📦 함수 묶음(Module) 제안

### **1순위: 사용자 관리 모듈 (User Management Module)**
**파일명**: `static/js/admin/user_management.js`

**포함 함수 (10개)**:
- `loadUsers()`
- `renderUsers()`
- `loadUserConversionHistory()`
- `grantTokens()`
- `resetTokens()`
- `approveUser()`
- `deleteUser()`
- `restoreUser()`
- `purgeUser()`
- `changeUserPlan()`

**이유**:
1. **강한 응집도**: 모든 함수가 '사용자 관리'라는 단일 책임을 가짐
2. **명확한 호출 체인**: `loadUsers()` → `renderUsers()` → `loadUserConversionHistory()` 순서가 명확함
3. **높은 재사용성**: 사용자 관리 기능은 다른 관리자 페이지에서도 재사용 가능
4. **독립성**: 다른 모듈과의 의존성이 적음 (utils.js의 `downloadFile()`만 사용)
5. **안전성**: 이미 분리된 함수들과의 충돌 위험이 없음

**의존성**:
- `utils.js`의 `downloadFile()` 함수
- `csrfToken()` 함수 (공통 유틸리티로 분리 필요)

---

### **2순위: 대시보드 코어 모듈 (Dashboard Core Module)**
**파일명**: `static/js/admin/dashboard_core.js`

**포함 함수 (4개)**:
- `checkAdminSession()`
- `showDashboard()`
- `refreshDashboard()`
- `toggleAutoRefresh()`

**이유**:
1. **핵심 기능**: 대시보드의 초기화와 새로고침을 담당하는 핵심 로직
2. **명확한 역할**: 대시보드의 생명주기(lifecycle)를 관리
3. **다른 모듈 호출**: `refreshDashboard()`가 여러 모듈의 함수를 호출하는 중앙 허브 역할
4. **안전성**: 초기화 로직이므로 다른 모듈보다 먼저 로드되어야 함

**의존성**:
- `utils.js`의 `updateLastRefreshTime()`, `stopAutoRefresh()`, `startAutoRefresh()`, `updateRefreshButtonText()`
- 사용자 관리 모듈의 `loadUsers()`
- 토큰 히스토리 모듈의 `loadTokenHistory()`
- 통계 모듈의 `loadStats()`

---

### **3순위: 통계 모듈 (Statistics Module)**
**파일명**: `static/js/admin/statistics.js`

**포함 함수 (2개)**:
- `loadStats()`
- `updateStatsContent()`

**이유**:
1. **단순성**: 함수가 2개뿐이어서 분리하기 쉬움
2. **독립성**: 다른 모듈과의 의존성이 거의 없음
3. **명확한 책임**: 통계 데이터 로드와 렌더링만 담당

**의존성**:
- `csrfToken()` 함수

---

### **4순위: 관리자 관리 모듈 (Admin Management Module)**
**파일명**: `static/js/admin/admin_management.js`

**포함 함수 (3개)**:
- `loadAdminUsers()`
- `loadAdminDashboardStats()`
- `updateAdminDashboardStats()`

**이유**:
1. **응집도**: 관리자 계정 관리라는 단일 책임
2. **독립성**: 다른 사용자 관리와 분리되어 있음
3. **명확한 호출 체인**: `loadAdminDashboardStats()` → `updateAdminDashboardStats()`

**의존성**:
- `csrfToken()` 함수

---

### **5순위: 활동 로그 모듈 (Activity Logs Module)**
**파일명**: `static/js/admin/activity_logs.js`

**포함 함수 (1개)**:
- `loadActivityLogs()`

**이유**:
1. **복잡성**: 함수가 매우 크고 복잡함 (약 150줄)
2. **독립성**: 다른 모듈과의 의존성이 거의 없음
3. **필터링 기능**: 필터링 로직이 포함되어 있어 별도 모듈로 분리하면 유지보수 용이

**의존성**:
- `csrfToken()` 함수

---

### **6순위: 토큰 히스토리 모듈 (Token History Module)**
**파일명**: `static/js/admin/token_history.js`

**포함 함수 (1개)**:
- `loadTokenHistory()`

**이유**:
1. **단순성**: 함수가 1개뿐이어서 분리하기 쉬움
2. **독립성**: 다른 모듈과의 의존성이 거의 없음
3. **명확한 책임**: 비활성 사용자 목록만 관리

**의존성**:
- `csrfToken()` 함수
- 사용자 관리 모듈의 `restoreUser()`, `purgeUser()` (이미 전역 함수로 선언되어 있으므로 문제없음)

---

### **7순위: 이메일 인증 설정 모듈 (Email Verification Settings Module)**
**파일명**: `static/js/admin/email_settings.js`

**포함 함수 (3개)**:
- `loadEmailVerificationSettings()`
- `renderEmailVerificationSettings()`
- `saveEmailSettings()`

**이유**:
1. **응집도**: 이메일 인증 설정이라는 단일 책임
2. **명확한 호출 체인**: `loadEmailVerificationSettings()` → `renderEmailVerificationSettings()`, `saveEmailSettings()` → `loadEmailVerificationSettings()`
3. **독립성**: 다른 모듈과의 의존성이 거의 없음

**의존성**:
- `csrfToken()` 함수
- `utils.js`의 `toggleEmailVerification()` 함수

---

### **공통 유틸리티 분리 필요**
**파일명**: `static/js/admin/common.js` (또는 `utils.js`에 추가)

**포함 함수 (1개)**:
- `csrfToken()`

**이유**:
- 거의 모든 모듈에서 사용하는 공통 함수이므로 별도 파일로 분리하거나 `utils.js`에 추가해야 함

---

## 🎯 최종 분리 우선순위 및 전략

### **Phase 1: 사용자 관리 모듈 분리 (1순위)**
**이유**: 가장 큰 묶음이며, 명확한 호출 체인을 가지고 있어 분리 효과가 큼

**작업 순서**:
1. `static/js/admin/user_management.js` 파일 생성
2. 10개 함수를 모두 이동
3. `utils.js`의 `downloadFile()` 의존성 확인
4. `csrfToken()` 함수는 공통 유틸리티로 분리하거나 전역 함수로 유지
5. `admin.html`에서 새 모듈 로드
6. 기능 검증 및 커밋

---

### **Phase 2: 공통 유틸리티 분리 (선행 작업)**
**이유**: 다른 모듈들이 `csrfToken()`을 사용하므로 먼저 분리해야 함

**작업 순서**:
1. `utils.js`에 `csrfToken()` 함수 추가 (또는 `common.js` 생성)
2. `admin.html`에서 `csrfToken()` 정의 제거
3. 모든 함수에서 `csrfToken()` 호출이 정상 작동하는지 확인
4. 기능 검증 및 커밋

---

### **Phase 3: 대시보드 코어 모듈 분리 (2순위)**
**이유**: 다른 모듈들을 호출하는 중앙 허브 역할이므로, 사용자 관리 모듈 분리 후 진행

**작업 순서**:
1. `static/js/admin/dashboard_core.js` 파일 생성
2. 4개 함수 이동
3. 다른 모듈들의 함수 호출 경로 확인
4. 기능 검증 및 커밋

---

### **Phase 4: 나머지 모듈들 순차 분리 (3~7순위)**
**이유**: 각 모듈이 독립적이므로 순서는 중요하지 않지만, 복잡도가 낮은 것부터 진행

**권장 순서**:
1. 통계 모듈 (2개 함수, 단순)
2. 토큰 히스토리 모듈 (1개 함수, 단순)
3. 관리자 관리 모듈 (3개 함수, 중간)
4. 이메일 인증 설정 모듈 (3개 함수, 중간)
5. 활동 로그 모듈 (1개 함수, 복잡)

---

## 📋 분리 시 주의사항

### 1. 전역 함수 선언
- `onclick` 속성에서 직접 호출되는 함수들(`grantTokens`, `resetTokens` 등)은 전역 스코프에 있어야 함
- 해결책: `window` 객체에 명시적으로 할당 (`window.grantTokens = grantTokens`)

### 2. 이벤트 리스너
- `DOMContentLoaded` 이벤트 내부의 코드는 모듈 로드 후 실행되어야 함
- 해결책: 각 모듈의 초기화 함수를 `admin.html`에서 호출

### 3. 탭 클릭 이벤트 핸들러
- 탭 클릭 시 각 모듈의 함수를 호출하는 로직이 `admin.html`에 남아있음
- 해결책: 이벤트 핸들러는 `admin.html`에 유지하되, 함수 호출만 모듈로 위임

### 4. 의존성 순서
- 스크립트 로드 순서가 중요함: `common.js` → `utils.js` → 각 모듈 → `admin.html` 인라인 스크립트

---

## ✅ 결론

**다음 단계**: **Phase 1 (사용자 관리 모듈 분리)**부터 시작하는 것을 강력히 권장합니다.

이유:
1. 가장 큰 묶음이므로 분리 효과가 가장 큼
2. 명확한 호출 체인으로 분리 시 부작용이 적음
3. 다른 모듈들의 기반이 되는 핵심 기능
4. 분리 후 `admin.html`의 코드가 크게 줄어듦 (약 500줄 감소 예상)


