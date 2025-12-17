# JSON 규칙 파일 완전 분석

## 📋 개요
이 문서는 1Tax App 변환 시스템에서 실제로 사용되는 JSON 규칙 파일들을 완전 분석한 문서입니다. 
**중요**: MD 파일은 참고용이고, **JSON 파일이 실제 변환에 관여하는 규칙 파일**입니다.

---

## 1. config/absolute_guidelines_v5.json (공급자 규칙 파일)

### 1.1 파일 개요
- **총 라인**: 170줄
- **역할**: 유저 정보 → 공급자 정보 절대값 매핑
- **로드 위치**: `core/absolute_guideline_loader.py` (라인 28)
- **버전**: v5.0
- **생성일**: 2025-10-03

### 1.2 규칙 구조 상세 분석

#### 1.2.1 absolute_rules (라인 7-105)
**핵심 절대 규칙들**

##### user_info_as_supplier (라인 8-13)
```json
"user_info_as_supplier": {
  "rule": "로그인한 유저 정보는 공급자 정보의 절대값입니다",
  "priority": "CRITICAL",
  "description": "변환앱에서 로그인한 유저의 정보는 세금계산서 템플릿의 공급자 정보로 반드시 사용되어야 합니다",
  "enforcement": "MANDATORY"
}
```
- **우선순위**: CRITICAL (최우선)
- **적용**: MANDATORY (강제)
- **Python 연결**: `core/absolute_guideline_loader.py`의 `get_user_info_as_supplier()` 메서드

##### template_field_mapping (라인 15-46)
**6개 필드 매핑 규칙**

1. **공급자_상호** (라인 16-20)
   - 소스: `user_info.company_name`
   - 검증: 필수값, 빈 값 불허
   - Python 연결: `core/template_manager.py`의 `map_supplier_info()` 메서드

2. **공급자_대표자** (라인 21-25)
   - 소스: `user_info.representative`
   - 검증: 필수값, 빈 값 불허

3. **공급자_사업자번호** (라인 26-30)
   - 소스: `user_info.business_number`
   - 검증: 10자리 숫자, 형식 검증 필수

4. **공급자_주소** (라인 31-35)
   - 소스: `user_info.address`
   - 검증: 필수값, 빈 값 불허

5. **공급자_이메일** (라인 36-40)
   - 소스: `user_info.email`
   - 검증: 이메일 형식 검증 필수

6. **공급자_전화번호** (라인 41-45)
   - 소스: `user_info.phone`
   - 검증: 전화번호 형식 검증 권장

##### data_validation_rules (라인 48-64)
**데이터 검증 규칙**

1. **business_number** (라인 49-53)
   - 형식: 10자리 숫자만
   - 정규식: `^[0-9]{10}$`
   - Python 연결: `core/absolute_guideline_loader.py`의 `validate_business_number()` 메서드

2. **email** (라인 54-58)
   - 형식: 이메일 형식
   - 정규식: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$`

3. **phone** (라인 59-63)
   - 형식: 전화번호 형식
   - 정규식: `^[0-9-+()\\s]+$`

##### template_cell_mapping (라인 66-97)
**엑셀 셀 위치 매핑**

- **A7**: 공급자_사업자번호 (숫자만, 하이픈 제거)
- **B7**: 작성일자 (YYMMDD 형식)
- **C7**: 공급자_상호 (문자열)
- **D7**: 공급자_대표자 (문자열)
- **E7**: 공급자_주소 (문자열)
- **F7**: 공급자_이메일 (이메일 형식)

##### absolute_values (라인 99-104)
**홈택스 템플릿 고정값**
- **A7**: "01"
- **W7**: "30"
- **BG7**: "01"

#### 1.2.2 guideline_steps (라인 107-133)
**5단계 실행 순서**

1. **step_1**: 사용자 정보 로드 (우선순위 1)
2. **step_2**: 절대값 검증 (우선순위 2)
3. **step_3**: 템플릿 매핑 (우선순위 3)
4. **step_4**: 절대값 적용 (우선순위 4)
5. **step_5**: 최종 검증 (우선순위 5)

#### 1.2.3 error_handling (라인 135-151)
**에러 처리 규칙**

1. **missing_user_info**: 사용자 정보 없음
2. **invalid_business_number**: 사업자번호 형식 오류
3. **invalid_email**: 이메일 형식 오류

### 1.3 Python 코드 연결

#### 1.3.1 로드 과정
```python
# core/absolute_guideline_loader.py (라인 28)
config_path = os.path.join(current_dir, 'config', 'absolute_guidelines_v5.json')

