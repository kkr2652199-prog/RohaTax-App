# 작전명: 최후의 자문 (Operation: The Final Counsel)
## 상용화 전략 종합 분석 보고서

**생성일**: 2025-11-16  
**분석 범위**: RohaTax 애플리케이션 전체 구조  
**목표**: 상용화 환경에서의 붕괴 지점 식별 및 필수 조치 제안

---

## 📊 1. 현재 구조의 '상용화' 스트레스 테스트

### 🔴 **1순위: 데이터베이스 연결 관리 - 치명적 붕괴 지점**

#### **현재 상태**
- **데이터베이스**: SQLite (단일 파일 기반)
- **연결 방식**: 요청마다 새 연결 생성 후 즉시 닫기 (`get_conn_optimized()`)
- **사용 빈도**: **108개 파일**에서 `get_conn()` 또는 `get_conn_optimized()` 사용
- **커넥션 풀**: **없음**

#### **100배/1000배 사용자 증가 시 예상 붕괴 시나리오**

**시나리오 1: 동시 연결 고갈 (즉시 발생)**
```
현재: 1명 사용자 → 1개 연결
100배: 100명 동시 사용자 → 100개 동시 연결
1000배: 1000명 동시 사용자 → 1000개 동시 연결

SQLite 동시 쓰기 제한: 약 100-200개 (WAL 모드 기준)
예상 붕괴 시점: 약 150명 동시 사용자
붕괴 증상: 
  - "database is locked" 오류
  - 요청 타임아웃
  - 전체 서비스 중단
```

**시나리오 2: 파일 I/O 병목 (중기 발생)**
```
SQLite는 단일 파일에 모든 데이터 저장
1000명 동시 사용 시:
  - 읽기/쓰기 경합 극심
  - 디스크 I/O 대기 시간 급증
  - 응답 시간: 100ms → 5초 이상
```

**시나리오 3: 데이터베이스 파일 크기 제한 (장기 발생)**
```
SQLite 최대 파일 크기: 약 281TB (이론적)
실제 권장 크기: 10GB 이하
1000명 사용자 × 100건/월 × 1MB/건 = 100GB/월
예상 붕괴 시점: 약 3-6개월
```

#### **유지보수 지옥 지수: ⭐⭐⭐⭐⭐ (최악)**

**파일**: `core/db.py` (414줄)
- **문제점 1**: 108개 파일에서 직접 호출 → 변경 시 전체 수정 필요
- **문제점 2**: 연결 생성 로직이 각 파일에 분산 → 일관성 없음
- **문제점 3**: 에러 처리 방식이 파일마다 다름 → 디버깅 어려움
- **문제점 4**: 성능 최적화 설정이 매번 반복 실행 → 불필요한 오버헤드

---

### 🟠 **2순위: 세션 관리 - 메모리 고갈**

#### **현재 상태**
- **세션 저장소**: Flask 기본 세션 (메모리 기반)
- **세션 영구화**: `session.permanent = True` (24시간)
- **세션 저장 위치**: 서버 메모리 (Redis/DB 없음)

#### **100배/1000배 사용자 증가 시 예상 붕괴 시나리오**

**시나리오 1: 서버 메모리 고갈 (즉시 발생)**
```
세션 데이터 크기: 약 500 bytes/세션
1000명 동시 사용자:
  - 메모리 사용량: 1000 × 500 bytes = 500KB (세션만)
  - 실제로는 더 큼 (세션 객체 오버헤드 포함)
  
문제점:
  - 서버 재시작 시 모든 세션 손실
  - 로드 밸런싱 불가능 (세션 공유 불가)
  - 메모리 누수 위험
```

**시나리오 2: 세션 쿠키 크기 제한**
```
Flask 세션 쿠키 크기 제한: 약 4KB
세션 데이터가 커지면 쿠키 전송 실패
```

#### **유지보수 지옥 지수: ⭐⭐⭐⭐ (높음)**

**파일**: `app.py` (라인 180-189)
- **문제점**: 세션 설정이 하드코딩되어 있음
- **문제점**: 세션 저장소 변경 시 전체 앱 수정 필요

---

### 🟡 **3순위: 파일 처리 - 디스크 공간 및 I/O 병목**

