# 🔍 기존 2D 멤버십 페이지 → 3D 쇼룸 판매 로직 이식 분석 보고서

## 📊 분석 결과 요약

### 1. 데이터 전달 방식 (Flask → HTML)

#### 백엔드 (`routes/payment_routes.py`)

**함수:** `_build_shop_context()` (26-92줄)

**반환하는 Context 변수:**
```python
{
    'products': products_list,              # 전체 상품 리스트
    'event_products': event_products,        # 이벤트 상품만 필터링
    'regular_products': regular_products,    # 일반 상품만 필터링
    'discount_rate': discount_rate,          # Premium 할인율 (%)
    'premium_per_token_price': premium_per_token_price,  # Premium 토큰당 가격
    'user_info': user_info                   # 사용자 정보
}
```

**HTML 템플릿에서 사용하는 변수명:**

1. **이벤트 상품 (Event Products):**
   ```jinja2
   {% for product in event_products %}
       {{ product.id }}
       {{ product.name }}
       {{ product.price }}
       {{ product.token_amount }}
       {{ product.duration_days }}
       {{ product.type }}
   {% endfor %}
   ```

2. **일반 상품 (Regular Products):**
   ```jinja2
   {% for product in regular_products %}
       {{ product.name }}
       {{ product.price }}
       {{ discount_rate }}              # Premium 상품 할인율
       {{ premium_per_token_price }}     # Premium 토큰당 가격
   {% endfor %}
   ```

---

### 2. 상품별 식별자 (Product Mapping)

#### DB 테이블 구조 (`products` 테이블)
```sql
- id: INTEGER (PRIMARY KEY)
- name: TEXT (예: 'Standard', 'Premium', 'Gold')
- type: TEXT (예: 'basic', 'package', 'subscription', 'event', 'event_period')
- price: INTEGER
- token_amount: INTEGER (무제한은 -1)
- duration_days: INTEGER
- is_active: INTEGER (0 또는 1)
```

#### HTML에서 상품 구분 방법

**1. 이벤트 상품 (Event 1/2):**
```jinja2
{% if product.type in ['event', 'event_period'] %}
    <!-- 이벤트 상품 렌더링 -->
{% endif %}
```

**2. Standard 상품:**
```jinja2
{% if product.name|lower|replace(' ', '') == 'standard' %}
    <!-- Standard 상품 렌더링 -->
{% endif %}
```

**3. Premium 상품:**
```jinja2
{% if product.name|lower|replace(' ', '') == 'premium' %}
    <!-- Premium 상품 렌더링 -->
    {{ discount_rate }}% SAVE  <!-- 할인율 표시 -->
{% endif %}
```

**4. Gold 상품:**
```jinja2
{% if product.name|lower|replace(' ', '') == 'gold' %}
    <!-- Gold 상품 렌더링 -->
{% endif %}
```

**핵심 식별자:**
- **Standard**: `product.name` = `'Standard'` (대소문자 무시, 공백 제거)
- **Premium**: `product.name` = `'Premium'` (대소문자 무시, 공백 제거)
- **Gold**: `product.name` = `'Gold'` (대소문자 무시, 공백 제거)
- **Event 1/2**: `product.type` = `'event'` 또는 `'event_period'`

---

### 3. 구매 트리거 (Purchase Logic)

#### 구매 버튼 HTML 구조 (`shop.html`)

**이벤트 상품 버튼:**
```html
<button class="btn-purchase" 
        data-id="{{ product.id }}"
        data-name="{{ product.name }}"
        data-price="{{ product.price or 0 }}"
        data-type="{{ product.type }}"
        data-token="{{ product.token_amount or 0 }}"
        data-duration="{{ product.duration_days or 0 }}">
    선택하기
</button>
```

**일반 상품 버튼:**
```html
<button class="btn-purchase" 
        data-id="{{ product.id }}"
        data-name="{{ product.name }}"
        data-price="{{ product.price or 0 }}"
        data-type="{{ product.type }}"
        data-token="{{ product.token_amount or 0 }}"
        data-duration="{{ product.duration_days or 0 }}">
    구매하기
</button>
```

#### JavaScript 구매 프로세스 (`static/js/payment/shop.js`)

**1단계: 버튼 클릭 → 모달 열기**
```javascript
// 이벤트 리스너 (675-688줄)
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-purchase')) {
        e.preventDefault();
        openCheckoutModal(e.target);  // ← 여기서 호출
    }
});
```