# core/guideline_manager.py에서 사용
guideline_loader = AbsoluteGuidelineLoader()
rules = guideline_loader.get_guidelines()
```

#### 1.3.2 실제 사용 위치
- **core/template_manager.py**: 템플릿 기입 시 공급자 정보 매핑
- **core/conversion_engine.py**: 변환 과정에서 절대값 적용
- **routes/conversion.py**: API 엔드포인트에서 규칙 적용

### 1.4 규칙 수정 가이드

#### 1.4.1 새 필드 추가
1. `template_field_mapping`에 새 필드 추가
2. `template_cell_mapping`에 엑셀 셀 위치 추가
3. `data_validation_rules`에 검증 규칙 추가
4. Python 코드 수정 (`core/template_manager.py`)
5. 테스트 실행

#### 1.4.2 검증 규칙 수정
1. `data_validation_rules`에서 정규식 수정
2. 파일 저장
3. 테스트 실행으로 검증

---

## 2. config/industry_config.json (업종별 설정 파일)

### 2.1 파일 개요
- **총 라인**: 1,105줄
- **역할**: 업종별 키워드 및 가중치 설정
- **로드 위치**: `core/industry_config_loader.py`
- **주요 업종**: delivery (배달대행사)

### 2.2 규칙 구조 상세 분석

#### 2.2.1 delivery 섹션 (배달대행사)

##### store_keywords (라인 7-60)
**47개 업체명 키워드**
- 가게, 가게명, 가맹점, 거래처가맹점, 거래처매장명...
- **역할**: 공급받는자 업체명 인식
- **사용 위치**: `core/recipient_extractor/main_extractor.py`

##### priority_fields (라인 61-67)
**5개 우선 필드**
- 사업자등록번호, 상호, 대표명, 사업장주소, 사업자이메일
- **역할**: 필드 우선순위 정의

##### confidence_threshold (라인 68)
- **값**: 0.3
- **역할**: 신뢰도 최소 임계값

##### min_valid_fields (라인 69)
- **값**: 3
- **역할**: 최소 유효 필드 수

##### recipient_keywords (라인 70-88)
**사업자번호 키워드 분류**

1. **strong** (라인 72-78): 강력한 키워드 6개
   - 공급받는자사업자번호, 수취인사업자번호, 거래처사업자번호...

2. **aux** (라인 79-87): 보조 키워드 7개
   - 사업자번호, 등록번호, 사업자등록번호...

##### amount_keywords (라인 89-120)
**32개 금액 관련 키워드**
- 요금, 금액, 비용, 가격, 수수료, 요금합계, 총금액, 합계, 부가세, VAT, 세금, 공급가액...

##### extraction_rules (라인 121-200+)
**추출 규칙들**

1. **business_number_pattern** (라인 122)
   - 정규식: `\\d{3}-\\d{2}-\\d{5}`

2. **email_pattern** (라인 123)
   - 정규식: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}`

3. **address_keywords** (라인 124-137)
   - 주소, 사업장, 본점, 지점, 소재지, 위치...

4. **representative_keywords** (라인 138-157)
   - 대표, 사장, 원장, 대표자, 대표이사, 임원...

5. **email_keywords** (라인 158-168)
   - 이메일, 사업자이메일, email, e-mail, 전자우편, 메일...

6. **address_city_tokens** (라인 169-200+)
   - 전국 시/도/구/군 이름들

### 2.3 Python 코드 연결

#### 2.3.1 로드 과정
```python
# core/industry_config_loader.py에서 로드
config = load_industry_config('delivery')

# core/file_parser.py에서 사용
keywords = config['store_keywords']
threshold = config['confidence_threshold']
```

#### 2.3.2 실제 사용 위치
- **core/file_parser.py**: 시트 선택 및 컬럼 매칭
- **core/recipient_extractor/main_extractor.py**: 공급받는자 정보 추출
- **core/amount_extractor.py**: 금액 정보 추출

### 2.4 규칙 수정 가이드

#### 2.4.1 새 키워드 추가
1. `industry_config.json` 열기
2. 해당 섹션 (예: `store_keywords`) 찾기
3. 배열에 새 키워드 추가
4. 파일 저장
5. 테스트 실행으로 검증

#### 2.4.2 임계값 조정
1. `confidence_threshold` 또는 `min_valid_fields` 찾기
2. 값 조정
3. 파일 저장
4. 테스트 실행으로 검증

---

## 3. 규칙 추가/수정 완전 가이드

### 3.1 새 키워드 추가

#### 절대지침 파일 (absolute_guidelines_v5.json)
1. 파일 열기
2. `template_field_mapping` 섹션 찾기
3. 새 필드 추가:
```json
"공급받는자_새필드": {
  "source": "user_info.new_field",
  "rule": "설명",
  "validation": "검증 규칙"
}
```
4. `template_cell_mapping`에 엑셀 셀 위치 추가
5. 파일 저장
6. Python 코드 수정 (`core/template_manager.py`)
7. 테스트 실행

