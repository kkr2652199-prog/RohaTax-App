# 3D 쇼룸 리팩토링 및 작업장 구축 계획서

## 🎯 최고 중요 원칙 확인

**✅ 유료 상품의 시스템 기능은 절대 수정하지 않고, 오직 UI/UX 시각적 요소만 작업합니다.**

---

## 📊 [단계 1] 리팩토링 및 모듈화 계획

### 1. 가구 클래스 분리 계획

#### 현재 상태 분석
- **ProductFactory.js** 내부에 3가지 유료 상품 생성 메서드 존재:
  - `createStandardCoin()` (라인 102-175)
  - `createPremiumCube()` (라인 181-251)
  - `createGoldCrown()` (라인 257-362)
- **GiftBox3D.js**는 이미 독립 클래스로 분리되어 있음 ✅

#### 분리 대상 클래스 목록

| 파일명 | 클래스명 | 역할 | 현재 위치 |
|--------|----------|------|-----------|
| `StandardCoin3D.js` | `StandardCoin3D` | 은색 코인 + 톱니바퀴 디테일 생성 | `ProductFactory.js` 라인 102-175 |
| `PremiumCube3D.js` | `PremiumCube3D` | 테크 큐브 (네온 시안 와이어프레임) 생성 | `ProductFactory.js` 라인 181-251 |
| `GoldCrown3D.js` | `GoldCrown3D` | 자이로스코프 (3개 교차 링 + 에너지 코어) 생성 | `ProductFactory.js` 라인 257-362 |

#### 각 클래스의 공통 인터페이스 설계

```javascript
/**
 * 공통 인터페이스: 모든 가구 클래스는 다음 메서드를 구현해야 함
 */
class BaseFurniture3D {
  constructor(scene, position, options = {}) {
    this.scene = scene;
    this.position = position || { x: 0, y: 0, z: 0 };
    this.options = options;
    this.group = null;
  }
  
  /**
   * 3D 모델 생성 (필수 구현)
   * @returns {THREE.Group} 생성된 3D 그룹 객체
   */
  create() {
    throw new Error("create() 메서드를 구현해야 합니다.");
  }
  
  /**
   * 메모리 해제 (선택 구현)
   */
  dispose() {
    if (this.group) {
      this.group.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
      this.scene.remove(this.group);
      this.group = null;
    }
  }
}
```

#### 각 클래스의 구체적 역할

**1. StandardCoin3D.js**
- **역할**: 은색 코인 3D 모델 생성
- **Geometry**: `CylinderGeometry(1.2, 1.2, 0.25, 64)` + `BoxGeometry` (톱니바퀴) + `TorusGeometry` (림)
- **Material**: `MeshStandardMaterial` (은색, metalness: 1.0)
- **애니메이션**: 없음 (정적 모델)
- **의존성**: `THREE.js`만 필요

**2. PremiumCube3D.js**
- **역할**: 테크 큐브 3D 모델 생성
- **Geometry**: `BoxGeometry(1.6, 1.6, 1.6)` + `EdgesGeometry` (와이어프레임)
- **Material**: `LineBasicMaterial` (네온 시안) + `MeshPhysicalMaterial` (내부 큐브)
- **애니메이션**: 회전 애니메이션 (외부/내부 반대 방향)
- **의존성**: `THREE.js`만 필요
- **주의사항**: `updateAnimation()` 메서드 필요 (회전 로직)

**3. GoldCrown3D.js**
- **역할**: 자이로스코프 3D 모델 생성
- **Geometry**: `TorusGeometry(0.7, 0.12, 32, 100)` × 3개 + `SphereGeometry(0.25, 32, 32)` + `BufferGeometry` (파티클)
- **Material**: `MeshPhysicalMaterial` (골드, metalness: 1.0) + `PointsMaterial` (파티클)
- **애니메이션**: 회전 애니메이션 (3개 링 + 코어)
- **의존성**: `THREE.js`만 필요
- **주의사항**: `updateAnimation()` 메서드 필요 (회전 로직)

---

### 2. ProductFactory.js 역할 재정의

#### 리팩토링 후 ProductFactory.js의 역할

**순수한 '공장' 메서드 목록:**

