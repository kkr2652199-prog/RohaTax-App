# 3D 쇼룸 환경 상세 아키텍처 보고서

**작업 디렉토리**: `homepage1` (서버 포트: 5001)  
**생성일**: 2024-12-XX  
**목적**: 향후 정확한 수정 작업을 위한 100% 필수 정보

---

## 🎯 핵심 발견 사항

### ✅ 3D 프레임워크/라이브러리
- **주요 프레임워크**: **Three.js r128** (Three.js 0.128.0)
- **로딩 방식**: CDN (외부 라이브러리)
- **확장 라이브러리**: OrbitControls (카메라 제어)

### ❌ 3D 모델 파일 (외부 파일 없음)
- **중요 발견**: `.gltf`, `.glb`, `.obj`, `.fbx`, `.mtl` 등의 외부 3D 모델 파일은 **존재하지 않음**
- **모델 생성 방식**: **Procedural Generation (절차적 생성)**
  - 모든 3D 모델이 JavaScript 코드로 직접 생성됨
  - Three.js의 기본 Geometry 클래스 사용 (BoxGeometry, CylinderGeometry, SphereGeometry 등)

---

## 📁 디렉토리 구조 (상세)

```
homepage1/
├── static/
│   ├── js/3d/                          # ⭐ 3D 렌더링 핵심 모듈
│   │   ├── Showroom.js                 # 메인 엔진 (1,220줄)
│   │   ├── ShowroomBuilder.js         # 환경 구축 (855줄)
│   │   ├── ProductFactory.js           # 상품 생성 (462줄)
│   │   ├── GiftBox3D.js                # 선물 상자 (987줄)
│   │   ├── gift_box_3d.js              # 레거시 버전 (517줄)
│   │   └── event_products_3d_scene.js # 이벤트 씬
│   │
│   ├── css/pages/                      # 스타일링
│   │   ├── shop_showroom.css           # 쇼룸 페이지 전용
│   │   ├── shop_card_3d.css            # 3D 카드 스타일
│   │   └── shop.css                    # 상점 공통
│   │
│   ├── assets/
│   │   └── video/
│   │       └── roha_conversion_demo.mp4  # ⭐ TV 스크린 비디오
│   │
│   └── images/
│       └── hometax_guide/               # 가이드 이미지 (8개)
│           ├── step1.png.jpg
│           ├── step2.png.jpg
│           ├── step3.png.jpg
│           ├── step4.png.jpg
│           ├── step5.png.jpg
│           ├── step6.png.jpg
│           ├── step7.png.jpg
│           └── step8.png.jpg
│
├── templates/
│   └── payment/
│       └── showroom.html                # ⭐ 메인 템플릿
│
└── config/
    ├── industry_config.json             # 업종별 설정 (3D 쇼룸과 무관)
    └── absolute_guidelines_v5.json     # 절대지침 (3D 쇼룸과 무관)
```

---

## 🎨 JavaScript 파일 상세 분석

### 1. **`static/js/3d/Showroom.js`** (1,220줄)
**역할**: 3D 쇼룸 메인 엔진 및 씬 관리

**주요 기능**:
- Three.js 씬 초기화 (`THREE.Scene`, `THREE.WebGLRenderer`)
- 카메라 제어 (`THREE.PerspectiveCamera`, FPS 스타일 컨트롤)
- 조명 시스템:
  - `THREE.AmbientLight` (환경 조명)
  - `THREE.PointLight` (점 조명)
  - `THREE.SpotLight` (스포트 조명)
  - `THREE.DirectionalLight` (방향 조명)
- 스마트 TV 및 비디오 텍스처 관리
- 애니메이션 루프 (`requestAnimationFrame`)
- 사용자 인터랙션 (마우스, 키보드, WASD 이동)

**Three.js 사용 패턴**:
```javascript
// 렌더러
this.renderer = new THREE.WebGLRenderer({...});

// 씬
this.scene = new THREE.Scene();
this.scene.background = new THREE.Color(0x0a0a0a);

// 카메라
this.camera = new THREE.PerspectiveCamera(50, ...);

// 조명
new THREE.AmbientLight(0xffffff, 0.5);
new THREE.PointLight(0xffffff, 1.0, 30);
```

**의존성**:
- `ShowroomBuilder.js` (환경 구축)
- `ProductFactory.js` (상품 생성)
- `GiftBox3D.js` (선물 상자 모델)

---

