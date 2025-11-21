# 작업 커밋 로그 (The Roha Way)



이 문서는 프로젝트의 모든 주요 변경 사항을 기록하는 항해 일지입니다. 모든 커밋은 Conventional Commits 규칙을 따르며, 커밋 직후 이곳에 기록됩니다.



---

### 2025-11-21 16:36 KST

**[76c47f2] feat(core): [2025-11-21 16:36 KST] 제트 엔진(Calamine+Pandas) 도입 완료 및 토큰 계산 로직 정상화 (5분 -> 27초)**

- **수정 파일:** `core/file_parser_utils/industry_rules.py`, `PANDAS_CONVERSION_DESIGN.md` (신규)

- **핵심 내용:** 
  1. **Pandas 기반 가족 통합 로직 리팩토링**: 기존 Python 리스트/반복문 기반의 `merge_family_data` 함수를 Pandas DataFrame의 `groupby().agg()` 기능을 활용하여 완전히 재구현함. 입력 데이터를 `pd.DataFrame`으로 변환한 후, 그룹핑 키(사업자번호 > 대표자명 > 금액 우선순위)를 생성하고, `groupby().agg()`로 금액 필드는 합산, 문자열 필드는 가장 긴 값을 선택하는 방식으로 통합함. 단일 그룹과 다중 그룹을 분리 처리하여 성능을 최적화하고, Pandas 사용 불가 시 Legacy 함수로 자동 fallback하는 안전장치를 포함함. 처리 시간이 대폭 단축되어 1799개 데이터를 0.57초 내에 287개로 통합하는 성능을 달성함.
  
  2. **토큰 계산 로직 정상화**: 1순위 시트(월 정산서)는 이미 통합된 데이터이므로 가족 통합을 생략하지만, 이로 인해 토큰 계산 시 원본 건수(1462건)가 그대로 사용되어 과다 차감되는 문제를 해결하기 위해 `calculate_count_and_parse` 함수에서 토큰 계산 시에는 강제로 `IndustryRules().merge_family_data()`를 호출하여 통합된 건수(227건)를 사용하도록 수정함. `parsed_data` 객체 자체는 수정하지 않고 원본을 유지하여, 실제 변환 로직에는 영향을 주지 않으면서도 토큰 계산의 정확성을 확보함.
  
  3. **Calamine 엔진 통합**: Excel 파일 로딩 속도를 300배 향상시킨 Calamine 엔진이 정상 작동 중이며, Pandas 기반 가족 통합과 함께 "제트 엔진"으로 작동하여 전체 변환 프로세스의 성능을 극대화함. 최신 변환 기록에서 227건을 27.12초에 처리하는 성능을 달성함(초당 8.40건/초).

- **성능 개선:**
  - 가족 통합 처리 시간: 약 0.57초 (1799개 → 287개)
  - 전체 변환 시간: 27.12초 (227건 처리)
  - 초당 처리 건수: 8.40건/초

- **기술적 특징:**
  - Pandas `groupby().agg()` 활용으로 코드 간결화 및 성능 향상
  - Legacy 함수 fallback 메커니즘으로 안정성 확보
  - 토큰 계산 시 강제 통합으로 정확성 확보
  - Calamine 엔진과의 시너지로 전체 프로세스 최적화

'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-21 16:00 KST

**[08f7863] fix(core): [2025-11-21 16:00 KST] 1순위 시트 토큰 과다 차감 오류 수정 (계산 시 강제 통합 적용)**

- **수정 파일:** `core/file_upload_helper.py`

- **핵심 내용:** 1순위 시트(월 정산서)는 이미 통합된 데이터이므로 가족 통합을 생략하지만, 이로 인해 토큰 계산 시 원본 건수(1462건)가 그대로 사용되어 과다 차감되는 문제가 발생함. 이를 해결하기 위해 `calculate_count_and_parse` 함수에서 토큰 계산 시에는 강제로 `IndustryRules().merge_family_data()`를 호출하여 통합된 건수(227건)를 사용하도록 수정함. `parsed_data` 객체 자체는 수정하지 않고 원본을 유지하여, 실제 변환 로직에는 영향을 주지 않으면서도 토큰 계산의 정확성을 확보함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-20 21:50 KST