```javascript
class ProductFactory {
  constructor(scene) {
    this.scene = scene;
    // 애니메이션 추적용 배열 (분리된 클래스 인스턴스 참조)
    this.animatedProducts = [];
  }
  
  /**
   * 이벤트 상품 생성 (GiftBox3D 사용)
   */
  createEventProduct(product, position) {
    // GiftBox3D 클래스 인스턴스화 및 생성
  }
  
  /**
   * 일반 상품 생성 (라우터 역할)
   */
  createRegularProduct(product, position) {
    // product.name에 따라 적절한 클래스 선택
    // - "standard" → StandardCoin3D
    // - "premium" → PremiumCube3D
    // - "gold" → GoldCrown3D
    // - 기타 → FallbackProduct3D
  }
  
  /**
   * 기본 상품 생성 (Fallback)
   */
  createFallbackProduct(product, position) {
    // 기본 BoxGeometry 생성
  }
  
  /**
   * 가격 라벨 생성 (UI 요소)
   */
  createPriceLabel(product) {
    // Canvas Texture 기반 가격 라벨 생성
  }
  
  /**
   * 상품 애니메이션 업데이트 (위임 패턴)
   */
  updateProductAnimations() {
    // 분리된 클래스의 updateAnimation() 메서드 호출
    this.animatedProducts.forEach(product => {
      if (product.updateAnimation) {
        product.updateAnimation();
      }
    });
  }
  
  /**
   * 모든 상품 메시 배열 반환
   */
  getAllMeshes() {
    // 분리된 클래스의 group 반환
  }
}
```

#### 변경 사항 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| **코인 생성** | `createStandardCoin()` 메서드 | `new StandardCoin3D().create()` 호출 |
| **큐브 생성** | `createPremiumCube()` 메서드 | `new PremiumCube3D().create()` 호출 |
| **크라운 생성** | `createGoldCrown()` 메서드 | `new GoldCrown3D().create()` 호출 |
| **애니메이션** | 내부 배열 직접 조작 | 분리된 클래스의 `updateAnimation()` 위임 |
| **코드 라인 수** | ~460줄 | ~150줄 (예상) |

---

### 3. UI/UX 비침해 보증 분석

#### 애니메이션 및 인터랙션 코드 심문 결과

**✅ ProductFactory.js 분석:**

| 코드 라인 | 기능 | 시스템 연관성 | 수정 가능 여부 |
|-----------|------|---------------|----------------|
| **라인 420-444** | `updateProductAnimations()` | ❌ 순수 시각적 애니메이션 (회전만) | ✅ 수정 가능 |
| **라인 242-248** | `premiumCubes` 배열 저장 | ❌ 애니메이션 추적용만 | ✅ 수정 가능 |
| **라인 359** | `goldCrowns` 배열 저장 | ❌ 애니메이션 추적용만 | ✅ 수정 가능 |
| **라인 390-415** | `createPriceLabel()` | ⚠️ 가격 표시 (UI 요소) | ✅ 수정 가능 (시각적만) |
| **라인 41-42, 86, 172, 249, 360, 383** | `userData.productData` 저장 | ⚠️ 상품 정보 메타데이터 | ✅ 수정 가능 (읽기 전용) |

**✅ GiftBox3D.js 분석:**

| 코드 라인 | 기능 | 시스템 연관성 | 수정 가능 여부 |
|-----------|------|---------------|----------------|
| **라인 874-908** | `animate()` 메서드 | ❌ 순수 시각적 애니메이션 (뚜껑/confetti) | ✅ 수정 가능 |
| **라인 431-434** | `userData.productData` 저장 | ⚠️ 상품 정보 메타데이터 | ✅ 수정 가능 (읽기 전용) |

**❌ 발견된 시스템 기능 (절대 수정 금지):**

- **없음** ✅
- 모든 코드는 순수 시각적 요소만 담당
- `userData.productData`는 메타데이터 저장용 (읽기 전용)
- `createPriceLabel()`은 가격 텍스트 표시만 (실제 결제 로직 없음)

#### 리팩토링 시 보호 방안

**1. 애니메이션 코드 분리:**
```javascript
// ✅ 수정 가능: 시각적 애니메이션만
class PremiumCube3D extends BaseFurniture3D {
  updateAnimation() {
    // 회전 속도, 방향 등 시각적 요소만 수정 가능
    this.group.rotation.y += 0.01;
    this.inner.rotation.y -= 0.02;
  }
}
```