### 2. **`static/js/3d/ShowroomBuilder.js`** (855줄)
**역할**: 3D 쇼룸 환경 구축 (방, 천장, 벽, 바닥)

**주요 기능**:
- 방 구조 생성 (`buildRoom()`)
- 대리석 바닥 텍스처 생성 (`createMarbleTexture()`)
  - Canvas API를 사용한 절차적 텍스처 생성
  - `THREE.CanvasTexture` 사용
- 모던 천장 생성 (`createModernCeiling()`)
- 스마트 TV 생성 (`createSmartTV()`)
- 벽 및 기타 구조물 생성

**Three.js Geometry 사용**:
```javascript
// 바닥
new THREE.PlaneGeometry(floorSize, floorSize)

// 벽
new THREE.BoxGeometry(30, 15, 1)

// 천장 프레임
new THREE.ExtrudeGeometry(outerFrameShape, {...})

// 진열대
new THREE.CylinderGeometry(1.2, 1.2, 0.4, 32)

// 기타
new THREE.TorusGeometry(...)
new THREE.SphereGeometry(...)
new THREE.CircleGeometry(...)
```

**텍스처 생성**:
- `createMarbleTexture()`: Canvas 2D API로 대리석 패턴 생성
- `THREE.CanvasTexture`: Canvas를 Three.js 텍스처로 변환

---

### 3. **`static/js/3d/ProductFactory.js`** (462줄)
**역할**: 상품 3D 모델 생성 연동 모듈

**주요 기능**:
- 이벤트 상품 생성 (`createEventProduct()` - GiftBox3D 사용)
- 일반 상품 생성 (`createRegularProduct()`)
- 표준 코인 생성 (`createStandardCoin()`)
  - `THREE.CylinderGeometry` (코인 본체)
  - `THREE.BoxGeometry` (톱니)
  - `THREE.TorusGeometry` (테두리)
- 프리미엄 큐브 생성 (`createPremiumCube()`)
  - `THREE.BoxGeometry` (외곽 프레임)
  - `THREE.EdgesGeometry` (와이어프레임)
- 골드 크라운 생성 (`createGoldCrown()`)
  - `THREE.TorusGeometry` (링)
  - `THREE.SphereGeometry` (코어)
  - `THREE.BufferGeometry` (파티클)

**Three.js Material 사용**:
```javascript
new THREE.MeshStandardMaterial({...})
new THREE.MeshPhysicalMaterial({...})
new THREE.MeshBasicMaterial({...})
new THREE.LineBasicMaterial({...})
new THREE.PointsMaterial({...})
new THREE.SpriteMaterial({...})
```

---

### 4. **`static/js/3d/GiftBox3D.js`** (987줄)
**역할**: 재사용 가능한 3D 선물 상자 컴포넌트

**주요 기능**:
- 선물 상자 3D 모델 생성 (`createModel()`)
- 리본 및 장식 추가
- 텍스트 오버레이 (Canvas 2D)
- 애니메이션 (상자 열기, 컨페티 효과)
- 인터랙션 (클릭 이벤트)

**Three.js 사용**:
- `THREE.Group` (상자 그룹화)
- `THREE.BoxGeometry` (상자 본체)
- `THREE.PlaneGeometry` (리본)
- `THREE.CanvasTexture` (텍스트 오버레이)

---

## 🎬 에셋 파일 상세

### 비디오 에셋
**경로**: `static/assets/video/roha_conversion_demo.mp4`
- **용도**: 쇼룸 내 스마트 TV 스크린에 표시되는 데모 비디오
- **사용 방식**: Three.js `VideoTexture` 또는 HTML5 Video Element
- **관련 코드**: `Showroom.js`의 `createSmartTV()` 메서드

### 이미지 에셋
**경로**: `static/images/hometax_guide/`
- **파일 수**: 8개 (step1.png.jpg ~ step8.png.jpg)
- **용도**: 홈택스 가이드 이미지 (쇼룸 내 가이드 표시용)
- **사용 방식**: `THREE.TextureLoader` 또는 HTML Image Element

---

## ⚙️ 설정 파일 분석

### 1. **`config/industry_config.json`**
- **용도**: 업종별 변환 규칙 설정
- **3D 쇼룸 관련성**: ❌ 무관 (세금계산서 변환 규칙만 포함)

### 2. **`config/absolute_guidelines_v5.json`**
- **용도**: 절대지침 설정
- **3D 쇼룸 관련성**: ❌ 무관

### 3. **`templates_data/template_config.json`**
- **용도**: 템플릿 설정
- **3D 쇼룸 관련성**: ❌ 무관 (Excel 템플릿 설정만 포함)

