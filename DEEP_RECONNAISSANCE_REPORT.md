# 작전명: 심층 정찰 (Operation: Deep Reconnaissance)
## 상세 비교 분석 보고서

---

## 📋 임무 1: 토큰 관리 모듈 비교 분석

### 1-1. `routes/conversion.py`의 `use_token()` 함수

```python
@conversion_bp.route('/api/use-token', methods=['POST'])
def use_token():
    """변환 작업 시 토큰 사용 API"""
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    tokens_to_use = int(data.get('tokens', 1))  # 기본 1토큰
    
    if tokens_to_use <= 0:
        return error('토큰 수량은 1 이상이어야 합니다', status=400)
    
    # 토큰 상태 조회 (중복 제거: token_service 사용)
    token_status = get_user_token_status(user_id)
    if token_status is None:
        return error('사용자를 찾을 수 없습니다', status=404)
    
    available_tokens = token_status['available_tokens']
    
    if available_tokens < tokens_to_use:
        return error(f'토큰이 부족합니다. 사용 가능: {available_tokens}개, 요청: {tokens_to_use}개', status=400)
    
    # 토큰 사용량 업데이트
    with get_conn() as conn:
        new_tokens_used = token_status['tokens_used'] + tokens_to_use
        conn.execute(
            "UPDATE users SET tokens_used = ? WHERE id = ?", 
            (new_tokens_used, user_id)
        )
        conn.commit()
    
    # 업데이트된 잔액 반환
    remaining_tokens = token_status['token_balance'] - new_tokens_used
    
    return success('토큰이 사용되었습니다', data={
        'tokens_used': tokens_to_use,
        'remaining_tokens': remaining_tokens,
        'total_granted': token_status['token_balance'],
        'total_used': new_tokens_used
    })
```

**특징:**
- ✅ `ensure_login_for_json()` 사용 (표준화된 인증)
- ✅ `get_user_token_status()` 사용 (중앙화된 토큰 서비스)
- ✅ 에러 메시지에 상세 정보 포함 (사용 가능 토큰, 요청 토큰)
- ✅ 반환값 필드명: `total_granted`, `total_used`, `remaining_tokens`

---

### 1-2. `routes/conversion_modules/token_routes.py`의 `use_token()` 함수

```python
@token_bp.route('/api/use-token', methods=['POST'])
def use_token():
    """변환 작업 시 토큰 사용 API"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        data = request.get_json()
        tokens_to_use = data.get('tokens', 1)
        
        if not isinstance(tokens_to_use, int) or tokens_to_use <= 0:
            return error("유효하지 않은 토큰 수입니다", 400)
        
        with get_conn() as conn:
            # 현재 사용자 정보 조회
            user = conn.execute(
                "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            # 사용 가능한 토큰 계산
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
            
            if available_tokens < tokens_to_use:
                return error(f"토큰이 부족합니다. 사용 가능: {available_tokens}개", 400)
            
            # 토큰 사용 기록
            new_tokens_used = (user['tokens_used'] or 0) + tokens_to_use
            conn.execute(
                "UPDATE users SET tokens_used = ? WHERE id = ?",
                (new_tokens_used, session['user_id'])
            )
            conn.commit()
            
            # 새로운 토큰 상태 반환
            remaining_tokens = available_tokens - tokens_to_use
            
            return success({
                "tokens_used": tokens_to_use,
                "remaining_tokens": remaining_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": new_tokens_used
            })
            
    except Exception as e:
        return error(f"토큰 사용 중 오류가 발생했습니다: {str(e)}", 500)
```

**특징:**
- ❌ 직접 세션 체크 (`session.get('user_id')`)
- ❌ 직접 DB 쿼리 (중앙화되지 않음)
- ✅ `try-except` 블록으로 예외 처리
- ✅ 타입 검증 (`isinstance(tokens_to_use, int)`)
- ✅ 반환값 필드명: `total_tokens`, `used_tokens`, `remaining_tokens`
- ⚠️ 에러 메시지에 요청 토큰 수 미포함

---

### 1-3. `use_token()` 함수 비교 분석

