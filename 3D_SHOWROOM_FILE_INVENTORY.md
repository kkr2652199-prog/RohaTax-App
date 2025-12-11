# 3D 쇼룸 관련 파일 및 디렉토리 인벤토리

**생성일**: 2024-12-XX  
**프로젝트**: RohaTax - homepage1 워크트리  
**목적**: 3D 쇼룸 시스템의 모든 파일 및 구조 파악

---

## 📁 디렉토리 구조

### 핵심 디렉토리
```
homepage1/
├── static/
│   ├── js/3d/              # 3D 렌더링 핵심 모듈
│   ├── css/pages/          # 쇼룸 페이지 스타일
│   ├── assets/video/       # 비디오 에셋
│   └── images/             # 이미지 에셋
├── templates/
│   └── payment/            # 쇼룸 HTML 템플릿
└── static/docs/            # 문서
```

---

## 🎨 JavaScript 파일 (3D 렌더링)

### 1. **`static/js/3d/Showroom.js`** (1,220줄)
- **역할**: 3D 쇼룸 메인 엔진 및 씬 관리
- **기능**:
  - Three.js 씬 초기화 및 렌더링 루프
  - 카메라 제어 (OrbitControls)
  - 조명 시스템 (AmbientLight, PointLight, SpotLight, DirectionalLight)
  - 스마트 TV 및 비디오 텍스처 관리
  - 시네마 모드 (Cinema Mode) 토글
  - 애니메이션 루프 및 이벤트 처리
  - 사용자 인터랙션 (마우스, 키보드)
- **의존성**: `ShowroomBuilder.js`, `ProductFactory.js`, `GiftBox3D.js`
- **관련 기능**: 렌더링, 애니메이션, 인터랙션

### 2. **`static/js/3d/ShowroomBuilder.js`** (855줄)
- **역할**: 3D 쇼룸 환경 구축 (방, 천장, 벽, 바닥)
- **기능**:
  - 방 구조 생성 (`buildRoom()`)
  - 대리석 바닥 텍스처 생성 (`createMarbleTexture()`)
  - 모던 천장 생성 (`createModernCeiling()`)
  - 스마트 TV 생성 (`createSmartTV()`)
  - 벽 및 기타 구조물 생성
  - 조명 설치
- **관련 기능**: 모델 로딩, 렌더링, 환경 구성

### 3. **`static/js/3d/ProductFactory.js`** (462줄)
- **역할**: 상품 3D 모델 생성 연동 모듈
- **기능**:
  - 이벤트 상품 생성 (`createEventProduct()` - GiftBox3D 사용)
  - 일반 상품 생성 (`createRegularProduct()`)
  - 표준 코인 생성 (`createStandardCoin()`)
  - 프리미엄 큐브 생성 (`createPremiumCube()`)
  - 골드 크라운 생성 (`createGoldCrown()`)
  - 폴백 상품 생성 (`createFallbackProduct()`)
- **의존성**: `GiftBox3D.js`
- **관련 기능**: 모델 로딩, 상품 렌더링

### 4. **`static/js/3d/GiftBox3D.js`** (987줄)
- **역할**: 재사용 가능한 3D 선물 상자 컴포넌트
- **기능**:
  - 선물 상자 3D 모델 생성 (`createModel()`)
  - 리본 및 장식 추가
  - 텍스트 오버레이 (Canvas 2D)
  - 애니메이션 (상자 열기, 컨페티 효과)
  - 인터랙션 (클릭 이벤트)
- **관련 기능**: 모델 로딩, 애니메이션, 인터랙션

### 5. **`static/js/3d/gift_box_3d.js`** (517줄)
- **역할**: 선물 상자 3D 모델 (레거시 또는 대체 버전)
- **기능**: GiftBox3D.js의 이전 버전 또는 대체 구현
- **관련 기능**: 모델 로딩

### 6. **`static/js/3d/event_products_3d_scene.js`**
- **역할**: 이벤트 상품 3D 씬 관리
- **기능**: 이벤트 상품 전용 3D 씬 구성
- **관련 기능**: 렌더링, 모델 로딩

---

## 🎨 CSS 파일 (스타일링)

