# 작전명: 최후의 공성 계획 보고서
## Operation: The Final Siege Plan

---

## 📋 1. 최종 목표 식별 (Identify Final Targets)

### 현재 `routes/conversion.py`에 남아있는 핵심 함수 3개

| 함수명 | 라인 범위 | 예상 줄 수 | 역할 | 복잡도 |
|--------|----------|-----------|------|--------|
| `start_conversion()` | 130-541 | **412줄** | 변환 시작 API (핵심 비즈니스 로직) | ⭐⭐⭐⭐⭐ |
| `download_converted()` | 544-621 | **78줄** | 변환 결과 다운로드 API | ⭐⭐ |
| `_calculate_template_count_precisely()` | 48-122 | **75줄** | 템플릿 건수 정밀 계산 헬퍼 | ⭐⭐⭐ |

**총 제거 대상: 약 565줄**

---

## 🔬 2. 심장부 해부 (Anatomy of the Core)

### `start_conversion()` 함수 내부 로직 분석

#### **1단계: 인증 및 보안 검증** (라인 145-152)
- **책임**: 사용자 인증 및 CSRF 토큰 검증
- **의존성**: `ensure_login_for_json()`, `request.headers/form`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립)

#### **2단계: Form Data 파라미터 추출 및 검증** (라인 154-180)
- **책임**: 
  - `template_id`, `issue_date`, `file_name`, `industry_type`, `guidelines` 추출
  - 파일 업로드 확인 (`request.files['file']`)
  - 필수 파라미터 검증
- **의존성**: `request.form`, `request.files`
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **3단계: 날짜 정규화** (라인 182-207)
- **책임**: 
  - 다양한 날짜 형식 지원 (`251001`, `25년10월01일`, ISO 형식)
  - ISO 형식(YYYY-MM-DD)으로 통일
- **의존성**: `datetime`
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립, 유틸리티 함수로 분리 가능)

#### **4단계: 사용자 정보 로드** (라인 209-222)
- **책임**: 
  - DB에서 사용자 정보 조회
  - 공급자 정보 자동 매핑 준비
- **의존성**: `get_conn()`, `users` 테이블
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **5단계: 파일 저장** (라인 224-228)
- **책임**: 업로드된 파일을 임시 디렉토리에 저장
- **의존성**: `save_uploaded_file()` (이미 연동 모듈로 분리됨)
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (이미 분리됨)

#### **6단계: 템플릿 건수 정밀 계산** (라인 230-240)
- **책임**: 
  - 파일 파싱을 통한 실제 템플릿 건수 계산
  - 변환 전 토큰 필요량 예측
- **의존성**: `calculate_template_count()` (이미 연동 모듈로 분리됨)
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐⭐ (이미 분리됨)

#### **7단계: VIP/GoldVIP 무제한 처리** (라인 242-259)
- **책임**: 
  - 사용자 구독 정보 확인
  - 무제한 사용자 여부 판단
  - 필요 토큰 수 계산 (무제한: 0, 일반: 템플릿 건수)
- **의존성**: `get_user_subscription()`, `is_unlimited_user()`
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **8단계: 토큰 잔량 정밀 확인** (라인 261-293)
- **책임**: 
  - `activity_logs` 기반으로 정확한 토큰 잔량 계산
  - `TOKEN_RESET_BY_ADMIN` 이후의 로그만 집계
  - 삭제된 레코드(`is_deleted=0`) 제외
- **의존성**: `get_conn()`, `activity_logs` 테이블, 복잡한 SQL 쿼리
- **복잡도**: 높음
- **분리 가능성**: ⭐⭐⭐ (중간, SQL 로직이 복잡함)

#### **9단계: 토큰 부족 시 에러 반환** (라인 295-317)
- **책임**: 
  - 토큰 부족 시 상세한 에러 메시지 반환
  - 부족한 토큰 수 및 예상 비용 계산