| 항목 | `conversion.py` | `token_routes.py` | 우위 |
|------|----------------|-------------------|------|
| **인증 방식** | `ensure_login_for_json()` | 직접 세션 체크 | ✅ conversion.py |
| **토큰 조회** | `get_user_token_status()` (중앙화) | 직접 DB 쿼리 | ✅ conversion.py |
| **타입 검증** | `int()` 변환만 | `isinstance()` 체크 | ✅ token_routes.py |
| **예외 처리** | 없음 | `try-except` 블록 | ✅ token_routes.py |
| **에러 메시지** | 상세 (사용 가능/요청 토큰) | 간단 (사용 가능만) | ✅ conversion.py |
| **반환 필드명** | `total_granted`, `total_used` | `total_tokens`, `used_tokens` | ⚠️ 불일치 |
| **코드 품질** | 중앙화된 서비스 사용 | 직접 구현 | ✅ conversion.py |

**결론:** `conversion.py` 버전이 더 최신이고 구조적으로 우수함. 다만 `token_routes.py`의 예외 처리와 타입 검증은 채택 가치 있음.

---

### 1-4. `routes/conversion.py`의 `token_status()` 함수

```python
@conversion_bp.route('/api/token-status', methods=['GET'])
def token_status():
    """현재 토큰 상태 조회 API (캐싱 적용)"""
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        logger.warning("로그인되지 않은 사용자")
        return guard_response

    logger.info(f"토큰상태 요청 - 세션 ID: {user_id}")
    logger.info(f"세션 전체: {dict(session)}")
    logger.info(f"요청 헤더: {dict(request.headers)}")

    # 토큰 잔액 조회 (중복 제거: token_service 사용)
    token_status = get_user_token_status(user_id)
    if token_status is None:
        logger.warning(f"사용자 ID {user_id}를 찾을 수 없음")
        return error('사용자를 찾을 수 없습니다', status=404)
    
    logger.info(f"토큰 상태 조회 성공: Balance={token_status['token_balance']}, Used={token_status['tokens_used']}, Available={token_status['available_tokens']}")
    
    return success('토큰 상태 조회 성공', data={
        'total_granted': token_status['token_balance'],
        'total_used': token_status['tokens_used'],
        'available_tokens': token_status['available_tokens']
    })
```

**특징:**
- ✅ `ensure_login_for_json()` 사용
- ✅ `get_user_token_status()` 사용 (중앙화)
- ✅ 상세한 로깅 (디버깅 용이)
- ✅ 반환값 필드명: `total_granted`, `total_used`, `available_tokens`

---

### 1-5. `routes/conversion_modules/token_routes.py`의 `token_status()` 함수

```python
@token_bp.route('/api/token-status', methods=['GET'])
def token_status():
    """현재 토큰 상태 조회 API (캐싱 적용)"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        with get_conn() as conn:
            user = conn.execute(
                "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
            
            return success({
                "available_tokens": available_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": user['tokens_used'] or 0,
                "timestamp": int(time.time())
            })
            
    except Exception as e:
        return error(f"토큰 상태 조회 중 오류가 발생했습니다: {str(e)}", 500)
```

**특징:**
- ❌ 직접 세션 체크
- ❌ 직접 DB 쿼리 (중앙화되지 않음)
- ✅ `try-except` 블록으로 예외 처리
- ✅ `timestamp` 필드 포함 (추가 정보)
- ✅ 반환값 필드명: `total_tokens`, `used_tokens`, `available_tokens`
- ❌ 로깅 없음

---

### 1-6. `token_status()` 함수 비교 분석

| 항목 | `conversion.py` | `token_routes.py` | 우위 |
|------|----------------|-------------------|------|
| **인증 방식** | `ensure_login_for_json()` | 직접 세션 체크 | ✅ conversion.py |
| **토큰 조회** | `get_user_token_status()` (중앙화) | 직접 DB 쿼리 | ✅ conversion.py |
| **예외 처리** | 없음 | `try-except` 블록 | ✅ token_routes.py |
| **로깅** | 상세한 디버깅 로그 | 없음 | ✅ conversion.py |
| **추가 정보** | 없음 | `timestamp` 필드 | ✅ token_routes.py |
| **반환 필드명** | `total_granted`, `total_used` | `total_tokens`, `used_tokens` | ⚠️ 불일치 |

