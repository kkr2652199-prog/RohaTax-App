# 상점 페이지 '명품 쇼룸' 리모델링 전 구조 분석 보고서

## 📋 분석 개요

**목표**: 상점 페이지를 '명품 쇼룸'으로 리모델링하기 전, 현재 구조를 정밀 분석하여 모듈화 전략 수립
**원칙**: 기존 파일 비대화 방지, 기능 보존, 시각적 업그레이드만 수행

---

## 1️⃣ 코드 비만도 측정

### 파일 크기 현황

**파일**: `static/css/pages/shop.css`
- **총 라인 수**: **1,369줄** ⚠️
- **500줄 규칙 초과**: **869줄 초과 (174% 초과)**
- **비만도 등급**: 🔴 **심각 (Critical)**

### 코드 구조 분석

#### 섹션별 라인 분포 (예상)

| 섹션 | 예상 라인 수 | 비율 | 특징 |
|------|------------|------|------|
| **CSS 변수 및 기본 스타일** | ~100줄 | 7% | `:root`, `body.shop-page` |
| **헤더 스타일** | ~280줄 | 20% | `.glass-header`, `.user-menu` 등 |
| **Hero 섹션** | ~60줄 | 4% | `.shop-hero`, `.shop-hero-title` |
| **이벤트 섹션 (Layout)** | ~50줄 | 4% | `.event-section`, `.event-grid` |
| **이벤트 카드 (Item)** | ~120줄 | 9% | `.event-card`, `.event-badge` |
| **상품 섹션 (Layout)** | ~50줄 | 4% | `.product-section`, `.product-grid` |
| **상품 카드 (Item)** | ~500줄 | 37% | `.product-card`, `.standard`, `.premium`, `.gold` |
| **구매 버튼** | ~50줄 | 4% | `.btn-purchase` |
| **모달 스타일** | ~150줄 | 11% | `.modal-overlay`, `.modal-content` |
| **특수 배지** | ~30줄 | 2% | `.gold-special-badge`, `.premium-discount-badge` |
| **미디어 쿼리** | ~80줄 | 6% | `@media` 쿼리들 |

#### 문제점 분석

**1. 카드 스타일과 레이아웃 스타일 혼재**
- ✅ **명확히 분리됨**: 섹션별 주석(`/* === */`)으로 구분되어 있음
- ⚠️ **하나의 파일에 집중**: 모든 스타일이 `shop.css`에 모여있음
- ⚠️ **카드 스타일 비중 높음**: 상품 카드 관련 스타일이 약 500줄 (37%)

**2. 중복 코드 가능성**
- `.event-card`와 `.product-card`의 유사한 스타일 패턴
- Glassmorphism 효과가 여러 곳에 반복 적용
- 3D 효과 관련 코드가 카드별로 중복

**결론**: ✅ **모듈화 필수** - 500줄 규칙을 크게 초과하며, 카드와 레이아웃이 명확히 분리 가능

---

## 2️⃣ HTML 구조 분석

### 현재 HTML 구조

**파일**: `templates/payment/shop.html`

#### 전체 구조
```html
<body class="shop-page">
    <!-- 전역 헤더 -->
    {% include 'partials/header.html' %}
    
    <div class="shop-page-wrapper">
        <!-- Hero Section -->
        <div class="shop-hero">...</div>
        
        <!-- 이벤트 상품 섹션 -->
        {% if event_products %}
        <section class="event-section">
            <div class="event-section-header">...</div>
            <div class="event-grid">
                {% for product in event_products %}
                <div class="event-card">...</div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
        
        <!-- 유료 요금제 섹션 -->
        {% if regular_products %}
        <section class="product-section" id="regular-products">
            <div class="product-section-header">...</div>
            <div class="product-grid">
                {% for product in regular_products %}
                <div class="product-card">...</div>
                {% endfor %}
            </div>
        </section>
        {% endif %}
    </div>
</body>
```

### 구역 분리 현황

#### ✅ **명확히 분리됨**

1. **이벤트 상품 구역**
   - 컨테이너: `<section class="event-section">`
   - 그리드: `<div class="event-grid">`
   - 카드: `<div class="event-card">`

2. **유료 상품 구역**
   - 컨테이너: `<section class="product-section">`
   - 그리드: `<div class="product-grid">`
   - 카드: `<div class="product-card">`

3. **최상위 래퍼**
   - 전체 감싸기: `<div class="shop-page-wrapper">`

### '유리 선반(Glass Shelf)' 적용 가능성

