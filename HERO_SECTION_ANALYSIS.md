# Hero Section 구조 분석 보고서

**분석일**: 2024-12-XX  
**목적**: Glassmorphism 및 애니메이션 업그레이드 전 현재 구조 파악

---

## 📋 1. HTML 구조 (Raw HTML)

### Hero Section 전체 구조
```html
<!-- 히어로 섹션 -->
<section class="hero-section" id="home">
    <div class="hero-content">
        <div class="hero-content-wrapper">
            <!-- 좌측: 텍스트 그룹 -->
            <div class="hero-copy hero-text-group reveal reveal-delay-1">
                <h1 class="hero-title">
                    복잡한 세무 정산 데이터,<br>
                    홈택스 업로드용<br>
                    <strong>표준 포맷으로 완벽 변환.</strong>
                </h1>
                <p class="hero-subtitle">
                    업로드 실패 없는 <strong>무결점 엑셀</strong> 생성.<br>
                    로하택스가 사장님의 원본 파일을 국세청 표준 양식으로 <strong>0.5초 만에</strong> 바꿔드립니다.
                </p>
                <div class="hero-actions">
                    <button class="btn-primary" onclick="window.location.href='/shop'">
                        무료로 시작하기
                    </button>
                </div>
            </div>

            <!-- 우측: 비주얼 영역 (브라우저 창 프레임 안에 대시보드 스크린샷) -->
            <div class="hero-image-wrapper reveal reveal-delay-2">
                <!-- UI 전용 이미지 (노트북 베젤 없음) -->
                <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2426&auto=format&fit=crop" 
                     alt="로하택스 대시보드 UI" 
                     class="hero-dashboard-img"
                     style="width: 100%; height: auto; display: block; object-fit: cover;">
            </div>
        </div>
    </div>
</section>
```

---

## 🎨 2. CSS 클래스 구조

### 2.1 주요 컨테이너 클래스

| 요소 | 클래스 | 역할 |
|------|--------|------|
| **최상위 섹션** | `.hero-section` | Hero Section 전체 컨테이너 |
| **콘텐츠 래퍼** | `.hero-content` | 최대 너비 1200px, 중앙 정렬 |
| **레이아웃 래퍼** | `.hero-content-wrapper` | Flexbox 레이아웃 (좌우 배치) |

### 2.2 텍스트 영역 클래스

| 요소 | 클래스 | 역할 |
|------|--------|------|
| **텍스트 그룹** | `.hero-copy.hero-text-group` | 좌측 텍스트 영역 (580px 고정 너비) |
| **제목** | `.hero-title` | 메인 헤드라인 (3.6rem, 800 weight) |
| **부제목** | `.hero-subtitle` | 설명 텍스트 (1.35rem, 500 weight) |
| **액션 버튼 영역** | `.hero-actions` | CTA 버튼 컨테이너 (Flexbox) |
| **버튼** | `.btn-primary` | 주요 액션 버튼 |

### 2.3 이미지 영역 클래스

| 요소 | 클래스 | 역할 |
|------|--------|------|
| **이미지 래퍼** | `.hero-image-wrapper` | 우측 이미지 영역 (650px 고정 너비) |
| **대시보드 이미지** | `.hero-dashboard-img` | 실제 이미지 요소 |

### 2.4 애니메이션 클래스

| 클래스 | 역할 | 위치 |
|--------|------|------|
| `.reveal` | 기본 reveal 애니메이션 | `animations.css` |
| `.reveal-delay-1` | 0.1초 딜레이 | 텍스트 그룹에 적용 |
| `.reveal-delay-2` | 0.2초 딜레이 | 이미지 래퍼에 적용 |

---

## 📁 3. 연결된 CSS 파일

### 3.1 Hero Section 전용 CSS
- **`static/css/sections/hero.css`** (372줄)
  - Hero Section 전용 스타일
  - 레이아웃, 타이포그래피, 반응형 디자인