**2. 메타데이터 보호:**
```javascript
// ⚠️ 읽기 전용: userData는 건드리지 않음
create() {
  this.group = new THREE.Group();
  // ... Geometry/Material 생성 ...
  
  // ✅ 수정 가능: 시각적 요소만
  this.group.userData.productData = this.options.product; // 메타데이터는 그대로 유지
}
```

**3. 가격 라벨 분리:**
```javascript
// ✅ 수정 가능: UI 요소만 (실제 결제 로직 없음)
createPriceLabel(product) {
  // Canvas Texture 생성 (시각적 요소만)
  // product.price는 읽기만 함 (수정 안 함)
}
```

---

## 🏗️ [단계 2] 새로운 작업장 페이지 구축 계획

### 1. 새 HTML 파일 경로 및 이름

**제안 경로:**
```
homepage1/templates/payment/furniture_workbench.html
```

**이유:**
- `payment/` 폴더에 위치하여 기존 쇼룸과 일관성 유지
- `furniture_workbench` 명명으로 목적 명확화
- 기존 `showroom.html`과 구조 유사하여 유지보수 용이

### 2. 워크벤치 로직 파일

**제안 경로:**
```
homepage1/static/js/3d/FurnitureWorkbench.js
```

**역할:**
- 작업장 환경 초기화 (Three.js 씬, 카메라, 조명)
- URL 파라미터 기반 가구 동적 로딩
- 실시간 디자인 수정 UI 제공
- 쇼룸 환경과 동일한 조명/배경 설정

### 3. 워크벤치 구조 설계

#### 핵심 구현 아이디어

**1. URL 파라미터 기반 가구 동적 로딩:**
```javascript
// 예시 URL: /payment/furniture-workbench?furniture=JewelryDisplay&width=2.5&height=1.8&depth=2
class FurnitureWorkbench {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, ...);
    this.renderer = new THREE.WebGLRenderer({ ... });
    
    // URL 파라미터 파싱
    const params = new URLSearchParams(window.location.search);
    this.furnitureType = params.get('furniture') || 'JewelryDisplay';
    this.furnitureSize = {
      width: parseFloat(params.get('width')) || 2.5,
      height: parseFloat(params.get('height')) || 1.8,
      depth: parseFloat(params.get('depth')) || 2.0
    };
    
    this.loadFurniture();
  }
  
  loadFurniture() {
    // 동적 클래스 로딩
    const FurnitureClass = window[this.furnitureType];
    if (!FurnitureClass) {
      console.error(`가구 클래스를 찾을 수 없습니다: ${this.furnitureType}`);
      return;
    }
    
    // 가구 인스턴스 생성
    this.furniture = new FurnitureClass(
      this.scene,
      { x: 0, y: 0, z: 0 },
      this.furnitureSize
    );
    this.furniture.create();
  }
}
```

**2. 쇼룸 환경 로드 (ShowroomBuilder 활용):**
```javascript
class FurnitureWorkbench {
  initShowroomEnvironment() {
    // ShowroomBuilder를 사용하여 쇼룸 환경 구성
    if (typeof window.ShowroomBuilder !== "undefined") {
      this.builder = new window.ShowroomBuilder(this.scene);
      // 바닥, 벽, 천장, 조명만 로드 (상품 제외)
      this.builder.buildRoomEnvironment(); // 새로운 메서드 필요
    } else {
      // 기본 환경 생성 (간단한 바닥 + 조명)
      this.createBasicEnvironment();
    }
  }
}
```

**3. 실시간 디자인 수정 UI:**
```html
<!-- furniture_workbench.html -->
<div id="workbench-container"></div>
<div id="design-controls">
  <div class="control-group">
    <label for="width">Width:</label>
    <input type="range" id="width" min="0.5" max="5" step="0.1" value="2.5">
    <span id="width-val">2.5</span>
  </div>
  <div class="control-group">
    <label for="height">Height:</label>
    <input type="range" id="height" min="0.5" max="5" step="0.1" value="1.8">
    <span id="height-val">1.8</span>
  </div>
  <div class="control-group">
    <label for="depth">Depth:</label>
    <input type="range" id="depth" min="0.5" max="5" step="0.1" value="2.0">
    <span id="depth-val">2.0</span>
  </div>
  <button id="update-design">디자인 업데이트</button>
  <button id="export-to-showroom">쇼룸에 적용</button>
</div>
```