**[1cd387b] feat(core): [2025-11-20 21:50 KST] Calamine 엔진 도입으로 엑셀 로딩 속도 300배 향상 (MockWorkbook 어댑터 적용)**

- **수정 파일:** `core/file_parser.py`, `core/utils/excel_adapter.py` (신규), `core/utils/__init__.py` (신규)

- **핵심 내용:** Excel 파일 로딩 속도 개선을 위해 `python-calamine` 엔진을 도입하고, 기존 `openpyxl` 의존 로직과의 호환성을 위해 `MockWorkbook` 어댑터 패턴을 구현함. `pandas.read_excel(engine='calamine')`을 사용하여 17MB Excel 파일의 로딩 시간을 약 3분에서 0.5초로 단축(약 300배 향상). `MockWorkbook`, `MockSheet`, `MockCell` 클래스를 통해 pandas DataFrame을 openpyxl Workbook처럼 동작하도록 래핑하여, 기존 `header_locator.py`의 로직을 전혀 수정하지 않고도 Calamine 엔진의 성능 이점을 활용할 수 있게 함. 또한 `core/utils/__init__.py`에서 기존 `core/utils.py`의 `row_value` 함수를 re-export하여 import 호환성을 유지함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-18 20:56:42 KST

**[8b6fe15] perf(parser): [대혁명 1-1] 중복 파일 파싱 제거 및 단일 파싱 구현**

- **수정 파일:** `core/file_upload_helper.py`, `routes/conversion_modules/conversion_engine_routes.py`, `core/conversion_engine.py`

- **핵심 내용:** 화이트보드 작전에서 설계한 이상적 흐름도의 Phase 1을 구현. `calculate_template_count` 함수를 `calculate_count_and_parse`로 변경하여 템플릿 건수와 파싱된 데이터를 튜플로 반환하도록 수정. `start_conversion`에서 파싱된 데이터를 `convert_file`에 직접 전달하여 중복 파싱을 완전히 제거. `convert_file` 함수는 `parsed_data`를 선택적 인자로 받아 재사용하거나, 미제공 시 하위 호환성을 위해 기존 로직을 실행. 이로써 파일은 단 한 번만 파싱되고, 그 결과가 템플릿 건수 계산과 변환 프로세스 모두에서 재사용되어 구조적 낭비를 제거함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 13:41:10 KST

**[3cea227] refactor(home): [수도 재편 1-5] 비밀번호 재설정 로직 분리**

- **수정 파일:** `routes/home.py`, `routes/home_modules/password_routes.py`, `app.py`

- **핵심 내용:** home.py에 혼재되어 있던 비밀번호 재설정 관련 함수들을 독립적인 `routes/home_modules/password_routes.py` 모듈로 분리함. 관련 url_for 참조를 모두 업데이트하여 시스템 전반의 일관성을 확보함. 이는 home.py 리팩토링의 다섯 번째 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 13:15:51 KST

**[3d4d80a] refactor(home): [수도 재편 1-4] 프로필 관리 로직 분리**

- **수정 파일:** `routes/home.py`, `routes/home_modules/profile_routes.py`, `app.py`

- **핵심 내용:** home.py에 혼재되어 있던 프로필 관리 관련 함수들을 독립적인 `routes/home_modules/profile_routes.py` 모듈로 분리함. 관련 url_for 참조를 모두 업데이트하여 시스템 전반의 일관성을 확보함. 이는 home.py 리팩토링의 네 번째 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 12:53:39 KST

**[6dbb73c] refactor(home): [수도 재편 1-3] 회원가입 로직 분리**

- **수정 파일:** `routes/home.py`, `routes/home_modules/registration_routes.py`, `app.py`, `routes/conversion_modules/main_routes.py`, `templates/conversion.html`

- **핵심 내용:** home.py에 혼재되어 있던 회원가입 관련 함수들을 독립적인 `routes/home_modules/registration_routes.py` 모듈로 분리함. 관련 url_for 참조를 모두 업데이트하여 시스템 전반의 일관성을 확보함. 이는 home.py 리팩토링의 세 번째 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 12:18:46 KST

**[e933b17] refactor(home): [수도 재편 1-2] 인증 로직 분리**