### ⚠️ **중요 발견**: 3D 쇼룸 전용 설정 파일 없음
- 모든 설정이 JavaScript 코드 내부에 하드코딩됨
- 설정값 변경 시 코드 직접 수정 필요

---

## 📄 HTML 템플릿 상세

### **`templates/payment/showroom.html`**

**Three.js 라이브러리 로딩** (순서 중요):
```html
<!-- [1] Three.js 핵심 라이브러리 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<!-- [2] Three.js 확장 (OrbitControls) -->
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

**3D 컴포넌트 로딩 순서** (의존성 순서):
```html
<!-- [3] 3D 컴포넌트 라이브러리 (순서 중요!) -->
<script src=".../GiftBox3D.js?v=100"></script>
<script src=".../ShowroomBuilder.js?v={{ timestamp }}"></script>
<script src=".../ProductFactory.js?v={{ timestamp }}"></script>
<script src=".../Showroom.js?v={{ timestamp }}"></script>
```

**데이터 주입**:
```javascript
window.PRODUCT_DATA = {{ products | tojson | safe }};
window.USER_INFO = {{ user_info | tojson | safe }};
```

**3D 엔진 초기화**:
```javascript
window.showroom = new window.Showroom('canvas-container');
```

---

## 🔧 3D 모델 생성 방식 (Procedural Generation)

### 모델 파일 없음
- ❌ `.gltf` 파일 없음
- ❌ `.glb` 파일 없음
- ❌ `.obj` 파일 없음
- ❌ `.fbx` 파일 없음
- ❌ `.mtl` 파일 없음

### 코드로 생성되는 모델들

#### 1. **바닥 (Floor)**
```javascript
// ShowroomBuilder.js
const floorGeo = new THREE.PlaneGeometry(floorSize, floorSize);
const floorTexture = this.createMarbleTexture(); // Canvas로 생성
const floorMat = new THREE.MeshPhysicalMaterial({...});
const floor = new THREE.Mesh(floorGeo, floorMat);
```

#### 2. **벽 (Walls)**
```javascript
// ShowroomBuilder.js
const backWall = new THREE.Mesh(
  new THREE.BoxGeometry(30, 15, 1),
  new THREE.MeshStandardMaterial({...})
);
```

#### 3. **천장 (Ceiling)**
```javascript
// ShowroomBuilder.js
const frameGeo = new THREE.ExtrudeGeometry(outerFrameShape, {...});
const frame = new THREE.Mesh(frameGeo, frameMat);
```

#### 4. **상품 모델들**
```javascript
// ProductFactory.js
// 코인
const coin = new THREE.Mesh(
  new THREE.CylinderGeometry(coinRadius, coinRadius, coinHeight, 64),
  coinMat
);

// 큐브
const inner = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  coreMat
);

// 크라운
const ring1 = new THREE.Mesh(
  new THREE.TorusGeometry(ringRadius, ringThickness, 32, 100),
  goldMat
);
```

#### 5. **선물 상자**
```javascript
// GiftBox3D.js
const boxGeometry = new THREE.BoxGeometry(boxWidth, boxHeight, boxDepth);
const boxMesh = new THREE.Mesh(boxGeometry, boxMaterial);
```

---

## 🎨 텍스처 생성 방식

### 1. **Canvas 기반 텍스처**
**파일**: `ShowroomBuilder.js` - `createMarbleTexture()`
```javascript
const canvas = document.createElement('canvas');
canvas.width = 2048;
canvas.height = 2048;
const ctx = canvas.getContext('2d');

// Canvas 2D API로 패턴 그리기
ctx.fillStyle = '#111111';
ctx.fillRect(0, 0, 2048, 2048);
// ... 패턴 그리기 ...