- **의존성**: 이전 단계의 `available_tokens`, `required_tokens`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **10단계: 골드 회원 공급자 선택 분기** (라인 332-381)
- **책임**: 
  - 골드 회원의 경우 선택한 고객 정보를 공급자로 사용
  - 비골드 회원 또는 미선택 시 기본 프로필 공급자 사용
  - `gold_customers` 테이블 조회
- **의존성**: `get_conn()`, `gold_customers` 테이블, `user['plan_type']`
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **11단계: 사용자 정보를 절대지침 시스템에 전달** (라인 383-394)
- **책임**: 
  - 사용자 정보를 딕셔너리 형태로 구성
  - 절대지침 시스템에 전달할 형식으로 변환
- **의존성**: `user` 딕셔너리
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립)

#### **12단계: 변환 엔진 실행** (라인 398-413)
- **책임**: 
  - `ConversionEngine` 인스턴스 생성 (상태 격리)
  - `convert_file()` 메서드 호출
  - 전체 변환 프로세스 실행
- **의존성**: `ConversionEngine`, 모든 변환 관련 모듈
- **복잡도**: 매우 높음 (하지만 이미 캡슐화됨)
- **분리 가능성**: ⭐⭐⭐⭐⭐ (이미 완전히 분리됨)

#### **13단계: 변환 실패 시 처리** (라인 415-421)
- **책임**: 
  - 변환 실패 시 임시 파일 정리
  - 에러 메시지 반환
- **의존성**: `cleanup_temp_file()`, `conversion_result`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립)

#### **14단계: 활동 로그 기록** (라인 423-489)
- **책임**: 
  - DB 트랜잭션 내에서 활동 로그 기록
  - 사용자 정보 재조회
  - `record_activity()` 호출
  - `FILE_CONVERT` 활동 타입으로 기록
- **의존성**: `get_conn()`, `record_activity()`, `activity_logs` 테이블
- **복잡도**: 높음
- **분리 가능성**: ⭐⭐⭐ (중간, 트랜잭션 관리 필요)

#### **15단계: 토큰 차감 처리** (라인 491-505)
- **책임**: 
  - `TokenDeductionProcessor`를 통한 토큰 차감
  - 변환 결과에서 실제 템플릿 건수 추출
  - 무제한 사용자 처리
- **의존성**: `TokenDeductionProcessor` (이미 연동 모듈로 분리됨)
- **복잡도**: 중간
- **분리 가능성**: ⭐⭐⭐⭐⭐ (이미 분리됨)

#### **16단계: 변환 완료 시간 기록** (라인 507-510)
- **책임**: 
  - 변환 시작/종료 시간 기록
  - 실행 시간 계산
- **의존성**: `time.time()`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립)

#### **17단계: 세션에 결과 저장** (라인 512-514)
- **책임**: 
  - 변환 결과를 세션에 저장
  - 다운로드 파일명 저장
- **의존성**: `session`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **18단계: 성공 응답 반환** (라인 516-529)
- **책임**: 
  - 토큰 정보 페이로드 구성
  - 성공 응답 반환
- **의존성**: `token_result`, `conversion_result`, `url_for()`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐ (높음)

#### **19단계: 예외 처리** (라인 531-540)
- **책임**: 
  - 변환 중 발생한 모든 예외 처리
  - 임시 파일 정리
  - 에러 로깅
- **의존성**: `cleanup_temp_file()`, `logger`
- **복잡도**: 낮음
- **분리 가능성**: ⭐⭐⭐⭐⭐ (완전 독립)

---

## 🏰 3. 새로운 요새 설계 (Design a New Fortress)

### 제안 모듈 구조: `routes/conversion_modules/conversion_engine_routes.py`