#### 업종별 설정 파일 (industry_config.json)
1. 파일 열기
2. 해당 섹션 (예: `store_keywords`) 찾기
3. 배열에 새 키워드 추가
4. 파일 저장
5. 테스트 실행으로 검증

### 3.2 검증 규칙 수정

#### 절대지침 파일
1. `data_validation_rules` 섹션 찾기
2. 정규식 수정
3. 파일 저장
4. 테스트 실행으로 검증

#### 업종별 설정 파일
1. `extraction_rules` 섹션 찾기
2. 패턴 수정
3. 파일 저장
4. 테스트 실행으로 검증

### 3.3 새 업종 추가

1. `industry_config.json` 열기
2. 새 업종 섹션 추가 (예: `logistics`)
3. 모든 키워드 배열 복사 및 수정
4. 파일 저장
5. Python 코드 수정 (`core/industry_config_loader.py`)
6. 테스트 실행

---

## 4. 테스트 및 검증

### 4.1 테스트 실행 명령
```bash
python tests/run_real_conversion_test.py
```

### 4.2 검증 항목
- 키워드 매칭 정확도
- 컬럼 인식 정확도
- 시트 선택 정확도
- 템플릿 기입 정확도

### 4.3 오류 발생 시
1. 테스트 로그 확인
2. JSON 파일 문법 검증 (쉼표, 따옴표)
3. 정규식 문법 검증
4. 임계값 범위 검증

---

## 5. 주의사항

### 5.1 JSON 파일 수정 시
- ⚠️ 쉼표(,) 빠뜨리지 않기
- ⚠️ 따옴표(") 정확히 닫기
- ⚠️ 정규식 이스케이프 문자 확인
- ⚠️ 임계값 범위 확인

### 5.2 키워드 추가 시
- ⚠️ 중복 키워드 확인
- ⚠️ 유사 키워드 그룹화
- ⚠️ 너무 일반적인 키워드 지양

### 5.3 필드 매핑 추가 시
- ⚠️ Python 코드도 함께 수정
- ⚠️ `template_manager.py` 업데이트
- ⚠️ 엑셀 셀 위치 확인

---

## 6. 규칙 우선순위

### 6.1 절대 규칙 (absolute_guidelines_v5.json)
- **최우선 순위**
- 공급자 정보는 항상 유저 정보 사용
- 변경 불가

### 6.2 업종별 규칙 (industry_config.json)
- **두 번째 우선순위**
- 업종별 키워드 및 가중치
- 조정 가능

### 6.3 하드코딩 규칙 (Python 코드)
- **세 번째 우선순위**
- `file_parser.py` 금지어 186개
- 수정 시 주의 필요

---

## 7. 버전 관리

### 7.1 현재 버전
- `absolute_guidelines_v5.json`: v5.0
- `industry_config.json`: 버전 없음 (추가 권장)

### 7.2 버전 업그레이드 시
1. 기존 파일 백업
2. 새 버전 파일 생성
3. `absolute_guideline_loader.py`에서 경로 수정
4. 테스트 실행
5. 문제 없으면 배포

---

## 8. 요약

### 실제 변환 시스템 규칙 관리
- ✅ **JSON 파일이 실제 규칙**
- ✅ **MD 파일은 참고 문서**
- ✅ **Python 코드가 실행 로직**

### 규칙 수정 흐름
1. MD 문서에서 규칙 설계
2. JSON 파일 수정
3. 필요 시 Python 코드 수정
4. 테스트로 검증
5. 배포

### 핵심 원칙
- ⚠️ 수정 후 반드시 테스트
- ⚠️ 백업 후 수정
- ⚠️ 문법 검증 필수
- ⚠️ Python 코드 연동 확인

---

## 9. 실제 변환 과정에서의 적용

### 9.1 변환 시작 시
1. `core/absolute_guideline_loader.py`가 `absolute_guidelines_v5.json` 로드
2. `core/industry_config_loader.py`가 `industry_config.json` 로드
3. 사용자 정보를 공급자 정보로 매핑

### 9.2 파일 파싱 시
1. `core/file_parser.py`가 `industry_config.json`의 키워드 사용
2. 시트 선택 및 컬럼 매칭
3. 공급받는자 정보 추출

### 9.3 템플릿 생성 시
1. `core/template_manager.py`가 `absolute_guidelines_v5.json` 사용
2. 공급자 정보를 템플릿에 기입
3. 절대값 적용

### 9.4 최종 검증 시
1. 모든 규칙 적용 확인
2. 에러 처리 규칙 적용
3. 변환 완료

---

*최종 업데이트: 2025-01-22*
*변경 사항: JSON 규칙 파일 완전 분석 완료, Python 코드 연결 명시, 규칙 수정 가이드 제공*