#### **현재 상태**
- **파일 업로드**: 로컬 디스크 (`uploads/` 폴더)
- **파일 크기 제한**: 50MB
- **파일 정리**: 자동 정리 시스템 존재 (`core/file_manager.py`)

#### **100배/1000배 사용자 증가 시 예상 붕괴 시나리오**

**시나리오 1: 디스크 공간 고갈**
```
1000명 사용자 × 10건/일 × 10MB/건 = 100GB/일
예상 붕괴 시점: 약 1주일 (1TB 디스크 기준)
```

**시나리오 2: 동시 파일 I/O 경합**
```
1000명 동시 업로드:
  - 디스크 쓰기 대기 시간 급증
  - 파일 시스템 락 경합
  - 응답 시간: 2초 → 30초 이상
```

#### **유지보수 지옥 지수: ⭐⭐⭐ (중간)**

**파일**: `core/file_manager.py` (559줄)
- **문제점**: 파일 정리 로직이 복잡함
- **문제점**: 파일 경로가 하드코딩되어 있음

---

### 🟡 **4순위: 대용량 파일 처리 - 메모리 및 CPU 병목**

#### **현재 상태**
- **파일 파싱**: 동기 처리 (요청 스레드에서 직접 실행)
- **병렬 처리**: `core/parallel_processor.py` 존재하나 실제 사용 여부 불명확
- **큐 시스템**: 없음 (동기 처리)

#### **100배/1000배 사용자 증가 시 예상 붕괴 시나리오**

**시나리오 1: 요청 스레드 고갈**
```
Flask 기본 스레드 풀: 약 40개
1000명 동시 변환 요청:
  - 모든 스레드가 파일 처리에 점유
  - 새로운 요청 대기
  - 타임아웃 발생
```

**시나리오 2: 메모리 고갈**
```
50MB 파일 × 1000명 동시 처리 = 50GB 메모리 필요
실제 서버 메모리: 8-16GB
예상 붕괴 시점: 약 200명 동시 사용자
```

#### **유지보수 지옥 지수: ⭐⭐⭐⭐ (높음)**

**파일**: `core/conversion_engine.py` (704줄)
- **문제점**: 동기 처리로 인한 응답 지연
- **문제점**: 에러 발생 시 전체 요청 실패

---

### 🟢 **5순위: 코드 구조 - 유지보수 어려움**

#### **현재 상태**
- **큰 파일들**: 21개 파일이 500줄 규칙 위반
- **최악의 파일**: `static/css/homepage.css` (3,800줄)
- **중복 코드**: `_row_value()` 함수가 6곳에 중복

#### **100배/1000배 사용자 증가 시 예상 붕괴 시나리오**

**시나리오 1: 버그 수정 시간 급증**
```
3,800줄 CSS 파일에서 버그 수정:
  - 버그 위치 찾기: 30분
  - 수정: 10분
  - 테스트: 20분
  - 총 소요 시간: 1시간

500줄 파일로 분할 시:
  - 버그 위치 찾기: 5분
  - 수정: 5분
  - 테스트: 10분
  - 총 소요 시간: 20분
```

**시나리오 2: 기능 추가 시 부작용**
```
큰 파일에 기능 추가:
  - 기존 코드와의 충돌 가능성 높음
  - 테스트 범위 넓어짐
  - 리뷰 시간 증가
```

#### **유지보수 지옥 지수: ⭐⭐⭐ (중간)**

**파일**: `static/css/homepage.css` (3,800줄), `templates/profile_edit.html` (2,102줄)
- **문제점**: 파일이 너무 커서 수정이 어려움
- **문제점**: Git 충돌 가능성 높음

---

## 🛡️ 2. '상용화'를 위한 필수 조치 목록

### **🔴 최우선 (결제 시스템 구축 전 필수)**

#### **1. 데이터베이스 마이그레이션: SQLite → PostgreSQL/MySQL**

**우선순위**: ⭐⭐⭐⭐⭐ (최우선)  
**예상 소요 시간**: 2-3주  
**예상 비용**: 서버 인프라 비용 증가 (월 $50-200)

**작업 내용**:
1. PostgreSQL/MySQL 데이터베이스 서버 구축
2. `core/db.py`를 SQLAlchemy ORM으로 전환
3. 커넥션 풀링 도입 (SQLAlchemy `create_engine` with pool)
4. 모든 `get_conn()` 호출을 ORM 세션으로 변경
5. 마이그레이션 스크립트 작성 및 실행