### 1. **`static/css/pages/shop_showroom.css`**
- **역할**: 쇼룸 페이지 전용 스타일
- **기능**:
  - 캔버스 컨테이너 레이아웃
  - 풀스크린 모드 스타일
  - UI 오버레이 스타일
- **관련 기능**: 레이아웃, UI 스타일링

### 2. **`static/css/pages/shop_card_3d.css`**
- **역할**: 3D 카드 스타일
- **기능**: 3D 카드 효과 및 애니메이션
- **관련 기능**: UI 스타일링, 애니메이션

### 3. **`static/css/pages/shop.css`**
- **역할**: 상점 페이지 공통 스타일
- **기능**: 상점 페이지 레이아웃 및 공통 스타일
- **관련 기능**: 레이아웃, UI 스타일링

---

## 📄 HTML 템플릿 파일

### 1. **`templates/payment/showroom.html`**
- **역할**: 3D 쇼룸 메인 페이지 템플릿
- **기능**:
  - Three.js 라이브러리 로딩
  - 3D 컴포넌트 스크립트 로딩 (순서 중요)
  - 데이터 주입 (window.PRODUCT_DATA, window.USER_INFO)
  - 3D 엔진 초기화
  - 캐시 버스팅 (version parameter)
- **관련 기능**: 렌더링, 데이터 바인딩

### 2. **`templates/payment/shop.html`**
- **역할**: 상점 페이지 템플릿
- **기능**: 상점 페이지 레이아웃 및 3D 쇼룸 연결
- **관련 기능**: 레이아웃, 데이터 바인딩

### 3. **`templates/components/3d_keypad.html`**
- **역할**: 3D 키패드 컴포넌트
- **기능**: 3D 키패드 UI 컴포넌트
- **관련 기능**: UI 컴포넌트, 인터랙션

---

## 🎬 비디오 에셋

### 1. **`static/assets/video/roha_conversion_demo.mp4`**
- **역할**: TV 스크린에 표시되는 데모 비디오
- **기능**: 쇼룸 내 스마트 TV에서 재생되는 변환 데모 영상
- **관련 기능**: 비디오 텍스처, 인터랙션

### 2. **`static/videos/roha_conversion_demo.mp4.mp4`**
- **역할**: 비디오 에셋 (중복 또는 백업)
- **관련 기능**: 비디오 텍스처

---

## 📸 이미지 에셋

### 1. **`static/images/hometax_guide/`** (8개 파일)
- **파일들**:
  - `step1.png.jpg` ~ `step8.png.jpg`
- **역할**: 홈택스 가이드 이미지
- **기능**: 쇼룸 내 가이드 표시용 이미지
- **관련 기능**: UI 표시, 이미지 로딩

---

## 📚 문서 파일

### 1. **`static/docs/room_blueprint.md`**
- **역할**: 쇼룸 구조 설계 문서
- **기능**: 쇼룸 구조 및 설계 가이드
- **관련 기능**: 문서화

### 2. **`SHOP_SHOWROOM_ANALYSIS.md`**
- **역할**: 쇼룸 분석 문서
- **기능**: 쇼룸 시스템 분석 및 개선 사항
- **관련 기능**: 문서화

### 3. **`SHOP_3D_TILT_ANALYSIS.md`**
- **역할**: 3D 틸트 효과 분석 문서
- **기능**: 3D 카드 틸트 효과 분석
- **관련 기능**: 문서화

### 4. **`SHOP_3D_UPGRADE_ANALYSIS.md`**
- **역할**: 3D 업그레이드 분석 문서
- **기능**: 3D 시스템 업그레이드 분석
- **관련 기능**: 문서화

---

## 🧪 테스트 파일

### 1. **`static/test_kwon3d_enhanced.html`**
- **역할**: 3D 쇼룸 테스트 페이지
- **기능**: 3D 쇼룸 기능 테스트
- **관련 기능**: 테스트, 디버깅

### 2. **`test_vanilla_3d.html`**
- **역할**: 바닐라 3D 테스트 페이지
- **기능**: 순수 Three.js 테스트
- **관련 기능**: 테스트, 디버깅