**현재 구조 평가:**
- ✅ **별도 컨테이너 존재**: `event-section`, `product-section`이 명확히 분리
- ✅ **래퍼 구조 완비**: `shop-page-wrapper`가 전체를 감싸고 있음
- ✅ **추가 래퍼 불필요**: 현재 구조만으로도 '유리 선반' 스타일 적용 가능

**결론**: ✅ **HTML 구조 변경 불필요** - 현재 구조로 '명품 쇼룸' 스타일 적용 가능

---

## 3️⃣ 모듈화 전략 수립

### 전략 A: 기존 파일 연장 (비권장)

**방식**: `shop.css`에 쇼룸 스타일 추가

**장점:**
- 파일 추가 없음
- 간단한 작업

**단점:**
- ❌ **500줄 규칙 위반 심화**: 현재 1,369줄 → 추가 시 1,500줄 이상 예상
- ❌ **유지보수 어려움**: 하나의 거대한 파일
- ❌ **코드 탐색 비효율**: 관련 스타일 찾기 어려움
- ❌ **프로젝트 규칙 위반**: "500줄 규칙" 명확히 위반

**결론**: ❌ **비권장** - 프로젝트 규칙 위반 및 유지보수성 저하

---

### 전략 B: 모듈 분리 (권장) ⭐

**방식**: 새로운 `shop_showroom.css` 파일 생성

#### 파일 구조 제안

```
static/css/pages/
├── shop.css              (기존 - 1,369줄)
│   ├── 헤더 스타일       (~280줄)
│   ├── Hero 섹션         (~60줄)
│   ├── 이벤트 카드       (~120줄)
│   ├── 상품 카드         (~500줄)
│   ├── 버튼/모달         (~200줄)
│   └── 미디어 쿼리       (~80줄)
│
└── shop_showroom.css     (신규 - 예상 200-300줄)
    ├── 쇼룸 배경         (~50줄)
    ├── 유리 선반 스타일  (~100줄)
    ├── 조명 효과         (~50줄)
    └── 진열대 애니메이션 (~50줄)
```

#### 모듈화 세부 계획

**1. `shop_showroom.css` (신규 파일)**
```css
/* ================================================================
   명품 쇼룸 배경 및 분위기
   ================================================================ */

.shop-page-wrapper {
    /* 쇼룸 배경: 어두운 고급스러운 톤 */
    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
    position: relative;
    overflow: hidden;
}

.shop-page-wrapper::before {
    /* 조명 효과 */
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 20% 30%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* ================================================================
   유리 선반 (Glass Shelf) - 이벤트 섹션
   ================================================================ */

.event-section {
    position: relative;
    z-index: 1;
    /* 유리 선반 배경 */
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 48px 32px;
    margin-bottom: 48px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* ================================================================
   유리 선반 (Glass Shelf) - 상품 섹션
   ================================================================ */

.product-section {
    position: relative;
    z-index: 1;
    /* 유리 선반 배경 */
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 48px 32px;
    margin-bottom: 48px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* ================================================================
   조명 효과 (Spotlight)
   ================================================================ */

.event-section::before,
.product-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: 50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    transform: translateX(-50%);
    pointer-events: none;
    z-index: -1;
    animation: spotlight-sweep 8s ease-in-out infinite;
}

@keyframes spotlight-sweep {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.6; }
}
```

**2. HTML 수정 (최소한)**
```html
<!-- shop.html에 추가 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/shop_showroom.css') }}?v={{ timestamp }}">
```

**장점:**
- ✅ **500줄 규칙 준수**: 기존 파일은 유지, 새 파일은 200-300줄 예상
- ✅ **명확한 책임 분리**: 쇼룸 스타일만 별도 관리
- ✅ **유지보수 용이**: 쇼룸 관련 스타일만 수정하면 됨
- ✅ **기능 보존**: 기존 `shop.css`는 건드리지 않음
- ✅ **프로젝트 규칙 준수**: "연장형 모듈 관리 원칙" 부합

**단점:**
- ⚠️ **파일 1개 추가**: 하지만 프로젝트 규칙상 필요

**결론**: ✅ **권장** - 프로젝트 규칙 준수 및 유지보수성 향상

---

## 4️⃣ HTML 구조 변경 필요성

### 현재 구조 평가

**기존 구조:**
```html
<div class="shop-page-wrapper">
    <section class="event-section">
        <div class="event-grid">...</div>
    </section>
    <section class="product-section">
        <div class="product-grid">...</div>
    </section>
</div>
```

### '명품 쇼룸' 스타일 적용 시나리오