**기대 효과**:
- 동시 연결 제한 해소 (1000+ 연결 지원)
- 읽기/쓰기 성능 향상 (10배 이상)
- 데이터베이스 크기 제한 해소

**위험도**: 중간 (데이터 마이그레이션 필요)

---

#### **2. 세션 저장소 변경: 메모리 → Redis**

**우선순위**: ⭐⭐⭐⭐⭐ (최우선)  
**예상 소요 시간**: 1주  
**예상 비용**: Redis 서버 비용 (월 $20-50)

**작업 내용**:
1. Redis 서버 구축
2. Flask-Session 또는 Flask-KVSession 도입
3. `app.py`의 세션 설정을 Redis로 변경
4. 세션 만료 정책 설정

**기대 효과**:
- 서버 재시작 시 세션 유지
- 로드 밸런싱 가능
- 메모리 사용량 감소

**위험도**: 낮음 (기존 세션은 손실되지만 사용자 재로그인으로 해결)

---

#### **3. 비동기 작업 큐 시스템 도입: Celery + Redis**

**우선순위**: ⭐⭐⭐⭐ (높음)  
**예상 소요 시간**: 2주  
**예상 비용**: 추가 워커 서버 (월 $50-100)

**작업 내용**:
1. Celery 설치 및 설정
2. Redis를 메시지 브로커로 사용
3. 파일 변환 작업을 비동기 큐로 이동
4. 작업 상태 조회 API 구현
5. 워커 프로세스 구축

**기대 효과**:
- 요청 스레드 고갈 방지
- 대용량 파일 처리 가능
- 작업 재시도 및 실패 처리

**위험도**: 중간 (기존 동기 처리 로직을 비동기로 전환 필요)

---

### **🟠 높은 우선순위 (결제 시스템 구축 전 권장)**

#### **4. 파일 저장소 마이그레이션: 로컬 디스크 → 클라우드 스토리지 (S3/GCS)**

**우선순위**: ⭐⭐⭐⭐ (높음)  
**예상 소요 시간**: 1주  
**예상 비용**: 클라우드 스토리지 비용 (월 $10-50, 사용량에 따라)

**작업 내용**:
1. AWS S3 또는 Google Cloud Storage 설정
2. `core/file_manager.py`를 클라우드 스토리지로 변경
3. 파일 업로드/다운로드 로직 수정
4. 자동 정리 정책 설정

**기대 효과**:
- 디스크 공간 제한 해소
- 확장성 향상
- 백업 자동화

**위험도**: 낮음 (기존 파일은 마이그레이션 필요)

---

#### **5. 로드 밸런싱 및 수평 확장 준비**

**우선순위**: ⭐⭐⭐ (중간)  
**예상 소요 시간**: 1주  
**예상 비용**: 추가 서버 (월 $50-200)

**작업 내용**:
1. Nginx 로드 밸런서 설정
2. 여러 Flask 서버 인스턴스 실행
3. 세션 공유 확인 (Redis 사용)
4. 정적 파일 CDN 설정

**기대 효과**:
- 트래픽 분산
- 서버 장애 시 자동 전환
- 성능 향상

**위험도**: 낮음 (기존 코드 변경 최소)

---

#### **6. 모니터링 및 로깅 시스템 구축**

**우선순위**: ⭐⭐⭐ (중간)  
**예상 소요 시간**: 1주  
**예상 비용**: 모니터링 서비스 (월 $10-50)

**작업 내용**:
1. Prometheus + Grafana 설정
2. 애플리케이션 메트릭 수집
3. 알림 시스템 구축
4. 로그 집중화 (ELK Stack 또는 CloudWatch)

**기대 효과**:
- 문제 조기 발견
- 성능 모니터링
- 디버깅 시간 단축

**위험도**: 낮음 (기존 코드에 미미한 변경)

---

### **🟡 중간 우선순위 (결제 시스템 구축 후 개선)**

#### **7. 코드 리팩토링: 큰 파일 분할**

**우선순위**: ⭐⭐⭐ (중간)  
**예상 소요 시간**: 4주  
**예상 비용**: 개발 시간