### 3. **`test_gift_box_3d_preview.html`**
- **역할**: 선물 상자 3D 프리뷰 테스트
- **기능**: GiftBox3D 컴포넌트 테스트
- **관련 기능**: 테스트, 디버깅

---

## 🔧 설정 파일

### 1. **`config/settings.py`**
- **역할**: 애플리케이션 설정
- **기능**: 쇼룸 관련 설정 포함 가능
- **관련 기능**: 설정 관리

### 2. **`config/industry_config.json`**
- **역할**: 업종별 설정
- **기능**: 업종별 3D 모델 설정 포함 가능
- **관련 기능**: 설정 관리

---

## 📊 데이터 파일

### 1. **`templates_data/template_config.json`**
- **역할**: 템플릿 설정
- **기능**: 3D 템플릿 설정 포함 가능
- **관련 기능**: 데이터 관리

---

## 🔗 외부 의존성

### CDN 라이브러리 (showroom.html에서 로딩)
1. **Three.js** (`https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js`)
   - 3D 렌더링 엔진
2. **OrbitControls** (`https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`)
   - 카메라 제어
3. **Vanilla Tilt** (`https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.1/vanilla-tilt.min.js`)
   - 3D 카드 틸트 효과

---

## 📋 파일별 기능 분류

### 렌더링 관련
- `Showroom.js` - 메인 렌더링 엔진
- `ShowroomBuilder.js` - 환경 렌더링
- `ProductFactory.js` - 상품 렌더링
- `GiftBox3D.js` - 선물 상자 렌더링

### 모델 로딩 관련
- `GiftBox3D.js` - 선물 상자 모델 생성
- `ProductFactory.js` - 상품 모델 생성
- `ShowroomBuilder.js` - 환경 모델 생성

### 애니메이션 관련
- `Showroom.js` - 메인 애니메이션 루프
- `GiftBox3D.js` - 선물 상자 애니메이션
- `event_products_3d_scene.js` - 이벤트 상품 애니메이션

### 인터랙션 관련
- `Showroom.js` - 마우스/키보드 이벤트
- `GiftBox3D.js` - 클릭 이벤트
- `shop.js` - 결제 모달 인터랙션

### 스타일링 관련
- `shop_showroom.css` - 쇼룸 페이지 스타일
- `shop_card_3d.css` - 3D 카드 스타일
- `shop.css` - 상점 페이지 스타일

---

## 🎯 핵심 파일 우선순위

### 필수 파일 (Core)
1. **`Showroom.js`** - 메인 엔진 (없으면 쇼룸 작동 불가)
2. **`ShowroomBuilder.js`** - 환경 구축 (없으면 방이 생성되지 않음)
3. **`ProductFactory.js`** - 상품 생성 (없으면 상품이 표시되지 않음)
4. **`showroom.html`** - 메인 템플릿 (없으면 페이지가 없음)

### 중요 파일 (Important)
5. **`GiftBox3D.js`** - 선물 상자 모델 (이벤트 상품에 필요)
6. **`shop_showroom.css`** - 스타일링 (레이아웃에 필요)
7. **`roha_conversion_demo.mp4`** - 비디오 에셋 (TV 스크린에 필요)

### 보조 파일 (Supporting)
8. **`gift_box_3d.js`** - 레거시 버전 (대체 가능)
9. **`event_products_3d_scene.js`** - 이벤트 전용 (선택적)
10. 테스트 파일들 - 개발/디버깅용

---

## 📝 참고 사항

- **파일 크기**: `Showroom.js` (1,220줄), `ShowroomBuilder.js` (855줄), `GiftBox3D.js` (987줄) 모두 500줄 가이드라인 초과
- **모듈화 필요**: 향후 리팩토링 시 연동 모듈로 분리 고려
- **의존성 순서**: `showroom.html`에서 스크립트 로딩 순서가 중요 (GiftBox3D → ShowroomBuilder → ProductFactory → Showroom)
- **캐시 버스팅**: 모든 스크립트에 `?v={{ timestamp }}` 파라미터 사용

---

**마지막 업데이트**: 2024-12-XX  
**작성자**: AI Assistant