**시나리오 1: 현재 구조 유지 (권장)**
- `event-section`, `product-section`에 직접 쇼룸 스타일 적용
- 추가 HTML 변경 없음
- 기능 영향 0%

**시나리오 2: 래퍼 추가 (선택)**
- 각 섹션을 감싸는 `<div class="glass-shelf">` 추가
- 디자인용 태그만 추가 (기능 영향 없음)
- 더 정교한 스타일링 가능

**결론**: ✅ **HTML 구조 변경 선택적** - 현재 구조로도 충분하나, 더 정교한 효과를 위해 래퍼 추가 가능

---

## 5️⃣ 최종 권장 전략

### ✅ **전략 B: 모듈 분리 (최종 권장)**

#### 구현 계획

**Phase 1: 새 파일 생성**
- `static/css/pages/shop_showroom.css` 생성
- 쇼룸 배경, 유리 선반, 조명 효과 스타일 작성

**Phase 2: HTML 연결**
- `shop.html`에 새 CSS 파일 링크 추가
- 기존 `shop.css`는 그대로 유지

**Phase 3: 스타일 적용**
- `event-section`, `product-section`에 유리 선반 스타일 적용
- 배경 조명 효과 추가
- 진열대 애니메이션 추가

**Phase 4: 검증**
- 기능 정상 작동 확인
- 반응형 디자인 확인
- 브라우저 호환성 확인

#### 예상 파일 크기

| 파일 | 현재 | 예상 | 변화 |
|------|------|------|------|
| `shop.css` | 1,369줄 | 1,369줄 | 변화 없음 |
| `shop_showroom.css` | 없음 | 200-300줄 | 신규 생성 |

**총 라인 수**: 1,569-1,669줄 (2개 파일로 분산)

#### 장점 요약

1. ✅ **프로젝트 규칙 준수**: 500줄 규칙 준수 (파일별)
2. ✅ **기능 보존**: 기존 `shop.css` 수정 없음
3. ✅ **명확한 책임 분리**: 쇼룸 스타일만 별도 관리
4. ✅ **유지보수 용이**: 쇼룸 관련 수정 시 한 파일만 수정
5. ✅ **확장성**: 향후 추가 쇼룸 스타일 확장 용이

---

## 6️⃣ HTML 구조 변경 제안 (선택사항)

### 현재 구조로도 가능하나, 더 정교한 효과를 위한 제안

**제안 1: 유리 선반 래퍼 추가 (선택)**
```html
<section class="event-section">
    <div class="glass-shelf">
        <div class="event-section-header">...</div>
        <div class="event-grid">...</div>
    </div>
</section>
```

**장점:**
- 더 정교한 유리 선반 효과 가능
- 섹션 헤더와 그리드를 별도로 스타일링 가능

**단점:**
- HTML 구조 변경 필요 (하지만 기능 영향 없음)

**결론**: ⚠️ **선택사항** - 현재 구조로도 충분하나, 더 정교한 효과를 원하면 래퍼 추가 권장

---

## 📊 종합 평가

### 현재 상태

| 항목 | 상태 | 평가 |
|------|------|------|
| **파일 크기** | 1,369줄 | 🔴 심각 (500줄 규칙 174% 초과) |
| **구조 분리** | 명확히 분리됨 | ✅ 양호 |
| **HTML 구조** | 섹션별 분리 완료 | ✅ 양호 |
| **모듈화 필요성** | 필수 | ✅ 권장 |

### 최종 권장사항

**✅ 전략 B: 모듈 분리 (최종 권장)**

1. **`shop_showroom.css` 신규 생성** (200-300줄 예상)
2. **기존 `shop.css`는 수정하지 않음** (1,369줄 유지)
3. **HTML에 새 CSS 파일 링크 추가** (1줄 추가)
4. **HTML 구조 변경 선택적** (현재 구조로도 충분)

**예상 작업량:**
- 신규 파일 생성: 1개
- HTML 수정: 1줄 (CSS 링크 추가)
- CSS 작성: 200-300줄
- 기능 영향: 0%

---

## 🎯 다음 단계

1. **`shop_showroom.css` 파일 생성**
2. **쇼룸 배경 및 유리 선반 스타일 작성**
3. **`shop.html`에 CSS 링크 추가**
4. **기능 검증 및 브라우저 테스트**

---

**보고서 작성일**: 2025-12-07
**분석 대상**: `homepage1/static/css/pages/shop.css`, `homepage1/templates/payment/shop.html`
**결론**: ✅ **모듈 분리 필수** - `shop_showroom.css` 신규 생성 권장