**작업 내용**:
1. `static/css/homepage.css` (3,800줄) → 컴포넌트별 분할
2. `templates/profile_edit.html` (2,102줄) → partials 분할
3. `static/js/conversion.js` (1,303줄) → 모듈 분할
4. 중복 코드 제거 (`_row_value()` 공통화)

**기대 효과**:
- 유지보수 시간 단축
- 버그 수정 시간 감소
- 코드 리뷰 시간 단축

**위험도**: 낮음 (기능 변경 없음)

---

#### **8. API 버전 관리 시스템 도입**

**우선순위**: ⭐⭐ (낮음)  
**예상 소요 시간**: 1주  
**예상 비용**: 개발 시간

**작업 내용**:
1. API 버전 네임스페이스 도입 (`/api/v1/`, `/api/v2/`)
2. 기존 API를 v1으로 마이그레이션
3. 새로운 API는 v2로 개발

**기대 효과**:
- 하위 호환성 유지
- 점진적 업그레이드 가능

**위험도**: 낮음 (기존 API 유지)

---

## 🎯 3. '대동맥' 작전 계획 평가

### **현재 계획 분석**

**제안된 테이블 구조**:
- `products`: 상품 정보
- `purchases`: 구매 기록
- `subscriptions`: 구독 정보

**기존 테이블 구조** (이미 존재):
- `subscription_plans`: 구독 플랜 정의
- `user_subscriptions`: 사용자 구독 상태

---

### **✅ 계획의 강점**

1. **명확한 데이터 모델**: 상품, 구매, 구독의 분리가 명확함
2. **확장성**: 새로운 상품 추가가 용이함
3. **감사 추적**: 구매 기록을 영구 보관

---

### **⚠️ 계획의 부족한 부분**

#### **1. 결제 게이트웨이 통합 부재**

**문제점**:
- `purchases` 테이블은 구매 기록만 저장
- 실제 결제 처리는 어디서?
- 결제 실패/환불 처리는?

**제안**:
```python
# 추가 테이블 필요
CREATE TABLE payment_transactions (
    id INTEGER PRIMARY KEY,
    purchase_id INTEGER,  -- purchases 테이블 참조
    payment_gateway TEXT,  -- 'iamport', 'toss', 'kakaopay'
    transaction_id TEXT,  -- 결제사 거래 ID
    amount INTEGER,
    status TEXT,  -- 'pending', 'completed', 'failed', 'refunded'
    paid_at TEXT,
    refunded_at TEXT,
    FOREIGN KEY(purchase_id) REFERENCES purchases(id)
);
```

---

#### **2. 구독 갱신 자동화 시스템 부재**

**문제점**:
- `user_subscriptions`에 `auto_renew` 필드는 있음
- 하지만 실제 자동 갱신 로직은?

**제안**:
```python
# Celery 스케줄러 작업 추가
@celery.task
def process_subscription_renewals():
    """만료 예정 구독 자동 갱신"""
    # 1. 만료 3일 전 구독 조회
    # 2. auto_renew=True인 구독 필터링
    # 3. 결제 정보로 자동 결제 시도
    # 4. 성공 시 구독 연장, 실패 시 알림
```

---

#### **3. 환불 및 취소 처리 로직 부재**

**문제점**:
- 구독 취소는?
- 부분 환불은?
- 구독 중도 해지 시 남은 기간 계산은?

**제안**:
```python
# purchases 테이블에 추가 필드
ALTER TABLE purchases ADD COLUMN refund_status TEXT;
ALTER TABLE purchases ADD COLUMN refunded_amount INTEGER;
ALTER TABLE purchases ADD COLUMN refunded_at TEXT;

# 구독 취소 로직
def cancel_subscription(user_id, subscription_id):
    # 1. 남은 기간 계산
    # 2. 부분 환불 금액 계산
    # 3. 결제사 환불 API 호출
    # 4. 구독 상태를 'cancelled'로 변경
    # 5. 환불 기록 저장
```

---

#### **4. 토큰 시스템과의 통합 부재**

**문제점**:
- 구독 구매 시 토큰 지급은?
- 구독 만료 시 토큰 회수는?
- 토큰 잔액과 구독 상태 동기화는?

**제안**:
```python
# purchase_subscription() 함수 수정
def purchase_subscription(user_id, plan_id):
    # 1. 구독 플랜 정보 조회
    # 2. 결제 처리
    # 3. 구독 생성
    # 4. 토큰 지급 (activity_logs에 기록)
    # 5. 사용자 plan_type 업데이트
```