**결론:** `conversion.py` 버전이 더 최신이고 구조적으로 우수함. 다만 `token_routes.py`의 예외 처리와 `timestamp` 필드는 채택 가치 있음.

---

## 📋 임무 2: 사용자 정보 모듈 비교 분석

### 2-1. `routes/conversion.py`의 `user_info()` 함수

```python
@conversion_bp.route('/api/user-info', methods=['GET'])
def user_info():
    """현재 로그인한 사용자 정보 조회 API"""
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        logger.warning("로그인되지 않은 사용자")
        return guard_response

    logger.info(f"유저정보 요청 - 세션 ID: {user_id}")
    
    # 사용자 정보 조회 (기존 방식으로 복원)
    with get_conn() as conn:
        user = conn.execute(
            """SELECT id, username, email, company_name, business_number,
                      representative_name, phone, address, business_type, business_category,
                      plan_type, monthly_limit, used_count, is_active, is_admin,
                      token_balance, tokens_used, created_at
               FROM users WHERE id = ?""",
            (user_id,)
        ).fetchone()
        
        if not user:
            logger.warning(f"사용자 ID {user_id}를 찾을 수 없음")
            return error('사용자를 찾을 수 없습니다', status=404)
        
        logger.info(f"사용자 정보 조회 성공: {user['username']}")
        
        # 민감한 정보는 제외하고 필요한 정보만 반환
        safe_user_data = {
            'id': row_value(user, 'id'),
            'username': row_value(user, 'username', ''),
            'email': row_value(user, 'email', ''),
            'company_name': row_value(user, 'company_name', ''),
            'business_number': row_value(user, 'business_number', ''),
            'representative_name': row_value(user, 'representative_name', ''),
            'phone': row_value(user, 'phone', ''),
            'address': row_value(user, 'address', ''),
            'business_type': row_value(user, 'business_type', ''),
            'business_category': row_value(user, 'business_category', ''),
            'plan_type': row_value(user, 'plan_type', ''),
            'monthly_limit': row_value(user, 'monthly_limit', 0),
            'used_count': row_value(user, 'used_count', 0),
            'is_active': bool(row_value(user, 'is_active', 0)),
            'is_admin': bool(row_value(user, 'is_admin', 0)),
            'token_balance': row_value(user, 'token_balance', 0) or 0,
            'tokens_used': row_value(user, 'tokens_used', 0) or 0,
            'created_at': row_value(user, 'created_at', '')
        }
        
        return success('사용자 정보 조회 성공', data={'user': safe_user_data})
```

**반환 필드 (18개):**
1. `id`
2. `username`
3. `email`
4. `company_name`
5. `business_number`
6. `representative_name`
7. `phone`
8. `address`
9. `business_type`
10. `business_category`
11. `plan_type`
12. `monthly_limit`
13. `used_count`
14. `is_active`
15. `is_admin`
16. `token_balance`
17. `tokens_used`
18. `created_at`

**특징:**
- ✅ `ensure_login_for_json()` 사용
- ✅ 상세한 로깅
- ✅ `row_value()` 함수 사용 (안전한 데이터 접근)
- ✅ 18개 필드 (완전한 사용자 정보)
- ✅ 비즈니스 정보 포함 (회사명, 사업자번호, 대표자명 등)

---

### 2-2. `routes/conversion_modules/user_routes.py`의 `user_info()` 함수

```python
@user_bp.route('/api/user-info', methods=['GET'])
def user_info():
    """현재 로그인한 사용자 정보 조회 API"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        with get_conn() as conn:
            user = conn.execute(
                "SELECT id, username, email, token_balance, COALESCE(tokens_used, 0) as tokens_used, created_at FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)

            # 호환성을 위해 평탄/중첩 구조를 동시에 반환
            payload = {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "available_tokens": available_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": user['tokens_used'] or 0,
                "created_at": user['created_at']
            }
            return success({
                **payload,
                "user": payload,
            })
```

**반환 필드 (7개):**
1. `id`
2. `username`
3. `email`
4. `available_tokens` (계산된 값)
5. `total_tokens`
6. `used_tokens`
7. `created_at`

