# 상점 데이터 구조 정밀 분석 보고서

## 📊 1. Discount Logic Trace (할인 데이터 추적)

### 1.1 DB 스키마 현황

**`products` 테이블 구조:**
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL DEFAULT 0,        -- ⚠️ 할인 전/후 가격 구분 없음
    token_amount INTEGER NOT NULL DEFAULT 0,
    type TEXT NOT NULL DEFAULT 'basic',
    vat_included INTEGER NOT NULL DEFAULT 0,
    duration_days INTEGER,
    token_validity_days INTEGER,
    one_time_limit INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);
```

**핵심 발견:**
- ❌ `discount_rate` 컬럼 **없음**
- ❌ `original_price` 컬럼 **없음**
- ✅ `price` 컬럼만 존재 (할인 적용된 최종 가격)

### 1.2 할인율 계산 로직 위치

**관리자 페이지 (`templates/admin/tabs/product_management.html`):**
- 102-108줄: Premium 상품의 할인율은 **"자동 계산"** 표시
- JavaScript 함수: `calculatePremiumDiscount()` (admin/product.js 235-251줄)

**할인율 계산 공식:**
```javascript
// 기준 단가(Standard) × Premium 토큰 수량 = 기준 총액
const standardTotalPrice = standardPrice * premiumTokenAmount;

// 할인율 = (기준 총액 - Premium 실제 가격) / 기준 총액 × 100
const discount = ((standardTotalPrice - premiumPrice) / standardTotalPrice * 100).toFixed(1);
```

**문제점:**
- 할인율은 **관리자 페이지에서만 계산**됨
- 계산된 할인율이 **DB에 저장되지 않음**
- 상점 페이지(`shop.html`)에는 **하드코딩된 "50% 할인"**만 표시됨 (139줄)

### 1.3 상점 페이지 할인 표시 현황

**`templates/payment/shop.html` 139줄:**
```html
<span class="premium-discount-badge">50% 할인</span>
```

**현재 상태:**
- ❌ 하드코딩된 텍스트 ("50% 할인")
- ❌ 실제 DB 데이터와 연동되지 않음
- ❌ 관리자가 설정한 할인율이 반영되지 않음

---

## 💰 2. Price Sync Check (가격 연동 확인)

### 2.1 데이터 흐름

**백엔드 (`routes/payment_routes.py` 33-77줄):**
```python
@payment_bp.route('/shop', methods=['GET'])
def shop():
    # DB에서 상품 조회
    products = conn.execute(
        "SELECT id, name, description, price, token_amount, ... FROM products"
    ).fetchall()
    
    # 템플릿에 전달
    return render_template('payment/shop.html', 
                         products=products_list,
                         event_products=event_products,
                         regular_products=regular_products)