---

#### **5. 테스트 및 검증 시스템 부재**

**문제점**:
- 결제 시스템은 실패 시 금전적 손실
- 테스트 환경 구축은?

**제안**:
```python
# 결제 게이트웨이 샌드박스 모드
PAYMENT_GATEWAY_MODE = os.getenv('PAYMENT_GATEWAY_MODE', 'sandbox')
# sandbox: 테스트 결제
# production: 실제 결제

# 결제 검증 로직
def verify_payment(transaction_id):
    # 1. 결제사 API로 거래 확인
    # 2. 금액 일치 확인
    # 3. 중복 결제 방지
    # 4. 결제 완료 처리
```

---

### **🔧 개선된 '대동맥' 작전 계획**

#### **Phase 1: 데이터베이스 스키마 확장 (1주)**

```sql
-- 기존 테이블 활용
-- subscription_plans (이미 존재)
-- user_subscriptions (이미 존재)

-- 새로 추가할 테이블
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    product_type TEXT NOT NULL,  -- 'subscription', 'token_pack', 'one_time'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE purchases (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER,
    subscription_id INTEGER,  -- user_subscriptions 참조 (구독 구매 시)
    amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'completed', 'failed', 'cancelled'
    payment_method TEXT,  -- 'card', 'bank_transfer', 'virtual_account'
    purchased_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(subscription_id) REFERENCES user_subscriptions(id)
);

CREATE TABLE payment_transactions (
    id INTEGER PRIMARY KEY,
    purchase_id INTEGER NOT NULL,
    payment_gateway TEXT NOT NULL,  -- 'iamport', 'toss', 'kakaopay'
    transaction_id TEXT UNIQUE,  -- 결제사 거래 ID
    amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    paid_at TEXT,
    refunded_at TEXT,
    refund_amount INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY(purchase_id) REFERENCES purchases(id)
);

-- 인덱스
CREATE INDEX idx_purchases_user_id ON purchases(user_id);
CREATE INDEX idx_purchases_status ON purchases(status);
CREATE INDEX idx_payment_transactions_purchase_id ON payment_transactions(purchase_id);
CREATE INDEX idx_payment_transactions_transaction_id ON payment_transactions(transaction_id);
```

---

#### **Phase 2: 결제 게이트웨이 통합 (2주)**

```python
# core/payment_gateway.py (새 파일)
class PaymentGateway:
    def __init__(self, gateway_name='iamport'):
        self.gateway = gateway_name
        self.mode = os.getenv('PAYMENT_GATEWAY_MODE', 'sandbox')
    
    def process_payment(self, purchase_id, amount, payment_method):
        """결제 처리"""
        # 1. 결제사 API 호출
        # 2. 결제 결과 저장 (payment_transactions)
        # 3. purchases.status 업데이트
        # 4. 구독/토큰 지급
        pass
    
    def verify_payment(self, transaction_id):
        """결제 검증 (웹훅용)"""
        # 1. 결제사 API로 거래 확인
        # 2. 중복 처리 방지
        # 3. 금액 일치 확인
        pass
    
    def refund_payment(self, transaction_id, amount=None):
        """환불 처리"""
        # 1. 결제사 환불 API 호출
        # 2. 환불 기록 저장
        # 3. 구독/토큰 회수
        pass
```

---

#### **Phase 3: 구독 자동 갱신 시스템 (1주)**

```python
# core/subscription_renewal.py (새 파일)
@celery.task
def process_subscription_renewals():
    """구독 자동 갱신 처리"""
    # 1. 만료 3일 전 구독 조회
    # 2. auto_renew=True인 구독 필터링
    # 3. 결제 정보로 자동 결제 시도
    # 4. 성공 시 구독 연장, 실패 시 알림
    pass

# Celery 스케줄러 설정
from celery.schedules import crontab

app.conf.beat_schedule = {
    'process-subscription-renewals': {
        'task': 'core.subscription_renewal.process_subscription_renewals',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
    },
}
```

---

#### **Phase 4: 토큰 시스템 통합 (1주)**