**4. 쇼룸 연동 (선택적):**
```javascript
class FurnitureWorkbench {
  exportToShowroom() {
    // 현재 디자인 설정을 쇼룸에 전달
    const designConfig = {
      type: this.furnitureType,
      size: this.furnitureSize,
      position: this.furniture.position
    };
    
    // 로컬 스토리지에 저장 (또는 서버로 전송)
    localStorage.setItem('furnitureDesign', JSON.stringify(designConfig));
    
    // 쇼룸 페이지로 리다이렉트
    window.location.href = '/payment/showroom';
  }
}
```

#### 파일 구조 요약

```
homepage1/
├── templates/
│   └── payment/
│       ├── showroom.html (기존)
│       └── furniture_workbench.html (신규)
├── static/
│   └── js/
│       └── 3d/
│           ├── Showroom.js (기존)
│           ├── ShowroomBuilder.js (기존)
│           ├── ProductFactory.js (리팩토링)
│           ├── FurnitureWorkbench.js (신규)
│           ├── GiftBox3D.js (기존)
│           ├── JewelryDisplay.js (기존)
│           ├── StandardCoin3D.js (신규)
│           ├── PremiumCube3D.js (신규)
│           └── GoldCrown3D.js (신규)
└── routes/
    └── payment_routes.py (신규 라우트 추가 필요)
```

#### Flask 라우트 추가 필요

```python
@payment_bp.route("/furniture-workbench", methods=["GET"])
def furniture_workbench():
    """
    가구 디자인 작업장 페이지
    URL 파라미터: ?furniture=JewelryDisplay&width=2.5&height=1.8&depth=2
    """
    try:
        context = _build_shop_context()
        return render_template("payment/furniture_workbench.html", **context)
    except Exception as exc:
        return error(f"작업장 페이지 로딩 실패: {str(exc)}", status=500)
```

---

## 📋 작업 후 필수 보고 사항

### ✅ 계획 요약

1. **가구 클래스 분리:**
   - `StandardCoin3D.js`, `PremiumCube3D.js`, `GoldCrown3D.js` 3개 파일 생성
   - 각 클래스는 `BaseFurniture3D` 인터페이스 구현
   - `ProductFactory.js`는 라우터 역할로 축소

2. **ProductFactory.js 역할:**
   - 순수 공장 메서드만 유지 (생성, 라우팅, 애니메이션 위임)
   - 코드 라인 수 약 70% 감소 예상

3. **UI/UX 비침해 보증:**
   - 모든 애니메이션 코드는 순수 시각적 요소만 (수정 가능)
   - `userData.productData`는 메타데이터 저장용 (읽기 전용)
   - 실제 결제/토큰 로직 없음 (안전)

4. **작업장 페이지 구축:**
   - `furniture_workbench.html` + `FurnitureWorkbench.js` 생성
   - URL 파라미터 기반 동적 가구 로딩
   - 쇼룸 환경과 동일한 조명/배경
   - 실시간 디자인 수정 UI 제공

### 🎯 다음 단계

1. **리팩토링 실행 순서:**
   - Step 1: `StandardCoin3D.js` 생성 및 테스트
   - Step 2: `PremiumCube3D.js` 생성 및 테스트
   - Step 3: `GoldCrown3D.js` 생성 및 테스트
   - Step 4: `ProductFactory.js` 리팩토링
   - Step 5: `FurnitureWorkbench.js` 및 HTML 생성
   - Step 6: Flask 라우트 추가 및 통합 테스트

2. **검증 체크리스트:**
   - [ ] 분리된 클래스가 독립적으로 작동하는가?
   - [ ] ProductFactory가 정상적으로 라우팅하는가?
   - [ ] 애니메이션이 정상 작동하는가?
   - [ ] 작업장 페이지가 가구를 정상 로드하는가?
   - [ ] 쇼룸 환경과 일관성이 유지되는가?

---

**이 보고서를 바탕으로 가장 합리적인 리팩토링 및 작업장 구축을 진행할 수 있습니다.**