**2단계: 모달에서 상품 정보 읽기**
```javascript
// openCheckoutModal() 함수 (23-169줄)
function openCheckoutModal(btn) {
    // 버튼의 data-* 속성 읽기
    currentProduct.id = parseInt(btn.getAttribute('data-id'), 10);
    currentProduct.name = btn.getAttribute('data-name') || '';
    currentProduct.price = parseFloat(btn.getAttribute('data-price')) || 0;
    currentProduct.type = btn.getAttribute('data-type') || '';
    currentProduct.token = parseInt(btn.getAttribute('data-token'), 10) || 0;
    currentProduct.duration = parseInt(btn.getAttribute('data-duration'), 10) || 0;
    
    // 모달 표시
    modal.classList.add('show');
}
```

**3단계: 결제 확인 → 주문 생성**
```javascript
// confirmPurchase() 함수 (453-504줄)
async function confirmPurchase() {
    // 수량 계산
    let quantity = ...;
    
    // 주문 생성 API 호출
    await createOrder(currentProduct.id, quantity);
}
```

**4단계: API 호출**
```javascript
// createOrder() 함수 (519-610줄)
async function createOrder(productId, quantity = 1) {
    const response = await fetch('/api/orders/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            product_id: productId,        // ← 상품 ID
            quantity: quantity,          // ← 수량
            payment_method: paymentMethod,  // 'card' 또는 'trans'
            tax_evidence_requested: taxEvidenceRequested  // true/false
        })
    });
    
    // 결제 완료 처리
    await completePayment(merchantUid);
}
```

---

## 📋 상품별 상세 정보

### [Standard]
- **변수명:** `regular_products` 리스트에서 `product.name|lower|replace(' ', '') == 'standard'`
- **구매함수:** `openCheckoutModal(btn)` → `confirmPurchase()` → `createOrder(productId, quantity)`
- **버튼 속성:**
  - `data-id`: 상품 ID
  - `data-name`: "Standard"
  - `data-price`: 가격 (예: 500원)
  - `data-type`: "basic"
  - `data-token`: 토큰 수량
  - `data-duration`: 0

### [Premium]
- **변수명:** `regular_products` 리스트에서 `product.name|lower|replace(' ', '') == 'premium'`
- **구매함수:** `openCheckoutModal(btn)` → `confirmPurchase()` → `createOrder(productId, quantity)`
- **추가 변수:** `discount_rate` (할인율 %), `premium_per_token_price` (토큰당 가격)
- **버튼 속성:**
  - `data-id`: 상품 ID
  - `data-name`: "Premium"
  - `data-price`: 가격 (예: 25,000원)
  - `data-type`: "package"
  - `data-token`: 토큰 수량 (예: 100개)
  - `data-duration`: 0

### [Gold]
- **변수명:** `regular_products` 리스트에서 `product.name|lower|replace(' ', '') == 'gold'`
- **구매함수:** `openCheckoutModal(btn)` → `confirmPurchase()` → `createOrder(productId, quantity)`
- **버튼 속성:**
  - `data-id`: 상품 ID
  - `data-name`: "Gold"
  - `data-price`: 가격 (예: 70,000원)
  - `data-type`: "subscription"
  - `data-token`: -1 (무제한)
  - `data-duration`: 0

### [Event 1/2]
- **변수명:** `event_products` 리스트 (2개)
- **구매함수:** `openCheckoutModal(btn)` → `confirmPurchase()` → `createOrder(productId, quantity)`
- **버튼 속성:**
  - `data-id`: 상품 ID
  - `data-name`: 이벤트 상품명
  - `data-price`: 0 (무료)
  - `data-type`: "event" 또는 "event_period"
  - `data-token`: 토큰 수량 (이벤트 토큰인 경우)
  - `data-duration`: 기간 일수 (이벤트 기간인 경우)

---

## 🎯 결론: 쇼룸 HTML에 넘겨줘야 할 변수

### 필수 Context 변수 (Flask에서 전달)

```python
# routes/payment_routes.py의 _build_shop_context() 반환값
{
    'event_products': event_products,        # 이벤트 상품 리스트 (2개)
    'regular_products': regular_products,    # 일반 상품 리스트 (Standard, Premium, Gold)
    'discount_rate': discount_rate,          # Premium 할인율 (%)
    'premium_per_token_price': premium_per_token_price,  # Premium 토큰당 가격
    'user_info': user_info                   # 사용자 정보
}
```