```python
# core/subscription_utils.py 수정
def purchase_subscription(user_id, plan_id):
    # 1. 구독 플랜 정보 조회
    # 2. 결제 처리 (PaymentGateway 사용)
    # 3. 구독 생성 (user_subscriptions)
    # 4. 토큰 지급 (token_service 사용)
    # 5. activity_logs에 기록
    # 6. 사용자 plan_type 업데이트
    pass

def cancel_subscription(user_id, subscription_id):
    # 1. 남은 기간 계산
    # 2. 부분 환불 금액 계산
    # 3. 환불 처리 (PaymentGateway 사용)
    # 4. 토큰 회수 (필요 시)
    # 5. 구독 상태를 'cancelled'로 변경
    pass
```

---

### **📊 최종 평가: '대동맥' 작전 계획**

| 평가 항목 | 점수 | 평가 |
|----------|------|------|
| **데이터 모델 설계** | 85/100 | 우수 (명확한 구조) |
| **결제 통합** | 40/100 | 부족 (게이트웨이 통합 필요) |
| **자동화 시스템** | 30/100 | 부족 (갱신 자동화 필요) |
| **에러 처리** | 50/100 | 보통 (환불/취소 로직 필요) |
| **토큰 시스템 통합** | 60/100 | 보통 (통합 로직 필요) |
| **테스트 가능성** | 40/100 | 부족 (샌드박스 모드 필요) |

**종합 점수**: 50.8/100 (보통)

---

### **✅ 개선 제안 요약**

1. **결제 게이트웨이 통합 필수**: `payment_transactions` 테이블 추가
2. **자동 갱신 시스템 필수**: Celery 스케줄러 작업 추가
3. **환불/취소 로직 필수**: 부분 환불 및 중도 해지 처리
4. **토큰 시스템 통합 필수**: 구독 구매 시 토큰 지급/회수 로직
5. **테스트 환경 구축 필수**: 샌드박스 모드 및 테스트 시나리오

---

## 🎯 최종 권고사항

### **결제 시스템 구축 전 필수 작업 (우선순위 순)**

1. **데이터베이스 마이그레이션** (SQLite → PostgreSQL) - **2-3주**
2. **세션 저장소 변경** (메모리 → Redis) - **1주**
3. **비동기 작업 큐 도입** (Celery + Redis) - **2주**
4. **파일 저장소 마이그레이션** (로컬 → S3/GCS) - **1주**
5. **모니터링 시스템 구축** - **1주**

**총 예상 소요 시간**: 7-9주  
**총 예상 비용**: 월 $140-500 (인프라)

---

### **'대동맥' 작전 계획 보완 작업**

1. **결제 게이트웨이 통합** - **2주**
2. **구독 자동 갱신 시스템** - **1주**
3. **환불/취소 로직** - **1주**
4. **토큰 시스템 통합** - **1주**
5. **테스트 환경 구축** - **1주**

**총 예상 소요 시간**: 6주

---

### **최종 타임라인 제안**

```
Week 1-3: 데이터베이스 마이그레이션 (PostgreSQL)
Week 4: 세션 저장소 변경 (Redis)
Week 5-6: 비동기 작업 큐 도입 (Celery)
Week 7: 파일 저장소 마이그레이션 (S3/GCS)
Week 8: 모니터링 시스템 구축
Week 9-10: 결제 게이트웨이 통합
Week 11: 구독 자동 갱신 시스템
Week 12: 환불/취소 로직
Week 13: 토큰 시스템 통합
Week 14: 테스트 환경 구축 및 최종 검증
```

**총 소요 시간**: 14주 (약 3.5개월)

---

## 🚨 최종 경고

### **결제 시스템을 먼저 구축하면 안 되는 이유**

1. **데이터베이스 붕괴**: 150명 동시 사용자에서 서비스 중단
2. **세션 손실**: 서버 재시작 시 모든 사용자 로그아웃
3. **파일 처리 병목**: 대용량 파일 처리 시 전체 서비스 마비
4. **확장 불가능**: 수평 확장 불가능한 구조

**결론**: 결제 시스템을 구축하기 전에, 위의 필수 조치들을 먼저 완료해야 합니다. 그렇지 않으면 결제 시스템이 구축되어도 서비스가 붕괴될 것입니다.

---

**보고서 작성자**: AI 전략 고문  
**작성일**: 2025-11-16  
**다음 검토일**: 필수 조치 완료 후