```python
"""
변환 엔진 라우트 모듈
변환 시작, 다운로드 등의 핵심 변환 기능
"""

from flask import Blueprint, session, request, url_for
from core.responses import success, error
from core.conversion_engine import ConversionEngine
from core.file_upload_helper import save_uploaded_file, cleanup_temp_file, calculate_template_count
from core.subscription_utils import get_user_subscription, is_unlimited_user
from core.token_deduction_processor import TokenDeductionProcessor
from core.activity_service import record_activity
from core.db import get_conn_optimized as get_conn
from ..utils.auth import ensure_login_for_json
import logging
import sqlite3
import time
from datetime import datetime

conversion_engine_bp = Blueprint('conversion_engine', __name__)
logger = logging.getLogger(__name__)

# ============================================
# 보조 함수들 (Helper Functions)
# ============================================

def normalize_issue_date(date_str: str) -> str:
    """날짜 정규화: 다양한 형식을 ISO 형식으로 변환"""
    # ... (라인 183-203 로직)
    pass

def validate_conversion_request(request) -> tuple[dict, str]:
    """변환 요청 파라미터 검증 및 추출"""
    # ... (라인 154-180 로직)
    pass

def load_user_info(user_id: int) -> dict:
    """사용자 정보 로드"""
    # ... (라인 209-222 로직)
    pass

def check_token_balance(user_id: int) -> dict:
    """토큰 잔량 확인 (activity_logs 기반)"""
    # ... (라인 266-293 로직)
    pass

def prepare_supplier_info(user: dict, selected_customer_id: str = None) -> dict:
    """공급자 정보 준비 (골드 회원 분기 포함)"""
    # ... (라인 332-381 로직)
    pass

def prepare_user_info_for_guidelines(user: dict, user_id: int) -> dict:
    """절대지침 시스템용 사용자 정보 준비"""
    # ... (라인 383-394 로직)
    pass

def record_conversion_activity(cursor, user_id: int, conversion_result: dict, user_current: dict):
    """변환 활동 로그 기록"""
    # ... (라인 427-478 로직)
    pass

def build_success_response(conversion_result: dict, token_result: dict, file_name: str, user: dict) -> dict:
    """성공 응답 구성"""
    # ... (라인 516-529 로직)
    pass

# ============================================
# 메인 라우트 함수들
# ============================================

@conversion_engine_bp.route('/api/convert/start', methods=['POST'])
def start_conversion():
    """변환 시작 API (리팩토링된 버전)"""
    # 1. 인증 및 보안 검증
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return guard_response
    
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not csrf_token:
        return error('보안 토큰이 없습니다. 다시 시도해주세요.', status=403)
    
    try:
        # 2. 파라미터 검증 및 추출
        params, error_response = validate_conversion_request(request)
        if error_response:
            return error_response
        
        # 3. 날짜 정규화
        issue_date = normalize_issue_date(params['issue_date_raw'])
        if not issue_date:
            return error('전자세금일자 형식이 올바르지 않습니다', status=400)
        
        # 4. 사용자 정보 로드
        user = load_user_info(user_id)
        if not user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        # 5. 파일 저장
        temp_file_path = save_uploaded_file(params['uploaded_file'])
        
        # 6. 템플릿 건수 계산
        template_count = calculate_template_count(temp_file_path, params['industry_type'])
        if template_count == 0:
            cleanup_temp_file(temp_file_path)
            return error('파일에서 템플릿 건수를 계산할 수 없습니다. 파일 형식을 확인해주세요.', status=400)
        
        # 7. VIP/GoldVIP 무제한 처리
        is_unlimited = is_unlimited_user(user_id)
        required_tokens = 0 if is_unlimited else template_count
        
        # 8. 토큰 잔량 확인
        token_balance_info = check_token_balance(user_id)
        available_tokens = token_balance_info['available_tokens']
        
        # 9. 토큰 부족 시 에러 반환
        if not is_unlimited and available_tokens < required_tokens:
            shortage = required_tokens - available_tokens
            cleanup_temp_file(temp_file_path)
            return error(
                f'토큰이 부족합니다. 템플릿 {template_count}개 생성에 {required_tokens}토큰이 필요하지만, '
                f'현재 {available_tokens}토큰을 보유하고 있어 {shortage}토큰이 부족합니다.',
                status=400,
                data={
                    'template_count': template_count,
                    'required_tokens': required_tokens,
                    'available_tokens': available_tokens,
                    'shortage': shortage,
                    'estimated_cost': shortage * 200
                }
            )
        
        # 10. 변환 시작 시간 기록
        conversion_start_time = time.time()
        
        # 11. 공급자 정보 준비
        supplier = prepare_supplier_info(user, params.get('selected_customer_id'))
        
        # 12. 사용자 정보 준비
        user_info = prepare_user_info_for_guidelines(user, user_id)
        
        # 13. 변환 엔진 실행
        conversion_engine = ConversionEngine()
        conversion_result = conversion_engine.convert_file(
            uploaded_file_path=temp_file_path,
            supplier_info=supplier,
            template_id=params['template_id'],
            industry_type=params['industry_type'],
            guidelines=params['guidelines'],
            issue_date=issue_date,
            file_name=params['file_name'],
            user_info=user_info
        )
        
        # 14. 변환 실패 시 처리
        if not conversion_result['success']:
            cleanup_temp_file(temp_file_path)
            return error(f"변환 실패: {conversion_result.get('error_message', '알 수 없는 오류')}", status=500)
        
        # 임시 파일 정리
        cleanup_temp_file(temp_file_path)
        
        # 15. 활동 로그 기록
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                user_current = cursor.execute(
                    "SELECT id, plan_type, token_balance, COALESCE(tokens_used, 0) AS tokens_used FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                
                if user_current:
                    record_conversion_activity(cursor, user_id, conversion_result, user_current)
                    conn.commit()
        except Exception as activity_error:
            logger.error(f"활동 로그 기록 중 오류 발생: {str(activity_error)}")
        
        # 16. 토큰 차감 처리
        token_processor = TokenDeductionProcessor()
        token_result = token_processor.process_token_deduction(
            user_id=user_id,
            is_unlimited=is_unlimited,
            conversion_result=conversion_result
        )
        
        if not token_result.get('success'):
            logger.error(f"토큰 차감 실패: {token_result.get('message')}")
            return error(token_result.get('message', '토큰 처리 중 오류가 발생했습니다'), status=500)
        
        # 17. 변환 완료 시간 기록
        conversion_end_time = time.time()
        execution_time = round(conversion_end_time - conversion_start_time, 2)
        logger.info(f"변환 완료: 실행시간 {execution_time}초 - 사용자 {user_id}")
        
        # 18. 세션에 결과 저장
        session['last_conversion_result'] = conversion_result
        session['last_file_name'] = params['file_name']
        
        # 19. 성공 응답 반환
        return build_success_response(conversion_result, token_result, params['file_name'], user)
        
    except Exception as e:
        logger.error(f"변환 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if 'temp_file_path' in locals():
            cleanup_temp_file(temp_file_path)
        return error(f'변환 처리 중 오류 발생: {str(e)}', status=500)


@conversion_engine_bp.route('/api/convert/download', methods=['GET'])
def download_converted():
    """변환된 홈텍스 파일 다운로드"""
    # ... (라인 544-621 로직, 거의 그대로 유지)
    pass
```

