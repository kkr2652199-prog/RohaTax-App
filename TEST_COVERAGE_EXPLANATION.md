# 📊 테스트 커버리지 80% 설명서

## 🎯 테스트 커버리지란?

**테스트 커버리지(Test Coverage)**는 **"우리 코드의 어느 부분이 테스트되었는가?"**를 측정하는 지표입니다.

### 간단한 비유
```
📚 책을 읽었다고 해서 모든 내용을 이해한 것은 아닙니다.
✅ 테스트 커버리지는 "책의 몇 페이지를 읽었는지"를 측정합니다.
```

---

## 📈 테스트 커버리지 80%의 의미

### 예시: 변환 엔진 코드

**전체 코드가 100줄이라고 가정:**

```python
# core/conversion_engine.py (예시)
class ConversionEngine:
    def convert_file(self, file_path, supplier_info):
        # 1. 파일 검증 (10줄) ✅ 테스트됨
        if not os.path.exists(file_path):
            raise FileNotFoundError()
        
        # 2. 파일 파싱 (20줄) ✅ 테스트됨
        parsed_data = self.file_parser.parse_file(file_path)
        
        # 3. 데이터 추출 (30줄) ✅ 테스트됨
        recipients = self.recipient_extractor.extract(parsed_data)
        
        # 4. 템플릿 생성 (20줄) ✅ 테스트됨
        template = self.template_manager.create_template(recipients)
        
        # 5. 에러 처리 (10줄) ❌ 테스트 안됨
        try:
            result = self._process_template(template)
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
        
        # 6. 결과 반환 (10줄) ❌ 테스트 안됨
        return result
```

**테스트 커버리지 계산:**
- ✅ 테스트된 코드: 80줄 (1, 2, 3, 4번)
- ❌ 테스트 안된 코드: 20줄 (5, 6번)
- **커버리지: 80%** (80줄 / 100줄 × 100)

---

## 🔍 현재 프로젝트의 테스트 상태

### ✅ 현재 있는 테스트

1. **통합 테스트** (`tests/integration_test.py`)
   - 전체 변환 프로세스 테스트
   - 실제 파일로 변환 테스트

2. **E2E 테스트** (`tests/run_e2e.py`)
   - End-to-End 테스트
   - 실제 사용자 시나리오 테스트

3. **마스터 변환 테스트** (`tests/master_conversion_test.py`)
   - 여러 파일로 변환 테스트
   - 결과 검증

### ❌ 부족한 테스트

1. **단위 테스트 (Unit Test)**
   - 각 함수/메서드를 개별적으로 테스트
   - 예: `FileParser.parse_file()` 단독 테스트

2. **API 테스트**
   - REST API 엔드포인트 테스트
   - 예: `/api/conversion` 엔드포인트 테스트

---

## 📝 구체적인 예시

### 예시 1: 단위 테스트 (현재 없음)

**테스트할 함수:**
```python
# core/file_parser.py
def parse_file(self, file_path: str) -> Dict[str, Any]:
    """파일을 파싱하여 데이터 추출"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # Excel 파일 읽기
    df = pd.read_excel(file_path)
    
    # 헤더 감지
    header_row = self._detect_header(df)
    
    # 데이터 추출
    data = self._extract_data(df, header_row)
    
    return data
```

**필요한 테스트:**
```python
# tests/unit/test_file_parser.py (새로 만들어야 함)
import pytest
from core.file_parser import FileParser

def test_parse_file_success():
    """정상 파일 파싱 테스트"""
    parser = FileParser()
    result = parser.parse_file("tests/input/sample_invoice.xlsx")
    
    assert result is not None
    assert 'recipients' in result
    assert len(result['recipients']) > 0

def test_parse_file_not_found():
    """파일이 없을 때 에러 테스트"""
    parser = FileParser()
    
    with pytest.raises(FileNotFoundError):
        parser.parse_file("존재하지않는파일.xlsx")

def test_parse_file_invalid_format():
    """잘못된 파일 형식 테스트"""
    parser = FileParser()
    
    with pytest.raises(ValueError):
        parser.parse_file("tests/input/invalid_file.txt")
```

**이 테스트들이 실행되면:**
- `parse_file()` 함수의 **80% 이상**이 테스트됨
- 정상 케이스, 에러 케이스 모두 검증

---

### 예시 2: API 테스트 (현재 없음)

**테스트할 API:**
```python
# routes/conversion_modules/convert_routes.py
@conversion_engine_bp.route('/api/conversion/convert', methods=['POST'])
def convert_file():
    """파일 변환 API"""
    # 파일 업로드 처리
    # 변환 엔진 실행
    # 결과 반환
```

**필요한 테스트:**
```python
# tests/api/test_conversion_api.py (새로 만들어야 함)
import pytest
from flask import Flask
from app import app

@pytest.fixture
def client():
    """테스트 클라이언트"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_convert_file_success(client):
    """정상 변환 테스트"""
    # 로그인 (세션 설정)
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    
    # 파일 업로드
    data = {
        'file': (open('tests/input/sample_invoice.xlsx', 'rb'), 'sample.xlsx')
    }
    
    response = client.post('/api/conversion/convert', data=data)
    
    assert response.status_code == 200
    assert response.json['success'] == True
    assert 'download_url' in response.json

def test_convert_file_no_file(client):
    """파일 없이 요청 테스트"""
    response = client.post('/api/conversion/convert')
    
    assert response.status_code == 400
    assert response.json['success'] == False

def test_convert_file_not_logged_in(client):
    """로그인 안한 사용자 테스트"""
    response = client.post('/api/conversion/convert')
    
    assert response.status_code == 401
```