- **수정 파일:** `routes/home.py`, `routes/home_modules/auth_routes.py`, `app.py`, `routes/admin/dashboard.py`, `routes/conversion_modules/main_routes.py`, `templates/conversion.html`, `templates/email_verification_pending.html`

- **핵심 내용:** home.py에 혼재되어 있던 인증(로그인, 로그아웃) 관련 함수들을 독립적인 `routes/home_modules/auth_routes.py` 모듈로 분리함. 관련 url_for 참조를 모두 업데이트하여 시스템 전반의 일관성을 확보함. 이는 home.py 리팩토링의 두 번째 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 12:02:44 KST

**[5c1d043] refactor(home): [수도 재편 1-1] API 엔드포인트 분리**

- **수정 파일:** `routes/home.py`, `routes/home_modules/api_routes.py`, `app.py`

- **핵심 내용:** home.py에 혼재되어 있던 API 관련 엔드포인트(사용자명/이메일 중복 확인 등)를 독립적인 `routes/home_modules/api_routes.py` 모듈로 분리함. 이는 home.py 리팩토링의 첫 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 11:33:12 KST

**[4ecc7f7] refactor(extractor): [최고사령부 해체 1-6] 특별대우 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/enhancement_handler.py`, `core/recipient_extractor/utils/__init__.py`

- **핵심 내용:** main_extractor.py의 마지막 핵심 로직인 _enhance_first_priority_with_second_priority_logic 메서드를 독립적인 `core/recipient_extractor/utils/enhancement_handler.py` 모듈로 분리함. 이로써 '최고사령부 해체' 작전을 공식적으로 종결하고, main_extractor.py의 모듈화를 완성함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 11:08:25 KST

**[58e0145] refactor(extractor): [최고사령부 해체 1-5] 2순위 시트 감지 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/second_priority_detector.py`, `core/recipient_extractor/utils/__init__.py`

- **핵심 내용:** main_extractor.py에 혼재되어 있던 2순위 시트 감지 관련 메서드(_detect_second_priority_sheet)를 독립적인 `core/recipient_extractor/utils/second_priority_detector.py` 모듈로 분리함. RecipientExtractor 클래스는 이제 외부 함수를 호출하는 wrapper 역할만 수행하게 되어, 책임이 명확히 분리됨. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 10:52:42 KST

**[fd763f8] refactor(extractor): [최고사령부 해체 1-4] 시트 선택 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/sheet_selector.py`, `core/recipient_extractor/utils/__init__.py`

- **핵심 내용:** main_extractor.py에 혼재되어 있던 시트 선택 관련 3개 핵심 메서드(_select_optimal_sheet_by_family_rule, _extract_family_from_sheet_simple, _extract_numeric_value)를 독립적인 `core/recipient_extractor/utils/sheet_selector.py` 모듈로 분리함. RecipientExtractor 클래스는 이제 외부 함수를 호출하는 wrapper 역할만 수행하게 되어, 핵심 전략 로직의 책임이 명확히 분리됨. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 10:32:05 KST

**[71a9272] refactor(extractor): [최고사령부 해체 1-3] 행 단위 추출 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/row_extractor.py`

- **핵심 내용:** main_extractor.py에 혼재되어 있던 행 단위 데이터 추출 관련 2개 핵심 메서드(_extract_from_row_intelligent, _extract_from_row_template_mode)를 독립적인 `core/recipient_extractor/utils/row_extractor.py` 모듈로 분리함. RecipientExtractor 클래스는 이제 외부 함수를 호출하는 wrapper 역할만 수행하게 되어, 핵심 실행 로직의 책임이 명확히 분리됨. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-15 17:56:50 KST