**특징:**
- ❌ 직접 세션 체크
- ❌ 로깅 없음
- ✅ `try-except` 블록으로 예외 처리
- ✅ `available_tokens` 계산 포함
- ✅ 평탄/중첩 구조 동시 반환 (호환성)
- ❌ 7개 필드만 (기본 정보만)
- ❌ 비즈니스 정보 없음

---

### 2-3. `user_info()` 함수 비교 분석

| 항목 | `conversion.py` | `user_routes.py` | 우위 |
|------|----------------|------------------|------|
| **인증 방식** | `ensure_login_for_json()` | 직접 세션 체크 | ✅ conversion.py |
| **로깅** | 상세한 디버깅 로그 | 없음 | ✅ conversion.py |
| **예외 처리** | 없음 | `try-except` 블록 | ✅ user_routes.py |
| **반환 필드 수** | 18개 | 7개 | ✅ conversion.py |
| **비즈니스 정보** | 포함 (회사명, 사업자번호 등) | 없음 | ✅ conversion.py |
| **토큰 정보** | `token_balance`, `tokens_used` | `total_tokens`, `used_tokens`, `available_tokens` | ⚠️ 불일치 |
| **데이터 안전성** | `row_value()` 사용 | 직접 접근 | ✅ conversion.py |
| **응답 구조** | `{success: true, data: {user: {...}}}` | 평탄/중첩 혼합 | ⚠️ 불일치 |

**결론:** `conversion.py` 버전이 훨씬 더 완전하고 상세한 정보를 제공함. 다만 `user_routes.py`의 예외 처리는 채택 가치 있음.

---

## 🎯 통합 방안 제안

### 토큰 관리 모듈 통합 방안

**최선의 방안:**
1. **기준 버전:** `conversion.py` 버전을 기준으로 사용
2. **개선 사항 채택:**
   - `token_routes.py`의 `try-except` 예외 처리 추가
   - `token_routes.py`의 타입 검증 (`isinstance`) 추가
   - `token_status()`에 `timestamp` 필드 추가
3. **통합 위치:** `routes/conversion_modules/token_routes.py`로 통합
4. **변경 사항:**
   - `conversion.py`에서 `use_token()`, `token_status()` 삭제
   - `token_routes.py`에 개선된 버전으로 통합
   - `conversion.py`에서 `from .conversion_modules.token_routes import use_token, token_status` import

**예상 효과:**
- 코드 중복 제거
- 중앙화된 토큰 서비스 활용
- 예외 처리 강화
- 일관된 API 응답 형식

---

### 사용자 정보 모듈 통합 방안

**최선의 방안:**
1. **기준 버전:** `conversion.py` 버전을 기준으로 사용 (18개 필드)
2. **개선 사항 채택:**
   - `user_routes.py`의 `try-except` 예외 처리 추가
   - `available_tokens` 계산 필드 추가 (선택적)
3. **통합 위치:** `routes/conversion_modules/user_routes.py`로 통합
4. **변경 사항:**
   - `conversion.py`에서 `user_info()` 삭제
   - `user_routes.py`에 개선된 버전으로 통합
   - `conversion.py`에서 `from .conversion_modules.user_routes import user_info` import

**예상 효과:**
- 코드 중복 제거
- 완전한 사용자 정보 제공
- 예외 처리 강화
- 일관된 API 응답 형식

---

## 📊 최종 권고사항

### 우선순위
1. **높음:** 사용자 정보 모듈 통합 (더 큰 차이)
2. **중간:** 토큰 관리 모듈 통합 (기능적 차이는 작지만 구조적 개선)

### 주의사항
- 두 모듈 모두 동일한 엔드포인트를 사용하므로, 통합 시 Blueprint 등록 순서 확인 필요
- 프론트엔드에서 사용하는 필드명 확인 필요 (`total_granted` vs `total_tokens`)
- 통합 후 기존 API 호출이 정상 작동하는지 검증 필요

---

**작전 완료 시간:** 2025-11-14
**분석자:** AI Assistant
**상태:** ✅ 분석 완료, 통합 대기 중