### 추가 모듈: `routes/conversion_modules/conversion_helpers.py`

```python
"""
변환 관련 헬퍼 함수 모듈
공통으로 사용되는 유틸리티 함수들
"""

def _calculate_template_count_precisely(uploaded_file, industry_type: str = 'delivery') -> int:
    """템플릿 건수 정밀 계산 (기존 함수 그대로 이동)"""
    # ... (라인 48-122 로직)
    pass
```

---

## 🎯 4. 첫 번째 돌파구 제안 (Propose the First Breach)

### 우선순위 1: 헬퍼 함수 이전 (가장 안전)

**대상**: `_calculate_template_count_precisely()` 함수 (라인 48-122, 약 75줄)

**이유**:
1. ✅ **의존성이 가장 낮음**: 다른 함수를 호출하지 않고, 독립적으로 작동
2. ✅ **현재 사용되지 않음**: 코드 분석 결과, `start_conversion()`에서는 `calculate_template_count()`를 사용하고 있어 이 함수는 실제로 사용되지 않을 가능성이 높음
3. ✅ **테스트 용이성**: 독립적인 함수이므로 단위 테스트가 쉬움
4. ✅ **리스크 최소**: 다른 로직에 영향을 주지 않음

**작업 계획**:
1. `routes/conversion_modules/conversion_helpers.py` 파일 생성
2. `_calculate_template_count_precisely()` 함수를 해당 파일로 이동
3. 함수명을 `calculate_template_count_precisely()`로 변경 (private에서 public으로)
4. `routes/conversion.py`에서 import 추가 (필요한 경우)