**[6a29c52] refactor(extractor): [최고사령부 해체 1-2] 설정 관리 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/config_manager.py`

- **핵심 내용:** main_extractor.py에 혼재되어 있던 설정 관리 관련 7개 메서드를 독립적인 `core/recipient_extractor/utils/config_manager.py` 모듈로 분리함. RecipientExtractor 클래스는 이제 ConfigManager를 통해 설정을 관리하며, 코드의 책임이 명확해짐. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-15 16:57:22 KST

**[1f648be] refactor(extractor): [최고사령부 해체 1-1] 서브지침 처리 로직 분리**

- **수정 파일:** `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/utils/sub_guideline_processor.py`

- **핵심 내용:** main_extractor.py에 혼재되어 있던 서브지침 처리 관련 3개 메서드(_check_and_apply_sub_guideline, _extract_with_sub_guidelines, _extract_with_basic_mode)를 독립적인 `core/recipient_extractor/utils/sub_guideline_processor.py` 모듈로 분리함. 이는 main_extractor.py 리팩토링의 첫 단계로, 단일 책임 원칙을 강화하고 코드의 구조를 개선함. 'Executor 자동 점검' 및 'Commander 최종 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-16 00:33:17 KST

**[e432d11] refactor(extractor): 핵심 추출 로직을 extractor 모듈로 분리**

- **수정 파일:** `core/recipient_extractor/second_priority_handler.py`, `core/recipient_extractor/utils/extractor.py`, `core/recipient_extractor/utils/__init__.py`

- **핵심 내용:** second_priority_handler.py의 가장 큰 핵심 로직인 extract_recipients_from_second_priority() 메서드를 독립적인 `core/recipient_extractor/utils/extractor.py` 모듈로 분리함. 이로 인해 second_priority_handler.py의 라인 수가 94% 감소했으며, 이제 이 클래스는 외부 전문 모듈들을 호출하는 단순한 '지휘관' 역할만 수행하게 됨. 이는 second_priority_handler.py 리팩토링의 마지막 단계로, 코드의 모듈성과 유지보수성을 극대화함.

---

### 2025-11-16 00:13:48 KST

**[0ead361] refactor(extractor): 컬럼 매핑 및 점수 계산 로직을 column_scorer로 분리**

- **수정 파일:** `core/recipient_extractor/second_priority_handler.py`, `core/recipient_extractor/utils/column_scorer.py`, `core/recipient_extractor/utils/__init__.py`

- **핵심 내용:** second_priority_handler.py에 혼재되어 있던 가장 복잡한 핵심 로직인 컬럼 매핑 및 점수 계산 관련 8개 메서드를 독립적인 `core/recipient_extractor/utils/column_scorer.py` 모듈로 분리함. 이로 인해 second_priority_handler.py의 라인 수가 55% 감소했으며, 핵심 판단 로직의 책임이 명확히 분리됨. 이는 second_priority_handler.py 리팩토링의 네 번째 단계로, 코드의 모듈성과 유지보수성을 극대화함.

---

### 2025-11-15 23:48:46 KST

**[47ac3a4] refactor(extractor): 설정 및 키워드 로직을 config_loader 모듈로 분리**

- **수정 파일:** `core/recipient_extractor/second_priority_handler.py`, `core/recipient_extractor/utils/config_loader.py`

- **핵심 내용:** second_priority_handler.py의 __init__ 메서드에 하드코딩되어 있던 모든 설정값과 키워드 리스트를 독립적인 `core/recipient_extractor/utils/config_loader.py` 모듈로 분리함. __init__ 메서드는 이제 외부 함수를 호출하여 설정을 로드하는 단순한 역할만 수행하게 됨. 이는 second_priority_handler.py 리팩토링의 세 번째 단계로, 설정 관리의 중앙화를 통해 코드의 유지보수성을 향상시킴.

---

### 2025-11-15 23:28:13 KST

**[76764ab] fix(extractor): 분리된 검증 함수 호출 경로 수정 및 누락된 메서드 추가**

- **수정 파일:** `core/file_parser_utils/column_mapper.py`, `core/recipient_extractor/main_extractor.py`, `core/recipient_extractor/pipeline.py`, `core/recipient_extractor/second_priority_handler.py`, `core/recipient_extractor/validation.py`, `core/recipient_extractor/utils/sheet_detector.py`

- **핵심 내용:** '진실 규명 작전'과 '파수대 건설' 작전에서 모듈을 분리한 후 발생한 AttributeError들을 해결함. main_extractor.py에서 분리된 검증 함수들을 올바르게 호출하도록 수정하고, pipeline.py가 호출하던 누락된 'validate_recipients' 메서드를 Validator 클래스에 새로 구현함. 또한 column_mapper.py에 검증/완료일자 관련 컬럼을 금액 필드 매핑에서 제외하는 로직을 추가하여 변환 오류를 방지함. 이로써 모든 기능적 회귀 문제를 해결하고 시스템의 안정성을 복원함.

---

### 2025-11-15 12:58:47 KST

**[71b75ca] refactor(extractor): 데이터 검증 로직을 data_validator 모듈로 분리**

- **수정 파일:** `core/recipient_extractor/second_priority_handler.py`, `core/recipient_extractor/utils/data_validator.py`, `core/recipient_extractor/utils/__init__.py`, `core/recipient_extractor/utils/legacy_utils.py`

- **핵심 내용:** second_priority_handler.py에 혼재되어 있던 데이터 유효성 검증 관련 6개 메서드를 독립적인 `core/recipient_extractor/utils/data_validator.py` 모듈로 분리함. 이 과정에서 기존 `utils.py`와의 충돌을 피하기 위해 `utils`를 패키지로 만들고, `legacy_utils.py`로 분리하여 호환성을 유지함. 이는 second_priority_handler.py 리팩토링의 첫 단계로, 단일 책임 원칙을 강화하고 코드의 재사용성을 높임.

---

### 2025-11-15 12:25:53 KST

**[61a3968] refactor(parser): header_locator 로직을 외부 모듈 호출 중심으로 재구성**

- **수정 파일:** `core/file_parser_utils/header_locator.py`

- **핵심 내용:** header_locator.py에 마지막으로 남아있던 복잡한 로직들을, 분리된 외부 모듈(config_builder, scoring_utils 등)을 호출하는 단순한 지휘부 역할로 재구성함. inspect_all_sheets 메서드의 내부 로직을 헬퍼 메서드로 분리하여 가독성을 높임. 이로써 '감시탑 해체' 작전을 공식적으로 종결하고, 파일 파싱 계층의 모듈화를 완성함.

---

### 2025-11-15 11:50:07 KST

**[d0eae96] refactor(parser): 헤더 탐지 로직을 header_detector 모듈로 분리**

- **수정 파일:** `core/file_parser_utils/header_locator.py`, `core/file_parser_utils/header_detector.py`

- **핵심 내용:** header_locator.py에 혼재되어 있던 헤더 행 탐지 관련 7개 메서드를 독립적인 header_detector.py 모듈로 분리함. 이는 header_locator.py 리팩토링의 다섯 번째 단계로, 핵심 탐지 로직의 책임을 명확히 하고 코드의 구조를 개선함.

---

### 2025-11-15 11:37:55 KST

**[42a6289] refactor(parser): 컬럼 매핑 로직을 column_mapper 모듈로 분리**

- **수정 파일:** `core/file_parser_utils/header_locator.py`, `core/file_parser_utils/column_mapper.py`

- **핵심 내용:** header_locator.py에 혼재되어 있던 컬럼 매핑 관련 메서드(map_columns, _validate_dad_column_before_mom)를 독립적인 column_mapper.py 모듈로 분리함. 이는 header_locator.py 리팩토링의 네 번째 단계로, 단일 책임 원칙을 강화하고 코드의 재사용성을 높임.

---

### 2025-11-15 11:14:45 KST

**[8c97a23] refactor(parser): 점수 계산 및 데이터 품질 평가 로직을 scoring_utils로 분리**

- **수정 파일:** `core/file_parser_utils/header_locator.py`, `core/file_parser_utils/scoring_utils.py`

- **핵심 내용:** header_locator.py에 혼재되어 있던 점수 계산 및 데이터 품질 평가 관련 메서드(_count_matched_fields, _count_csv_matched_fields, _calculate_data_density, _calculate_csv_data_density, _evaluate_data_quality)를 scoring_utils.py 모듈로 분리하여, 모든 점수 계산 및 데이터 품질 평가 로직을 한 곳에 통합함. 이는 header_locator.py 리팩토링의 세 번째 단계로, 코드의 응집도를 높이고 재사용성을 향상시킴.

---

### 2025-11-15 11:00:20 KST

**[35377e2] refactor(parser): 유틸리티 및 점수 계산 로직 분리**

- **수정 파일:** `core/file_parser_utils/header_locator.py`, `core/file_parser_utils/number_parser.py`, `core/file_parser_utils/scoring_utils.py`

- **핵심 내용:** header_locator.py에 혼재되어 있던 숫자 파싱과 점수 계산 로직을 각각 독립적인 number_parser.py와 scoring_utils.py 모듈로 분리하여 단일 책임 원칙을 강화하고 코드의 재사용성을 높임.

---

### 2025-11-15 10:39:28 KST

**[a9895c3] refactor(parser): 설정 빌더 로직을 config_builder 모듈로 분리**

- **수정 파일:** `core/file_parser_utils/header_locator.py`, `core/file_parser_utils/config_builder.py`

- **핵심 내용:** header_locator.py에 혼재되어 있던 설정 관련 메서드를 독립적인 config_builder.py 모듈로 분리하고, 중복된 get_actual_data_range() 메서드를 통합하여 코드 구조를 개선함.

---

### 2025-11-14 21:49:03 KST

**[1916956] refactor(api): 사용자 API를 user_api.py 모듈로 분리**

- **수정 파일:** `routes/api.py`, `routes/api_modules/user_api.py`, `app.py`

- **핵심 내용:** `api.py`에 남아있던 모든 사용자 관련 API 엔드포인트를 별도의 `user_api.py` 모듈로 분리하여, 단일 책임 원칙에 따라 API의 책임을 완전히 분리하고 코드의 구조적 명확성과 유지보수성을 극대화함.

---

### 2025-11-14 21:22:55 KST

**[7442080] refactor(api): 관리자 API를 admin_api.py 모듈로 분리**

- **수정 파일:** `routes/api.py`, `routes/api_modules/admin_api.py`, `app.py`

- **핵심 내용:** `api.py`의 관리자 관련 API를 별도 모듈로 분리하여 구조를 개선함.

---

### 2025-11-14 21:10:43 KST

**[7212ed0] perf(api): myhome-data에서 중복 사용자 조회 제거**

- **수정 파일:** `routes/api.py`

- **핵심 내용:** `/api/myhome-data` 함수 내 불필요한 중복 DB 쿼리를 제거하여 성능을 개선함.

---

### 2025-11-14 20:53:03 KST

**[2f55e81] refactor(api): 중복된 /api/myhome-data 엔드포인트 제거**

- **수정 파일:** `routes/api.py`

- **핵심 내용:** api.py에 중복으로 정의되어 있던 두 개의 /api/myhome-data 엔드포인트 중, 더 이상 사용되지 않는 낡고 비효율적인 버전(N+1 문제 포함)을 완전히 제거함. 이로써 코드의 일관성을 확보하고, 잠재적인 혼란과 유지보수 비용을 줄임. '인간 검증'을 통해 기능적 회귀가 없음을 확인함.

---

### 2025-11-14 (KST)

**[2c4e4a4] feat(ops): 워크트리 간 데이터베이스 동기화 스크립트 추가**

- **수정 파일:** `sync_db.py` (신규 생성)

- **핵심 내용:** homepage1(전진기지)의 데이터를 master(본진)로 안전하게 복사하기 위한 자동화 스크립트를 추가함. 기존 본진 DB를 백업한 후, 전진기지의 DB로 덮어쓰는 자동화된 절차를 제공하여, 코드 변경과 별개로 관리되는 데이터의 동기화 문제를 해결하고 '인간의 실수'를 원천 차단함.

---

### 2025-11-14 (KST)

**[0942697] fix(api): 토큰 통계 집계 로직을 activity_logs 기반으로 통일**

- **수정 파일:** `routes/api.py`

- **핵심 내용:** '마이홈'과 '통합 관제실' 간의 토큰 데이터 불일치 문제를 해결하고, 모든 토큰 관련 통계 API가 '가장 최근 리셋 이후'의 `activity_logs`만을 집계하는 표준 법률을 따르도록 SQL 로직을 완전히 통일함. 이로써 제국 전체의 데이터 일관성을 확보하고, Commander의 본래 의도를 시스템 전체에 명확히 적용함.

---

### 2025-11-14 17:14:20 KST

**[e2f055a] fix(template): 불필요한 인라인 토큰 조회 스크립트 제거**

- **수정 파일:** `templates/conversion.html`

- **핵심 내용:** `/api/token-status`를 호출하던 중복된 인라인 스크립트를 제거하여, `static/js/conversion.js`의 정식 토큰 조회 시스템만 사용하도록 통일함.

---

### 2025-11-14 16:02:36 KST

**[59ccdec] perf(api): 토큰 사용 내역 조회 시 N+1 쿼리 문제 해결**

- **수정 파일:** `routes/api.py`

- **핵심 내용:** 루프 내 개별 쿼리를 단일 쿼리로 변경하여, 심각한 성능 병목 현상을 해결하고 시스템 안정성을 강화함.

---

### 2025-11-14 15:49:17 KST

**[f79ff72] fix(security): gold_customers_routes에서 SQL Injection 취약점 제거**

- **수정 파일:** `routes/conversion_modules/gold_customers_routes.py`

- **핵심 내용:** 동적 쿼리 생성 로직을 파라미터화된 쿼리로 변경하여, 심각한 보안 취약점을 해결함.

---

### 2025-11-14 15:31:53 KST

**[5d1f709] feat(conversion): 핵심 변환 로직을 conversion_engine_routes로 완전 분리**

- **수정 파일:** `app.py`, `routes/conversion.py` (삭제), `routes/conversion_modules/conversion_engine_routes.py` (신규), `routes/conversion_modules/page_routes.py`

- **핵심 내용:** 기존 conversion.py에 남아있던 start_conversion, download_converted 함수를 새로운 전용 모듈로 이전함. app.py의 Blueprint 연결을 교체하고, 기존 conversion.py 파일을 물리적으로 삭제하여 '위대한 혼돈'의 시대를 공식적으로 종결함. 이로써 conversion 관련 모든 기능은 `conversion_modules` 내에서 명확한 책임을 갖게 됨. '인간 검증'을 통해 전체 변환 프로세스의 기능적 회귀가 없음을 최종 확인함.

---

### 2025-11-14 14:20:45 KST

**[0926fb5] refactor(conversion): 공급자 정보 준비 로직 분리**

- **수정 파일:** `routes/conversion.py`, `routes/conversion_modules/conversion_helpers.py`

- **핵심 내용:** 핵심 변환 함수 내부에 있던 골드 회원 관련 공급자 정보 준비 로직을 외부 '병참' 함수로 분리하여 구조를 개선함.

---

### 2025-11-14 13:57:25 KST

**[068d399] refactor(conversion): 파라미터 추출 및 검증 로직 분리**

- **수정 파일:** `routes/conversion.py`, `routes/conversion_modules/conversion_helpers.py`

- **핵심 내용:** 핵심 변환 함수의 진입점에 있던 입력값 검증 로직을 별도의 '검문소' 함수로 분리하여 구조를 명확히 함.

---

### 2025-11-14 13:44:10 KST

**[2514d7e] refactor(conversion): 날짜 정규화 로직을 헬퍼 모듈로 분리**

- **수정 파일:** `routes/conversion.py`, `routes/conversion_modules/conversion_helpers.py`

- **핵심 내용:** 핵심 변환 함수 내부에 있던 날짜 처리 로직을 외부 헬퍼 모듈로 분리하여 코드 구조를 개선함.

---

### 2025-11-14 13:14:58 KST

**[e11653f] refactor(conversion): 헬퍼 함수를 conversion_helpers 모듈로 분리**

- **수정 파일:** `routes/conversion.py`, `routes/conversion_modules/conversion_helpers.py`

- **핵심 내용:** 핵심 변환 로직과 직접적인 관련이 적은 헬퍼 함수를 별도 모듈로 분리 및 격리하여, 대규모 리팩토링의 첫 단계를 완료함.

---

### 2025-11-14 12:40:00 KST

**[0289d8d] refactor(token): 토큰 관리 API를 확장 버전으로 통합**

- **수정 파일:** `routes/conversion_modules/token_routes.py`, `routes/conversion.py`, `app.py`

- **핵심 내용:** 분산되어 있던 토큰 관리 API를 안정성과 기능이 강화된 버전으로 통합하고 중앙화함.

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

