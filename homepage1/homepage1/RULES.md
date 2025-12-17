# RohaTax Absolute Rules (v1.0)

## 0. 서버 실행 규칙 (Server Execution)

### 0.1 포트 구분
- **본진 (5000번 포트)**: `start_server_5000.bat` (프로젝트 루트)
- **전초기지 (5001번 포트)**: `start_server_5001.bat` (homepage1 폴더)

### 0.2 실행 원칙
- ✅ **단독 실행**: 한 번에 하나의 서버만 실행 (포트 충돌 방지)
- ✅ **명확한 구분**: 파일명으로 포트 번호를 명시
- ❌ **혼동 금지**: `start_server_simple.bat` 같은 모호한 이름 사용 금지

---

## 1. 상품 및 결제 (Products & Payments)

### 1.1 테이블 구조
- **상품 테이블**: `products` - 모든 상품 정보의 유일한 진실
- **주문 테이블**: `orders` - 모든 결제/주문 기록의 유일한 진실
- **⚠️ 금지**: `product_packages`, `payment_history` 등 이원화된 테이블 사용 금지

### 1.2 상품 유형 (Product Types)
| Type | 설명 | 가격 | 토큰 | 기간 |
|---|---|---|---|---|
| `basic` | 기준 단가 (1개당) | 500원 | 1개 | - |
| `package` | 할인 패키지 | 25,000원 | 100개 | - |
| `subscription` | 무제한 구독 | 70,000원 | -1 (무제한) | 30일 |
| `event` | 무료 토큰 이벤트 | 0원 | 50개 | - |
| `event_period` | 무료 기간 이벤트 | 0원 | 0개 | 3일 |

### 1.3 관리 원칙
- ✅ 상품 추가/수정: **관리자 대시보드 > 상품 관리 탭**에서만 수행
- ✅ 결제 생성: **관리자 대시보드 > 결제 관리 탭**에서 수동 생성 가능
- ✅ 0원 결제: 무료 이벤트 상품도 `orders` 테이블에 정상 기록
- ❌ 직접 DB 수정 금지 (마이그레이션 스크립트 제외)

---

## 2. 마이홈 (My Home)

### 2.1 데이터 소스
- **유일한 진실**: `activity_logs` 테이블
- **금지**: `users.token_balance`를 직접 조회하여 표시 (동기화 문제 발생)

### 2.2 활동 로그 필터링
```javascript
// 탭별 activity_type 매핑
const ACTIVITY_FILTERS = {
  'ALL': null,                    // 전체 보기
  'FINANCIAL': [                  // 💰 금융
    'TOKEN_CHARGE',               // 토큰 충전
    'TOKEN_REFUND',               // 토큰 환불
    'PAYMENT_CANCEL',             // 결제 취소
    'GRADE_CHANGE_BY_ADMIN'       // 등급 변경
  ],
  'ACTIVITY': [                   // 🔄 활동
    'TOKEN_USE',                  // 토큰 사용
    'CONVERSION_SUCCESS',         // 변환 성공
    'CONVERSION_FAIL'             // 변환 실패
  ],
  'SECURITY': [                   // 🔒 보안
    'LOGIN',                      // 로그인
    'LOGOUT',                     // 로그아웃
    'PASSWORD_CHANGE'             // 비밀번호 변경
  ]
};
```

---

## 3. 데이터베이스 (Database)

### 3.1 핵심 테이블
```sql
-- 상품 (Products)
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER DEFAULT 0,
    token_amount INTEGER DEFAULT 0,
    duration_days INTEGER,
    type TEXT NOT NULL,           -- basic, package, subscription, event, event_period
    vat_included INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);

-- 주문 (Orders)
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    order_uid TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',
    amount INTEGER DEFAULT 0,
    token_amount INTEGER DEFAULT 0,
    supply_price INTEGER DEFAULT 0,
    vat INTEGER DEFAULT 0,
    payment_method TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- 활동 로그 (Activity Logs)
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    performed_by_id INTEGER,
    performed_by_type TEXT,       -- USER, ADMIN, SYSTEM
    activity_type TEXT NOT NULL,
    details TEXT,                 -- JSON
    token_change INTEGER DEFAULT 0,
    potential_cost INTEGER DEFAULT 0,
    token_balance_before INTEGER,
    token_balance_after INTEGER,
    user_plan_snapshot TEXT,
    created_at TEXT
);
```

### 3.2 DB 접근 원칙
- ✅ `get_conn_optimized()` 사용 (트랜잭션 자동 관리)
- ✅ `sqlite3.Row` 팩토리 사용 (딕셔너리 접근)
- ❌ 직접 `sqlite3.connect()` 사용 금지

---

## 4. 개발 원칙 (The Roha Way)