```

**프론트엔드 (`templates/payment/shop.html`):**
```jinja2
{{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
```

**결론:**
- ✅ 가격은 **단순 DB 조회(`SELECT`)**로 표시됨
- ✅ 관리자가 `price` 컬럼을 수정하면 **자동으로 반영**됨
- ✅ JavaScript 동적 계산 없음 (서버 사이드 렌더링)

### 2.2 가격 변수명 안전 구역

**현재 사용 중인 변수:**
- `{{ product.price }}` - 가격 (원 단위)
- `{{ product.name }}` - 상품명
- `{{ product.description }}` - 상품 설명
- `{{ product.token_amount }}` - 토큰 수량
- `{{ product.type }}` - 상품 유형
- `{{ product.duration_days }}` - 기간 (일)

**디자인 변경 시 주의사항:**
- ✅ 위 변수명은 **절대 변경 금지**
- ✅ HTML 구조만 변경 가능 (CSS/디자인)
- ✅ 변수명을 그대로 유지하면 기능 파괴 없음

---

## 🏗️ 3. HTML Structure Analysis (리모델링 견적)

### 3.1 현재 카드 구조

**`.product-card` 내부 구조 (`shop.html` 105-127줄):**
```html
<div class="product-card standard">
    <span class="product-icon">🚀</span>
    <div class="product-tagline">급할 때 한 건씩!</div>
    <h3 class="product-name">{{ product.name }}</h3>
    <p class="product-description">필요할 때만 사용하는 유연한 플랜</p>
    <div class="product-price">
        {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
    </div>
    <ul class="product-feature-list">...</ul>
    <button class="btn-purchase" data-id="..." data-price="...">구매하기</button>
</div>
```

**Premium 카드 (할인 배지 포함):**
```html
<div class="product-card premium">
    ...
    <div class="product-price">
        {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
        <span class="premium-discount-badge">50% 할인</span>  <!-- ⚠️ 하드코딩 -->
    </div>
    ...
</div>
```

### 3.2 디자인 업그레이드 제안

**할인율 배지 개선 방안:**

1. **리본 스타일 배지 (Ribbon Badge):**
   ```html
   <div class="product-price">
       {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
       <div class="discount-ribbon">
           <span class="ribbon-text">{{ discount_rate }}%</span>
       </div>
   </div>
   ```

2. **네온 배지 (Neon Badge):**
   ```html
   <div class="product-price">
       {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
       <div class="neon-discount-badge">
           <span class="neon-text">{{ discount_rate }}% OFF</span>
       </div>
   </div>
   ```

3. **Glassmorphism 배지:**
   ```html
   <div class="product-price">
       {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
       <div class="glass-discount-badge">
           <span>{{ discount_rate }}% 할인</span>
       </div>
   </div>
   ```

### 3.3 추가 래퍼 필요성

**현재 구조로 충분:**
- ✅ `.product-price` 내부에 배지를 추가하면 됨
- ✅ 별도 `div` 래퍼 불필요
- ✅ CSS만으로 고급스러운 효과 구현 가능

**제안 구조:**
```html
<div class="product-price">
    <div class="price-main">
        {{ "{:,}".format(product.price or 0) }}<span class="product-price-unit">원</span>
    </div>
    {% if product.id == 2 %}  <!-- Premium만 할인율 표시 -->
    <div class="discount-ribbon" data-discount="{{ calculated_discount }}">
        <span>{{ calculated_discount }}%</span>
    </div>
    {% endif %}
</div>
```

---

## 🎯 4. 핵심 문제점 및 해결 방안

### 4.1 문제점 요약

1. **할인율이 DB에 저장되지 않음**
   - 관리자 페이지에서만 계산
   - 상점 페이지에는 하드코딩된 "50% 할인"만 표시

2. **할인율 계산 로직이 프론트엔드에 없음**
   - 상점 페이지 JavaScript에 할인율 계산 함수 없음
   - Standard 가격 정보가 상점 페이지에 전달되지 않음

3. **데이터 연동 불일치**
   - 관리자가 설정한 할인율이 상점에 반영되지 않음

### 4.2 해결 방안

**옵션 1: 백엔드에서 할인율 계산 후 전달 (권장)**
```python
# routes/payment_routes.py 수정
def shop():
    # Standard 상품 가격 조회
    standard = conn.execute("SELECT price FROM products WHERE id = 1").fetchone()
    standard_price = standard['price'] if standard else 500
    
    # 각 상품에 할인율 계산
    for product in products_list:
        if product['id'] == 2:  # Premium
            premium_total = standard_price * product['token_amount']
            if premium_total > 0:
                discount = ((premium_total - product['price']) / premium_total * 100)
                product['discount_rate'] = round(discount, 1)
            else:
                product['discount_rate'] = 0
    
    return render_template('payment/shop.html', 
                         products=products_list,
                         standard_price=standard_price,  # 추가
                         ...)
```

**옵션 2: 프론트엔드에서 계산 (비권장)**
- Standard 가격을 별도로 전달해야 함
- JavaScript 계산 로직 추가 필요
- 서버 사이드 계산이 더 안전함

---

## 📋 5. 디자인 변경 안전 구역

### 5.1 변경 가능 영역

✅ **CSS 스타일링:**
- `.product-card` 배경, 테두리, 그림자
- `.product-price` 레이아웃, 색상, 폰트
- `.premium-discount-badge` → `.discount-ribbon` 등 클래스명 변경 가능
- 3D 효과, 홀로그램 효과, 네온 효과 등 시각적 효과

✅ **HTML 구조 (디자인용 래퍼 추가):**
- `<div class="price-wrapper">` 같은 래퍼 추가 가능
- 배지 위치 변경 가능 (가격 위/아래/옆)

### 5.2 절대 변경 금지 영역

❌ **Jinja2 변수명:**
- `{{ product.price }}` - 절대 변경 금지
- `{{ product.name }}` - 절대 변경 금지
- `{{ product.id }}` - 절대 변경 금지

❌ **data 속성:**
- `data-id="{{ product.id }}"` - 구매 버튼 기능에 필수
- `data-price="{{ product.price }}"` - 결제 로직에 필수

❌ **JavaScript 기능:**
- `shop.js`의 구매 버튼 이벤트 리스너
- 모달 열기/닫기 로직

---

## 🎨 6. 리모델링 제안

### 6.1 할인율 배지 디자인 제안

**1. 리본 스타일 (Ribbon):**
```css
.discount-ribbon {
    position: absolute;
    top: -10px;
    right: -10px;
    background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
    color: white;
    padding: 8px 16px;
    clip-path: polygon(0 0, 100% 0, 100% 85%, 85% 100%, 0 100%);
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
    animation: ribbon-pulse 2s infinite;
}
```

**2. 네온 배지 (Neon):**
```css
.neon-discount-badge {
    background: rgba(6, 182, 212, 0.1);
    border: 2px solid #06b6d4;
    color: #06b6d4;
    padding: 6px 12px;
    border-radius: 20px;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.5),
                0 0 40px rgba(6, 182, 212, 0.3);
    animation: neon-glow 2s infinite;
}
```

**3. Glassmorphism 배지:**
```css
.glass-discount-badge {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 8px 16px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
```

### 6.2 구현 우선순위

1. **1단계: 할인율 계산 로직 추가 (백엔드)**
   - `payment_routes.py`에서 Standard 가격 조회
   - Premium 상품 할인율 계산
   - 템플릿에 `discount_rate` 전달

2. **2단계: HTML 구조 수정**
   - 하드코딩된 "50% 할인" 제거
   - `{{ discount_rate }}% 할인` 동적 표시

3. **3단계: CSS 디자인 적용**
   - 리본/네온/Glassmorphism 배지 스타일 적용
   - 3D 효과와 조화롭게 디자인

---

## ✅ 최종 결론

### 현재 상태
- ❌ 할인율이 DB에 저장되지 않음
- ❌ 상점 페이지에 하드코딩된 "50% 할인"만 표시
- ✅ 가격은 DB 조회로 정상 연동됨

### 해결 필요 사항
1. 백엔드에서 할인율 계산 후 템플릿에 전달
2. HTML에서 하드코딩 제거, 동적 할인율 표시
3. CSS로 고급스러운 배지 디자인 적용

### 안전 구역
- ✅ CSS 스타일링 자유롭게 변경 가능
- ✅ HTML 구조 (디자인용 래퍼) 추가 가능
- ❌ Jinja2 변수명 절대 변경 금지
- ❌ JavaScript 기능 로직 절대 변경 금지

---

**보고서 작성일:** 2024-12-19
**분석 대상:** `homepage1/routes/payment_routes.py`, `homepage1/templates/payment/shop.html`, `homepage1/templates/admin/tabs/product_management.html`



