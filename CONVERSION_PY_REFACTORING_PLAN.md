# routes/conversion.py 리팩토링 계획서

## 📊 현재 상태 분석

### 파일 크기
- **routes/conversion.py**: 1,232줄 (목표: 500줄 이하)
- **기존 모듈들**: 총 1,631줄 (8개 파일)

### 현재 함수 목록 (16개 라우트 + 1개 헬퍼)

| 라인 | 함수명 | 엔드포인트 | 기능 분류 |
|------|--------|-----------|----------|
| 39 | `_calculate_template_count_precisely` | - | 헬퍼 함수 |
| 117 | `conversion()` | `/conversion` | 페이지 렌더링 |
| 134 | `use_token()` | `/api/use-token` | 토큰 관리 |
| 177 | `token_status()` | `/api/token-status` | 토큰 관리 |
| 207 | `user_info()` | `/api/user-info` | 사용자 정보 |
| 259 | `get_templates()` | `/api/templates` | 템플릿 관리 |
| 273 | `get_template_info()` | `/api/templates/<id>` | 템플릿 관리 |
| 290 | `validate_template()` | `/api/templates/<id>/validate` | 템플릿 관리 |
| 310 | `upload_template()` | `/api/templates/upload` | 템플릿 관리 |
| 373 | `validate_template_data()` | `/api/validate-template-data` | 절대지침 검증 |
| 408 | `get_guidelines_version()` | `/api/guidelines/version` | 절대지침 검증 |
| 422 | `get_security_status()` | `/api/security/status` | 보안 시스템 |
| 450 | `get_notifications()` | `/api/security/notifications` | 보안 시스템 |
| 479 | `mark_notification_read()` | `/api/security/notifications/<id>/read` | 보안 시스템 |
| 495 | `start_conversion()` | `/api/convert/start` | 변환 실행 (핵심) |
| 909 | `download_converted()` | `/api/convert/download` | 다운로드 |
| 1205 | `test_file_validation()` | `/api/security/validation/test` | 보안 시스템 |

---

## 🎯 기능 단위 분석 및 모듈 그룹화

### 그룹 1: 페이지 렌더링 모듈
**함수**: `conversion()` (라인 117-130)
- **기능**: 변환 페이지 렌더링
- **의존성**: 낮음 (템플릿 렌더링만)
- **분리 난이도**: ⭐ (매우 쉬움)
- **제안 파일**: `routes/conversion_modules/page_routes.py` (신규 생성)

### 그룹 2: 토큰 관리 모듈 (이미 부분 분리됨)
**함수**: 
- `use_token()` (라인 134-173)
- `token_status()` (라인 177-200)

**현재 상태**: 
- `routes/conversion_modules/token_routes.py`에 이미 유사한 함수들이 존재
- 하지만 `conversion.py`에도 중복으로 존재

**분리 전략**: 
- `conversion.py`의 함수들을 `token_routes.py`로 이동하거나 통합
- 또는 `token_routes.py`의 함수들을 `conversion.py`에서 제거하고 import로 대체

**의존성**: 중간 (token_service 사용)
**분리 난이도**: ⭐⭐ (쉬움)

### 그룹 3: 사용자 정보 모듈 (이미 부분 분리됨)
**함수**: `user_info()` (라인 207-255)

**현재 상태**: 
- `routes/conversion_modules/user_routes.py`에 이미 `user_info()` 함수 존재
- `conversion.py`의 함수가 더 상세한 정보를 반환 (더 많은 필드)

**분리 전략**: 
- `conversion.py`의 함수를 `user_routes.py`로 이동
- 또는 두 함수를 통합하여 더 완전한 버전으로 통일

**의존성**: 낮음
**분리 난이도**: ⭐⭐ (쉬움)

### 그룹 4: 템플릿 관리 모듈 (이미 부분 분리됨)
**함수**: 
- `get_templates()` (라인 259-269)
- `get_template_info()` (라인 273-286)
- `validate_template()` (라인 290-306)
- `upload_template()` (라인 310-369)