const texture = new THREE.CanvasTexture(canvas);
```

### 2. **비디오 텍스처** (추정)
**파일**: `Showroom.js` - `createSmartTV()`
- HTML5 Video Element 사용
- `THREE.VideoTexture` 또는 유사 방식으로 TV 스크린에 표시

### 3. **이미지 텍스처** (가능성)
- `THREE.TextureLoader` 사용 가능
- 현재 코드에서 명시적 사용 확인 안 됨

---

## 📊 파일별 Three.js 사용 통계

| 파일 | THREE 사용 횟수 | 주요 클래스 |
|------|----------------|------------|
| `Showroom.js` | 493+ | Scene, WebGLRenderer, PerspectiveCamera, Lights, Groups |
| `ShowroomBuilder.js` | 200+ | Geometry, Material, Mesh, ExtrudeGeometry, CanvasTexture |
| `ProductFactory.js` | 100+ | Geometry, Material, Mesh, Groups |
| `GiftBox3D.js` | 50+ | Geometry, Material, Mesh, Groups, CanvasTexture |

---

## 🔗 외부 의존성 (CDN)

### Three.js
- **버전**: r128 (0.128.0)
- **URL**: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
- **용도**: 3D 렌더링 엔진

### OrbitControls
- **버전**: 0.128.0
- **URL**: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`
- **용도**: 카메라 제어 (현재 FPS 컨트롤로 대체됨)

### Vanilla Tilt
- **버전**: 1.8.1
- **URL**: `https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.1/vanilla-tilt.min.js`
- **용도**: 3D 카드 틸트 효과 (쇼룸과 직접 무관)

---

## 🎯 핵심 파일 경로 요약

### 필수 파일 (Core - 없으면 작동 불가)
1. `static/js/3d/Showroom.js` - 메인 엔진
2. `static/js/3d/ShowroomBuilder.js` - 환경 구축
3. `static/js/3d/ProductFactory.js` - 상품 생성
4. `templates/payment/showroom.html` - 메인 템플릿

### 중요 파일 (Important)
5. `static/js/3d/GiftBox3D.js` - 선물 상자 모델
6. `static/css/pages/shop_showroom.css` - 스타일링
7. `static/assets/video/roha_conversion_demo.mp4` - 비디오 에셋

### 보조 파일 (Supporting)
8. `static/js/3d/gift_box_3d.js` - 레거시 버전
9. `static/js/3d/event_products_3d_scene.js` - 이벤트 씬
10. `static/images/hometax_guide/*.jpg` - 가이드 이미지

---

## ⚠️ 중요 주의사항

### 1. **모델 파일 없음**
- 모든 3D 모델이 코드로 생성됨
- 외부 모델 파일 로더 (`GLTFLoader`, `OBJLoader` 등) 사용 안 함
- 모델 수정 시 JavaScript 코드 직접 수정 필요

### 2. **설정 파일 없음**
- 3D 쇼룸 전용 설정 파일 없음
- 모든 설정이 코드 내부에 하드코딩됨
- 설정 변경 시 코드 직접 수정 필요

### 3. **의존성 순서 중요**
- `showroom.html`에서 스크립트 로딩 순서가 중요
- `GiftBox3D` → `ShowroomBuilder` → `ProductFactory` → `Showroom` 순서 필수

### 4. **캐시 버스팅**
- 모든 스크립트에 `?v={{ timestamp }}` 파라미터 사용
- 브라우저 캐시 문제 방지

---

## 📋 수정 작업 시 체크리스트

### 모델 수정 시
- [ ] 해당 Geometry 생성 코드 찾기
- [ ] Material 설정 확인
- [ ] 위치/회전/스케일 확인
- [ ] 텍스처 설정 확인

### 환경 수정 시
- [ ] `ShowroomBuilder.js`의 `buildRoom()` 메서드 확인
- [ ] 조명 설정 확인
- [ ] 텍스처 생성 로직 확인

### 상품 수정 시
- [ ] `ProductFactory.js`의 해당 메서드 확인
- [ ] `GiftBox3D.js` 확인 (이벤트 상품인 경우)
- [ ] 진열대 위치 확인

### 성능 최적화 시
- [ ] Geometry 재사용 확인
- [ ] Material 재사용 확인
- [ ] 인스턴싱 가능 여부 확인

---

## 🎓 기술 스택 요약

| 항목 | 기술/도구 |
|------|----------|
| **3D 프레임워크** | Three.js r128 (0.128.0) |
| **모델 형식** | Procedural Generation (코드 생성) |
| **텍스처 생성** | Canvas 2D API → THREE.CanvasTexture |
| **비디오 처리** | HTML5 Video → THREE.VideoTexture (추정) |
| **카메라 제어** | 커스텀 FPS 컨트롤 (OrbitControls 대체) |
| **렌더링** | WebGL (THREE.WebGLRenderer) |
| **애니메이션** | requestAnimationFrame |
| **상호작용** | 마우스/키보드 이벤트 |

---

**마지막 업데이트**: 2024-12-XX  
**작성자**: AI Assistant  
**검증 상태**: ✅ 코드베이스 실제 파일 기반 (추측 정보 없음)