### 3.2 공통 CSS 파일 (영향 가능성)

#### Core Styles
- `static/css/core/reset.css`
- `static/css/core/variables.css`
- `static/css/core/fonts.css`

#### Layout Styles
- `static/css/layout/container.css`
- `static/css/layout/header.css`

#### Component Styles
- `static/css/components/buttons.css` - **`.btn-primary` 스타일 정의**
- `static/css/components/cards.css`
- `static/css/components/animations.css` - **`.reveal` 애니메이션 정의**

---

## 🔧 4. JavaScript 파일 분석

### 4.1 연결된 JavaScript 파일

#### 1. `static/js/homepage.js` (807줄)
**Hero Section과 관련된 기능:**

```javascript
// Scroll Reveal Animation (IntersectionObserver)
const revealElements = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
            observer.unobserve(entry.target);
        }
    });
}, {
    root: null,
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
});

revealElements.forEach(el => revealObserver.observe(el));
```

**영향 분석:**
- ✅ **애니메이션 충돌 가능성 낮음**: IntersectionObserver 기반으로 작동
- ⚠️ **주의**: `.reveal.active` 클래스 추가 시 애니메이션 트리거됨
- ✅ **호환성**: 새로운 애니메이션과 병행 가능

#### 2. `static/js/components/video_player.js`
- Hero Section과 직접 관련 없음 (다른 섹션용)

#### 3. 외부 라이브러리
- `lucide@latest` (아이콘 라이브러리) - Hero Section에서 사용 안 함

---

## 🎯 5. 현재 스타일 특성

### 5.1 배경 및 레이아웃
```css
.hero-section {
    background: #FFFFFF;  /* 흰색 배경 */
    padding: 120px 0 140px;
    position: relative;
    overflow: hidden;
}
```

### 5.2 레이아웃 구조
```css
.hero-content-wrapper {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 80px;
    max-width: 1440px;
    min-height: 700px;
}
```

### 5.3 타이포그래피
```css
.hero-title {
    font-size: 3.6rem;
    font-weight: 800;
    color: #0f172a;
}

.hero-title strong {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
```

### 5.4 이미지 영역
```css
.hero-image-wrapper {
    flex: 0 0 650px;
    border-radius: 12px;
    box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(0,0,0,0.08);
    background: #fff;
    overflow: hidden;
}

.hero-image-wrapper::before {
    /* 브라우저 창 상단 바 (빨강/노랑/초록 점) */
    content: '';
    display: block;
    height: 32px;
    background: #f1f5f9;
    /* ... */
}
```

---

## ⚠️ 6. 잠재적 충돌 요소

### 6.1 애니메이션 충돌 가능성

#### 현재 Reveal 시스템
- **동작 방식**: IntersectionObserver로 `.active` 클래스 추가
- **트리거 조건**: 요소가 10% 보일 때
- **애니메이션**: `opacity: 0 → 1`, `translateY(40px) → translateY(0)`

#### Glassmorphism 적용 시 고려사항
- ✅ **호환 가능**: 기존 reveal 애니메이션과 병행 가능
- ⚠️ **주의**: 새로운 애니메이션 추가 시 transition 충돌 가능성
- ✅ **권장**: 기존 `.reveal` 클래스 유지하고 추가 효과만 적용

### 6.2 CSS 우선순위

#### 현재 스타일 계층
1. `core/reset.css` - 기본 리셋
2. `core/variables.css` - CSS 변수
3. `sections/hero.css` - Hero 전용 스타일
4. `components/animations.css` - 애니메이션 유틸리티

#### 충돌 가능성
- ⚠️ **`.btn-primary`**: `components/buttons.css`에서 정의됨
- ✅ **`.reveal`**: `components/animations.css`에서 정의됨
- ✅ **권장**: `!important` 사용 최소화, 특이성(specificity) 활용

---

## 📊 7. 반응형 브레이크포인트