**현재 상태**: 
- `routes/conversion_modules/template_routes.py`에 이미 동일한 함수들이 존재
- `conversion.py`의 함수들은 중복

**분리 전략**: 
- `conversion.py`에서 이 4개 함수를 모두 삭제
- `template_routes.py`의 함수들을 import하여 사용

**의존성**: 낮음 (template_manager 사용)
**분리 난이도**: ⭐ (매우 쉬움)

### 그룹 5: 절대지침 검증 모듈 (이미 부분 분리됨)
**함수**: 
- `validate_template_data()` (라인 373-404)
- `get_guidelines_version()` (라인 408-418)

**현재 상태**: 
- `routes/conversion_modules/security_routes.py`에 이미 `get_guidelines_version()` 존재
- `validate_template_data()`는 `template_routes.py`에 존재

**분리 전략**: 
- `get_guidelines_version()`: `conversion.py`에서 삭제, `security_routes.py` 사용
- `validate_template_data()`: `conversion.py`에서 삭제, `template_routes.py` 사용

**의존성**: 낮음
**분리 난이도**: ⭐ (매우 쉬움)

### 그룹 6: 보안 시스템 모듈 (이미 부분 분리됨)
**함수**: 
- `get_security_status()` (라인 422-446)
- `get_notifications()` (라인 450-475)
- `mark_notification_read()` (라인 479-490)
- `test_file_validation()` (라인 1205-1230)

**현재 상태**: 
- `routes/conversion_modules/security_routes.py`에 이미 동일한 함수들이 존재
- `conversion.py`의 함수들은 중복

**분리 전략**: 
- `conversion.py`에서 이 4개 함수를 모두 삭제
- `security_routes.py`의 함수들을 import하여 사용

**의존성**: 낮음
**분리 난이도**: ⭐ (매우 쉬움)

### 그룹 7: 변환 실행 모듈 (핵심, 가장 복잡)
**함수**: 
- `start_conversion()` (라인 495-905) - **약 410줄**
- `download_converted()` (라인 909-985) - **약 76줄**
- `_calculate_template_count_precisely()` (라인 39-113) - **약 75줄**

**현재 상태**: 
- `routes/conversion_modules/convert_routes.py`에 이미 `start_conversion()`과 `download_converted_file()` 존재
- 하지만 `conversion.py`의 함수가 더 최신 버전일 가능성 (토큰 계산 로직 등)

**분리 난이도**: ⭐⭐⭐⭐ (어려움)
- 가장 큰 함수 (410줄)
- 복잡한 비즈니스 로직 포함
- 많은 의존성 (ConversionEngine, TokenDeductionProcessor, activity_service 등)
- 골드 회원 처리 로직 포함

**분리 전략**: 
- `start_conversion()`을 `convert_routes.py`로 이동하되, 최신 로직 유지
- `download_converted()`를 `convert_routes.py`로 이동
- `_calculate_template_count_precisely()`를 헬퍼 함수로 `core/` 폴더로 이동하거나 `convert_routes.py`에 포함

---

## 📁 제안된 파일 구조

### 기존 구조 (유지)
```
routes/
├── conversion.py (현재 1,232줄 → 목표: 200줄 이하)
└── conversion_modules/
    ├── conversion_processor.py (247줄)
    ├── convert_routes.py (262줄) ← 변환 실행 로직 이동 대상
    ├── gold_customers_routes.py (330줄)
    ├── main_routes.py (214줄)
    ├── security_routes.py (133줄)
    ├── template_routes.py (155줄)
    ├── token_routes.py (199줄)
    └── user_routes.py (91줄)
```

### 신규 생성 필요 파일
```
routes/conversion_modules/
└── page_routes.py (신규) ← 페이지 렌더링 전용
```