---

### 우선순위 2: 날짜 정규화 함수 분리 (높은 재사용성)

**대상**: `normalize_issue_date()` 내부 함수 (라인 183-203)

**이유**:
1. ✅ **완전 독립**: 외부 의존성이 거의 없음 (`datetime`만 사용)
2. ✅ **높은 재사용성**: 다른 곳에서도 사용 가능한 유틸리티 함수
3. ✅ **테스트 용이성**: 입력/출력이 명확함
4. ✅ **코드 가독성 향상**: `start_conversion()` 함수가 더 간결해짐

**작업 계획**:
1. `core/utils.py` 또는 `routes/conversion_modules/conversion_helpers.py`에 `normalize_issue_date()` 함수 추가
2. `start_conversion()` 내부의 중첩 함수를 제거하고 외부 함수 호출로 변경

---

### 우선순위 3: 파라미터 검증 함수 분리 (중간 복잡도)

**대상**: Form Data 파라미터 추출 및 검증 로직 (라인 154-180)

**이유**:
1. ✅ **명확한 책임**: 파라미터 검증이라는 단일 책임
2. ✅ **테스트 용이성**: Mock `request` 객체로 쉽게 테스트 가능
3. ✅ **코드 가독성 향상**: `start_conversion()`의 복잡도 감소

**작업 계획**:
1. `routes/conversion_modules/conversion_helpers.py`에 `validate_conversion_request()` 함수 추가
2. 반환값: `(params_dict, error_response)` 튜플
3. `start_conversion()`에서 호출하여 파라미터 추출

---

### 우선순위 4: 공급자 정보 준비 함수 분리 (비즈니스 로직)

**대상**: 골드 회원 공급자 선택 분기 로직 (라인 332-381)

**이유**:
1. ✅ **명확한 책임**: 공급자 정보 준비라는 단일 책임
2. ✅ **비즈니스 로직 분리**: 골드 회원 특화 로직을 별도 함수로 분리
3. ✅ **테스트 용이성**: 골드/비골드 시나리오를 독립적으로 테스트 가능

**작업 계획**:
1. `routes/conversion_modules/conversion_helpers.py`에 `prepare_supplier_info()` 함수 추가
2. `user` 딕셔너리와 `selected_customer_id`를 파라미터로 받음
3. 골드 회원 분기 로직을 모두 포함

---

### 우선순위 5: 토큰 잔량 확인 함수 분리 (복잡한 SQL)

**대상**: 토큰 잔량 정밀 확인 로직 (라인 266-293)

**이유**:
1. ⚠️ **복잡한 SQL 로직**: CTE를 사용한 복잡한 쿼리
2. ✅ **재사용성**: 다른 곳에서도 사용 가능
3. ✅ **테스트 용이성**: SQL 로직을 독립적으로 테스트 가능
4. ⚠️ **주의사항**: `get_token_summary_v2()`와 로직이 중복될 수 있으므로 통합 검토 필요

**작업 계획**:
1. `core/token_service.py`에 `get_user_token_balance_from_activity_logs()` 함수 추가
2. 기존 `get_token_summary_v2()`와 로직 통합 검토
3. `start_conversion()`에서 호출

---

### 우선순위 6: 다운로드 함수 이전 (독립적)

**대상**: `download_converted()` 함수 (라인 544-621, 약 78줄)