**이 테스트들이 실행되면:**
- `/api/conversion/convert` 엔드포인트의 **모든 케이스** 테스트
- 정상 케이스, 에러 케이스 모두 검증

---

## 🎯 80% 커버리지 달성 방법

### 1단계: 핵심 기능 테스트 (우선순위 최고)

**변환 엔진 핵심 함수들:**
```python
# tests/unit/test_conversion_engine.py
def test_convert_file_success()      # ✅ 정상 변환
def test_convert_file_invalid_file() # ✅ 잘못된 파일
def test_convert_file_no_supplier() # ✅ 공급자 정보 없음
def test_convert_file_empty_data()   # ✅ 빈 데이터
```

**예상 커버리지:** 60% → 80%

### 2단계: API 엔드포인트 테스트

**주요 API 엔드포인트:**
```python
# tests/api/test_user_api.py
def test_get_user_info()      # ✅ 사용자 정보 조회
def test_update_profile()     # ✅ 프로필 수정
def test_get_token_balance()  # ✅ 토큰 잔량 조회

# tests/api/test_conversion_api.py
def test_convert_file()       # ✅ 파일 변환
def test_get_conversion_log() # ✅ 변환 로그 조회
```

**예상 커버리지:** 80% → 85%

### 3단계: 에러 케이스 테스트

**에러 처리 테스트:**
```python
# tests/unit/test_error_handling.py
def test_file_not_found_error()      # ✅ 파일 없음
def test_invalid_format_error()      # ✅ 잘못된 형식
def test_database_error()            # ✅ DB 오류
def test_permission_denied_error()   # ✅ 권한 없음
```

**예상 커버리지:** 85% → 90%

---

## 📊 커버리지 측정 방법

### pytest-cov 사용

```bash
# 테스트 실행 + 커버리지 측정
pytest tests/ --cov=core --cov=routes --cov-report=html

# 결과:
# ----------- coverage: platform win32, python 3.14 -----------
# Name                          Stmts   Miss  Cover
# ------------------------------------------------------------
# core/conversion_engine.py       401     80    80%
# core/file_parser.py            2363    472    80%
# routes/conversion_routes.py     200     40    80%
# ------------------------------------------------------------
# TOTAL                          2964    592    80%
```

**결과 해석:**
- `Stmts`: 전체 코드 줄 수
- `Miss`: 테스트 안된 줄 수
- `Cover`: 커버리지 비율

---

## 🎯 목표: 80% 커버리지 달성

### 현재 상태 추정
- **예상 커버리지: 40-50%**
  - 통합 테스트만 존재
  - 단위 테스트 부족
  - API 테스트 부족

### 달성 방법

**1주차 작업:**
1. **핵심 변환 엔진 단위 테스트 작성**
   - `test_conversion_engine.py` (20개 테스트)
   - `test_file_parser.py` (15개 테스트)
   - `test_recipient_extractor.py` (10개 테스트)

2. **API 엔드포인트 테스트 작성**
   - `test_conversion_api.py` (10개 테스트)
   - `test_user_api.py` (8개 테스트)
   - `test_admin_api.py` (5개 테스트)

**예상 결과:**
- 현재: 40-50% 커버리지
- 1주차 후: **80% 커버리지 달성**

---

## 💡 왜 80% 커버리지가 중요한가?

### 1. 버그 조기 발견
```
❌ 테스트 없음: 사용자가 발견 → 고객 불만 → 수정 비용 높음
✅ 테스트 있음: 개발 중 발견 → 즉시 수정 → 수정 비용 낮음
```

### 2. 코드 변경 시 안전성
```
❌ 테스트 없음: 코드 수정 시 다른 기능 깨질 수 있음
✅ 테스트 있음: 코드 수정 후 테스트 실행 → 문제 즉시 발견
```

### 3. 상용화 신뢰성
```
❌ 테스트 없음: "혹시 버그 있을까?" 불안
✅ 테스트 있음: "80% 검증됨" → 신뢰성 확보
```

---

## 📋 요약

### 테스트 커버리지 80%란?
- **전체 코드의 80%가 테스트 코드로 검증되었다**는 의미
- **100줄 코드 중 80줄이 테스트됨** = 80% 커버리지

### 현재 상태
- ✅ 통합 테스트 존재 (40-50% 커버리지 추정)
- ❌ 단위 테스트 부족
- ❌ API 테스트 부족

### 목표
- **1주차 내 80% 커버리지 달성**
- 핵심 기능 우선 테스트
- 에러 케이스 포함

### 측정 방법
```bash
pytest tests/ --cov=core --cov=routes --cov-report=html
```

---

**다음 단계:** 실제 테스트 코드 작성 시작할까요?