### 수정 필요 파일
```
routes/conversion.py
├── conversion() → page_routes.py로 이동
├── use_token(), token_status() → token_routes.py로 이동 또는 삭제
├── user_info() → user_routes.py로 이동 또는 삭제
├── get_templates(), get_template_info(), validate_template(), upload_template() → 삭제 (template_routes.py 사용)
├── validate_template_data(), get_guidelines_version() → 삭제 (기존 모듈 사용)
├── get_security_status(), get_notifications(), mark_notification_read(), test_file_validation() → 삭제 (security_routes.py 사용)
└── start_conversion(), download_converted(), _calculate_template_count_precisely() → convert_routes.py로 이동
```

---

## 🎯 첫 번째 분리 대상 우선순위

### 1순위: 템플릿 관리 모듈 (4개 함수) ⭐⭐⭐⭐⭐
**이유**:
- ✅ **가장 안전**: 이미 `template_routes.py`에 동일한 함수들이 존재
- ✅ **의존성 최소**: `template_manager`만 사용, 다른 함수와 독립적
- ✅ **즉시 효과**: 4개 함수 삭제로 약 110줄 감소
- ✅ **검증 용이**: 기능이 명확하고 테스트하기 쉬움

**작업 내용**:
1. `conversion.py`에서 4개 함수 삭제
2. `template_routes.py`의 함수들을 `conversion.py`에서 import
3. Blueprint 등록 확인

**예상 감소**: 약 110줄

---

### 2순위: 보안 시스템 모듈 (4개 함수) ⭐⭐⭐⭐
**이유**:
- ✅ **안전**: 이미 `security_routes.py`에 동일한 함수들이 존재
- ✅ **의존성 낮음**: 보안 관련 기능만 사용
- ✅ **효과적**: 4개 함수 삭제로 약 110줄 감소
- ⚠️ **주의**: 관리자 권한 체크 로직 확인 필요

**작업 내용**:
1. `conversion.py`에서 4개 함수 삭제
2. `security_routes.py`의 함수들을 `conversion.py`에서 import
3. Blueprint 등록 확인

**예상 감소**: 약 110줄

---

### 3순위: 절대지침 검증 모듈 (2개 함수) ⭐⭐⭐⭐
**이유**:
- ✅ **안전**: 이미 다른 모듈에 존재
- ✅ **의존성 낮음**: `absolute_guidelines`만 사용
- ✅ **효과적**: 2개 함수 삭제로 약 50줄 감소

**작업 내용**:
1. `get_guidelines_version()` 삭제 → `security_routes.py` 사용
2. `validate_template_data()` 삭제 → `template_routes.py` 사용

**예상 감소**: 약 50줄

---

### 4순위: 페이지 렌더링 모듈 (1개 함수) ⭐⭐⭐
**이유**:
- ✅ **독립적**: 다른 함수와 의존성 없음
- ✅ **간단**: 약 14줄의 단순한 함수
- ⚠️ **주의**: `conversion.html` 템플릿 경로 확인 필요

**작업 내용**:
1. `page_routes.py` 신규 생성
2. `conversion()` 함수 이동
3. Blueprint 등록

**예상 감소**: 약 14줄

---

### 5순위: 토큰 관리 모듈 (2개 함수) ⭐⭐⭐
**이유**:
- ⚠️ **중복 확인 필요**: `token_routes.py`와 기능 비교 필요
- ✅ **의존성 낮음**: `token_service` 사용 (이미 통합됨)
- ✅ **효과적**: 2개 함수 이동으로 약 70줄 감소

**작업 내용**:
1. `token_routes.py`와 함수 비교
2. 더 완전한 버전 선택 또는 통합
3. `conversion.py`에서 삭제 또는 이동

**예상 감소**: 약 70줄

---

### 6순위: 사용자 정보 모듈 (1개 함수) ⭐⭐⭐
**이유**:
- ⚠️ **중복 확인 필요**: `user_routes.py`와 기능 비교 필요
- ✅ **의존성 낮음**: 단순 조회 함수
- ✅ **효과적**: 1개 함수 이동으로 약 50줄 감소

**작업 내용**:
1. `user_routes.py`와 함수 비교
2. 더 완전한 버전 선택 또는 통합
3. `conversion.py`에서 삭제 또는 이동

**예상 감소**: 약 50줄

---