### 상품별 데이터 구조

**각 상품 객체 (`product`)의 필드:**
```python
{
    'id': int,                    # 상품 ID (DB PK)
    'name': str,                  # 상품명 ('Standard', 'Premium', 'Gold', 이벤트명)
    'description': str,           # 상품 설명
    'price': int,                 # 가격 (원)
    'token_amount': int,          # 토큰 수량 (-1이면 무제한)
    'duration_days': int,        # 기간 (일)
    'type': str,                  # 타입 ('basic', 'package', 'subscription', 'event', 'event_period')
    'vat_included': bool,         # 부가세 포함 여부
    'is_active': int              # 활성화 여부 (0 또는 1)
}
```

### JavaScript에서 사용하는 함수

**1. 모달 열기:**
```javascript
window.openCheckoutModal(buttonElement);
// 또는
openCheckoutModal(buttonElement);
```

**2. 주문 생성 (내부 호출):**
```javascript
await createOrder(productId, quantity);
```

**3. 결제 완료 (내부 호출):**
```javascript
await completePayment(merchantUid);
```

---

## 🔧 3D 쇼룸에 이식할 때 필요한 작업

### 1. HTML 템플릿 (`showroom.html`)

**현재 상태:**
- ✅ `shop.html`과 동일한 Context 변수 사용 (`_build_shop_context()`)
- ✅ `static/js/payment/shop.js` 로드됨
- ❌ 3D 상품 클릭 시 구매 버튼 연결 필요

**필요한 작업:**
1. 3D 상품 클릭 시 `openCheckoutModal()` 호출
2. 3D 상품에 `data-*` 속성 추가 (또는 JavaScript 객체로 관리)
3. 구매 버튼 이벤트 리스너 연결

### 2. JavaScript 연동

**3D 쇼룸에서 구매 트리거 예시:**
```javascript
// Showroom.js 또는 별도 파일
function handleProductClick(product3DObject) {
    // 3D 객체에서 상품 정보 추출
    const productData = product3DObject.userData.product;
    
    // 가상 버튼 생성 (shop.js의 openCheckoutModal이 기대하는 형식)
    const virtualButton = document.createElement('button');
    virtualButton.setAttribute('data-id', productData.id);
    virtualButton.setAttribute('data-name', productData.name);
    virtualButton.setAttribute('data-price', productData.price);
    virtualButton.setAttribute('data-type', productData.type);
    virtualButton.setAttribute('data-token', productData.token_amount);
    virtualButton.setAttribute('data-duration', productData.duration_days);
    
    // 기존 shop.js 함수 호출
    if (window.openCheckoutModal) {
        window.openCheckoutModal(virtualButton);
    }
}
```

### 3. 상품 데이터 매핑

**3D 쇼룸의 상품 객체에 데이터 연결:**
```javascript
// Showroom.js에서 상품 생성 시
const product3D = factory.createStandardCoin(...);
product3D.userData.product = {
    id: standardProduct.id,
    name: standardProduct.name,
    price: standardProduct.price,
    type: standardProduct.type,
    token_amount: standardProduct.token_amount,
    duration_days: standardProduct.duration_days
};

// 클릭 이벤트 연결
product3D.addEventListener('click', () => {
    handleProductClick(product3D);
});
```

---

## 📝 체크리스트

### 쇼룸 HTML에 필요한 것
- [x] `event_products` 변수 전달
- [x] `regular_products` 변수 전달
- [x] `discount_rate` 변수 전달
- [x] `premium_per_token_price` 변수 전달
- [x] `shop.js` 스크립트 로드
- [ ] 3D 상품 클릭 이벤트 핸들러
- [ ] 3D 상품 → 구매 모달 연결

### JavaScript 연동
- [x] `openCheckoutModal()` 함수 사용 가능
- [x] `createOrder()` API 엔드포인트 (`/api/orders/create`)
- [x] `completePayment()` API 엔드포인트 (`/api/payment/complete`)
- [ ] 3D 상품 클릭 → `openCheckoutModal()` 호출 로직
- [ ] 3D 상품 데이터 → `data-*` 속성 변환 로직

---

**분석 완료. 이제 3D 쇼룸에 판매 로직을 100% 이식할 준비가 되었습니다!** 🚀