**이유**:
1. ✅ **완전 독립**: `start_conversion()`과 거의 독립적으로 작동
2. ✅ **명확한 책임**: 파일 다운로드라는 단일 책임
3. ✅ **낮은 복잡도**: 상대적으로 간단한 로직

**작업 계획**:
1. `routes/conversion_modules/conversion_engine_routes.py`에 `download_converted()` 함수 추가
2. `conversion_bp` 대신 `conversion_engine_bp`에 등록
3. `routes/conversion.py`에서 삭제

---

### 우선순위 7: 메인 함수 리팩토링 (최종 단계)

**대상**: `start_conversion()` 함수 전체 (라인 130-541)

**이유**:
1. ⚠️ **가장 복잡함**: 412줄의 거대한 함수
2. ✅ **이미 보조 함수들 분리 완료**: 위 단계들을 완료한 후 진행
3. ✅ **최종 통합**: 모든 보조 함수를 조합하여 메인 함수 구성

**작업 계획**:
1. 위 1-6단계를 모두 완료한 후 진행
2. `routes/conversion_modules/conversion_engine_routes.py`에 새로운 `start_conversion()` 함수 작성
3. 보조 함수들을 조합하여 로직 구성
4. `routes/conversion.py`에서 기존 함수 삭제
5. `app.py`에 `conversion_engine_bp` 등록

---

## 📊 작업 우선순위 요약

| 우선순위 | 대상 | 예상 줄 수 | 복잡도 | 리스크 | 예상 소요 시간 |
|---------|------|-----------|--------|--------|---------------|
| 1 | `_calculate_template_count_precisely()` | 75줄 | 낮음 | 매우 낮음 | 15분 |
| 2 | `normalize_issue_date()` | 20줄 | 낮음 | 매우 낮음 | 10분 |
| 3 | 파라미터 검증 함수 | 30줄 | 중간 | 낮음 | 20분 |
| 4 | 공급자 정보 준비 함수 | 50줄 | 중간 | 낮음 | 30분 |
| 5 | 토큰 잔량 확인 함수 | 30줄 | 높음 | 중간 | 40분 |
| 6 | `download_converted()` | 78줄 | 낮음 | 낮음 | 20분 |
| 7 | `start_conversion()` 리팩토링 | 412줄 | 매우 높음 | 높음 | 2시간 |

**총 예상 소요 시간**: 약 4시간 5분

---

## 🎯 최종 권장사항

### 단계별 접근 전략

1. **1단계 (즉시 시작 가능)**: 우선순위 1, 2, 6을 먼저 완료
   - 헬퍼 함수 이전
   - 날짜 정규화 함수 분리
   - 다운로드 함수 이전
   - **예상 소요 시간**: 45분
   - **리스크**: 매우 낮음

2. **2단계 (안정화 후)**: 우선순위 3, 4 완료
   - 파라미터 검증 함수 분리
   - 공급자 정보 준비 함수 분리
   - **예상 소요 시간**: 50분
   - **리스크**: 낮음

3. **3단계 (신중하게)**: 우선순위 5 완료
   - 토큰 잔량 확인 함수 분리
   - 기존 `get_token_summary_v2()`와 통합 검토
   - **예상 소요 시간**: 40분
   - **리스크**: 중간

4. **4단계 (최종 통합)**: 우선순위 7 완료
   - 메인 함수 리팩토링
   - 모든 보조 함수 통합
   - **예상 소요 시간**: 2시간
   - **리스크**: 높음 (하지만 이전 단계 완료 시 안전)

---

## ✅ 검증 계획

각 단계 완료 후:
1. 서버 재시작 및 기본 기능 테스트
2. 변환 페이지에서 파일 업로드 테스트
3. 변환 시작 버튼 클릭 테스트
4. 다운로드 기능 테스트
5. 토큰 차감 정확성 확인

---

**작전명: 최후의 공성 계획 보고서 완료**

*이 보고서는 분석 및 계획 단계입니다. 실제 코드 수정은 Commander의 승인 후 진행됩니다.*