### 4.1 패턴 1: 탐정 놀이 (Detective Work)
**수정 전 반드시 확인:**
1. 서버 로그 확인 (`terminals/*.txt`)
2. DB 데이터 확인 (`SELECT * FROM ...`)
3. 브라우저 콘솔 확인 (F12 개발자 도구)
4. 네트워크 요청 확인 (API 응답)

### 4.2 패턴 2: 설계 (Design First)
- 큰 기능은 먼저 구조를 설계한 후 구현
- API 엔드포인트, DB 스키마, UI 흐름을 먼저 정의

### 4.3 패턴 3: 현실 직시 (Face Reality)
- 이상적인 해결책보다 **지금 작동하는 해결책** 우선
- 완벽한 리팩토링보다 **버그 수정** 우선

### 4.4 패턴 4: 안전지대 (Safe Zone)
- 중요한 작업 전 반드시 **커밋** 또는 **백업**
- 위험한 코드는 **테스트 환경**에서 먼저 검증

### 4.5 패턴 5: 쪼개고 정복하기 (Divide & Conquer)
- 큰 문제를 작은 단위로 분해
- 한 번에 하나씩 해결

### 4.6 패턴 6: 역사 기록 (Chronicle)
- 중요한 마일스톤은 `kweon.md`에 기록
- 커밋 메시지는 명확하게 작성
- 형식: `feat(module): 작업 내용`

---

## 5. 코드 스타일 (Code Style)

### 5.1 Python
```python
# Service Layer 패턴 사용
from core.product.service import ProductService

product_service = ProductService()
product = product_service.get_product_by_id(product_id)

# Pydantic 스키마 사용
from core.product.schemas import ProductCreate, ProductResponse

product_data = ProductCreate(**request.json)
```

### 5.2 JavaScript
```javascript
// async/await 사용
async function loadProducts() {
    const response = await fetch('/admin/api/products');
    const result = await response.json();
    return result.data.products;
}

// 에러 처리
try {
    await saveProduct(data);
} catch (error) {
    console.error('[saveProduct] 오류:', error);
    alert('저장 실패: ' + error.message);
}
```

### 5.3 SQL
```sql
-- 명확한 컬럼 명시
SELECT id, name, type, price FROM products WHERE is_active = 1;

-- JOIN 사용 시 테이블 별칭
SELECT 
    p.id, p.name, 
    o.order_uid, o.amount
FROM products p
LEFT JOIN orders o ON p.id = o.product_id;
```

---

## 6. 금지 사항 (Forbidden)

### 6.1 절대 금지
- ❌ `seed_demo()` 호출 (DB 초기화 방지)
- ❌ `init_db()` 무분별한 호출 (데이터 손실 방지)
- ❌ 하드코딩된 ID 사용 (`data-product-id="4"` 금지)
- ❌ 서버 재시작 시 DB 리셋 로직
- ❌ 이중 테이블 사용 (`products` + `product_packages`)

### 6.2 주의 사항
- ⚠️ 브라우저 캐시 문제 (JS/CSS 버전 쿼리 스트링 사용)
- ⚠️ 비동기 타이밍 문제 (`await` 누락)
- ⚠️ CSRF 토큰 누락
- ⚠️ SQL Injection (파라미터 바인딩 사용)

---

## 7. 배포 및 운영 (Deployment)

### 7.1 서버 시작
```bash
# 홈페이지1 (5001번 포트)
cd homepage1
cmd /c start_server_simple.bat

# 메인 서버 (5000번 포트)
cd RohaTax
cmd /c start_server_port.bat
```

### 7.2 로그 확인
- **서버 로그**: `terminals/*.txt`
- **애플리케이션 로그**: `logs/*.log`
- **DB 로그**: `activity_logs` 테이블

### 7.3 백업
- **DB 백업**: `database/app.db` → `database/app.db.bak`
- **코드 백업**: Git 커밋

---

## 8. 문제 해결 (Troubleshooting)

### 8.1 상품이 안 보일 때
1. `products` 테이블 확인: `SELECT * FROM products;`
2. `is_active` 값 확인: `UPDATE products SET is_active = 1 WHERE id = ?;`
3. 브라우저 캐시 삭제 (Ctrl+Shift+R)

### 8.2 결제가 안 될 때
1. 서버 로그 확인 (`terminals/*.txt`)
2. `PaymentService`가 `products` 테이블을 보는지 확인
3. CSRF 토큰 확인

### 8.3 토큰이 안 맞을 때
1. `activity_logs` 테이블 확인: `SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC;`
2. `token_balance_before`와 `token_balance_after` 차이 확인
3. `token_change` 합계 계산

---

**마지막 업데이트**: 2025-11-27 (프로젝트 골든 게이트 완료)
**버전**: v1.0
**작성자**: The Roha Way Team