### 7순위: 변환 실행 모듈 (3개 함수) ⭐⭐
**이유**:
- ❌ **복잡도 높음**: `start_conversion()`이 410줄로 가장 큰 함수
- ❌ **의존성 많음**: ConversionEngine, TokenDeductionProcessor, activity_service 등
- ❌ **비즈니스 로직 복잡**: 골드 회원 처리, 토큰 계산, 파일 처리 등
- ⚠️ **주의**: `convert_routes.py`와 버전 차이 확인 필요

**작업 내용**:
1. `convert_routes.py`의 `start_conversion()`과 비교
2. 최신 로직을 `convert_routes.py`로 이동
3. `download_converted()` 이동
4. `_calculate_template_count_precisely()` 헬퍼 함수 처리

**예상 감소**: 약 560줄 (가장 큰 효과이지만 가장 위험)

---

## 📋 최종 분리 계획 요약

### Phase 1: 안전한 중복 제거 (즉시 실행 가능)
1. **템플릿 관리 모듈** (4개 함수 삭제) → 약 110줄 감소
2. **보안 시스템 모듈** (4개 함수 삭제) → 약 110줄 감소
3. **절대지침 검증 모듈** (2개 함수 삭제) → 약 50줄 감소

**총 감소**: 약 270줄 (1,232줄 → 962줄)

### Phase 2: 독립적 함수 이동
4. **페이지 렌더링 모듈** (1개 함수 이동) → 약 14줄 감소
5. **토큰 관리 모듈** (2개 함수 이동/통합) → 약 70줄 감소
6. **사용자 정보 모듈** (1개 함수 이동/통합) → 약 50줄 감소

**총 감소**: 약 134줄 (962줄 → 828줄)

### Phase 3: 핵심 변환 로직 이동 (신중한 접근 필요)
7. **변환 실행 모듈** (3개 함수 이동) → 약 560줄 감소

**최종 목표**: 약 268줄 (목표 500줄 이하 달성)

---

## 🎯 첫 번째 분리 대상 최종 제안

### **1순위: 템플릿 관리 모듈 (4개 함수)**

**이유**:
1. **가장 안전**: 이미 `template_routes.py`에 동일한 함수들이 존재하여 중복 제거만 하면 됨
2. **의존성 최소**: 다른 함수와 독립적이며, `template_manager`만 사용
3. **즉시 효과**: 4개 함수 삭제로 약 110줄 감소 (약 9% 감소)
4. **검증 용이**: 기능이 명확하고 테스트하기 쉬움
5. **부작용 없음**: 다른 함수와의 호출 관계가 없음

**작업 단계**:
1. `template_routes.py`의 함수들이 `conversion.py`에서 사용 가능한지 확인
2. `conversion.py`에서 4개 함수 삭제
3. 필요한 경우 Blueprint import 추가
4. 기능 검증

**예상 소요 시간**: 30분
**위험도**: 매우 낮음 (⭐⭐⭐⭐⭐)

---

## ⚠️ 주의사항

1. **Blueprint 등록 확인**: 각 모듈의 Blueprint가 `app.py`에 등록되어 있는지 확인 필요
2. **중복 함수 버전 확인**: 기존 모듈의 함수와 `conversion.py`의 함수 중 더 완전한 버전 선택
3. **의존성 체크**: 함수 이동 시 import 문 수정 필요
4. **테스트 필수**: 각 Phase마다 기능 검증 필수

---

## 📊 예상 결과

### 최종 목표
- **현재**: 1,232줄
- **Phase 1 후**: 962줄 (270줄 감소)
- **Phase 2 후**: 828줄 (134줄 감소)
- **Phase 3 후**: 268줄 (560줄 감소)
- **목표 달성**: ✅ 500줄 이하 (268줄)

### 파일 분산
- `conversion.py`: 268줄 (핵심 통합 로직만)
- `conversion_modules/`: 각 모듈별로 기능 분산

---

**이 계획서는 분석 및 제안 단계이며, 실제 파일 수정은 승인 후 진행됩니다.**