### 현재 반응형 설정

```css
/* 데스크톱 (기본) */
.hero-content-wrapper {
    flex-direction: row;  /* 좌우 배치 */
    gap: 80px;
}

/* 태블릿 (1280px 이하) */
@media (max-width: 1280px) {
    .hero-content-wrapper {
        flex-direction: column;  /* 세로 배치 */
        text-align: center;
    }
}

/* 모바일 (768px 이하) */
@media (max-width: 768px) {
    .hero-section {
        padding: 4rem 0 2rem 0;
    }
    .hero-title {
        font-size: 36px;
    }
}
```

---

## 🔍 8. 현재 애니메이션 상태

### 8.1 활성 애니메이션

| 애니메이션 | 클래스 | 위치 | 상태 |
|-----------|--------|------|------|
| **Reveal (스크롤)** | `.reveal` | `animations.css` | ✅ 활성 |
| **Reveal Delay 1** | `.reveal-delay-1` | `animations.css` | ✅ 활성 (텍스트) |
| **Reveal Delay 2** | `.reveal-delay-2` | `animations.css` | ✅ 활성 (이미지) |
| **Blob Pulse** | `.hero-visual::before` | `hero.css` | ⚠️ 정의되어 있으나 사용 안 함 |

### 8.2 사용되지 않는 애니메이션

- `.hero-visual::before` - `blob-pulse` 애니메이션 정의되어 있으나 HTML에 `.hero-visual` 요소 없음
- `.hero-visual-card` - 정의되어 있으나 HTML에 사용 안 함

---

## 📝 9. 요약

### Hero Section 구조 요약

#### HTML 계층
```
<section class="hero-section">
  └─ <div class="hero-content">
      └─ <div class="hero-content-wrapper"> (Flexbox: 좌우 배치)
          ├─ <div class="hero-copy hero-text-group reveal reveal-delay-1"> (좌측)
          │   ├─ <h1 class="hero-title">
          │   ├─ <p class="hero-subtitle">
          │   └─ <div class="hero-actions">
          │       └─ <button class="btn-primary">
          └─ <div class="hero-image-wrapper reveal reveal-delay-2"> (우측)
              └─ <img class="hero-dashboard-img">
```

#### 주요 CSS 클래스
- **컨테이너**: `.hero-section`, `.hero-content`, `.hero-content-wrapper`
- **텍스트**: `.hero-copy`, `.hero-text-group`, `.hero-title`, `.hero-subtitle`, `.hero-actions`
- **이미지**: `.hero-image-wrapper`, `.hero-dashboard-img`
- **애니메이션**: `.reveal`, `.reveal-delay-1`, `.reveal-delay-2`
- **버튼**: `.btn-primary`

#### JavaScript 영향
- ✅ **IntersectionObserver 기반 reveal 애니메이션**: 새로운 애니메이션과 호환 가능
- ✅ **충돌 가능성 낮음**: 기존 시스템이 `.active` 클래스 추가만 수행

---

## ✅ 10. Glassmorphism 적용 준비 상태

### 현재 상태
- ✅ **구조 명확**: HTML 구조가 명확하게 정의됨
- ✅ **CSS 분리**: Hero 전용 CSS 파일 존재 (`hero.css`)
- ✅ **애니메이션 시스템**: 기존 reveal 시스템과 호환 가능
- ✅ **반응형 준비**: 브레이크포인트 정의 완료

### 적용 시 고려사항
1. **기존 `.reveal` 클래스 유지**: IntersectionObserver와 호환
2. **CSS 특이성**: `hero.css`에서 Glassmorphism 스타일 추가
3. **애니메이션 순서**: reveal → glassmorphism 효과 순서 고려
4. **성능**: `backdrop-filter` 사용 시 성능 최적화 필요

---

**보고서 작성 완료**: Cursor AI  
**다음 단계**: Glassmorphism 및 애니메이션 업그레이드 구현






