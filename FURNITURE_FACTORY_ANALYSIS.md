# 🔍 3D 쇼룸 가구 공장(Factory Pattern) 도입 가능성 분석 보고서

**분석 일시**: 2025-12-12  
**분석 목적**: '공간(Showroom)'과 '가구(Furniture)' 분리 리팩토링 가능성 및 WebGL 위험성 평가  
**분석자**: The Executor

---

## 📊 1. 가구 식별 (Furniture Identification)

### 1.1 현재 가구 구현 현황

#### ✅ **무료 상품 2종 (Event 상품 - 선물박스)**

**구현 방식**: **클래스 방식** (이미 분리됨)
- **클래스**: `GiftBox3D` (별도 파일: `GiftBox3D.js`)
- **생성 경로**: 
  ```javascript
  // Showroom.js:548, 560
  this.factory.createEventProduct(eventProducts[0], productPos)
  // → ProductFactory.js:293
  // → GiftBox3D 클래스 인스턴스 생성
  ```
- **특징**: 
  - ✅ 이미 Factory Pattern 적용됨
  - ✅ Static Material 공유 시스템 구현됨
  - ✅ 독립적인 클래스로 분리 완료

#### ⚠️ **유료 상품 3종 (Standard, Premium, Gold)**

**구현 방식**: **하이브리드 (중복 구조)**

**경로 1: Factory Pattern (권장 경로)**
```javascript
// Showroom.js:509, 522, 535
this.factory.createRegularProduct(gold, productPos)
// → ProductFactory.js:337
// → ProductFactory.createStandardCoin() / createPremiumCube() / createGoldCrown()
```
- ✅ **ProductFactory 클래스 사용** (별도 파일: `ProductFactory.js`)
- ✅ **Static Material 공유 시스템** 구현됨
- ✅ **WebGL 최적화 완료**

**경로 2: 하드코딩 메서드 (중복 코드)**
```javascript
// Showroom.js:662-704
createRegularProduct(product, position, index) {
  // ...
  if (normalized === "standard") {
    group = this.createStandardCoin(product, position);  // ⚠️ Showroom.js 내부 메서드
  } else if (normalized === "premium") {
    group = this.createPremiumCube(product, position);  // ⚠️ Showroom.js 내부 메서드
  } else if (normalized === "gold") {
    group = this.createGoldCrown(product, position);    // ⚠️ Showroom.js 내부 메서드
  }
}
```
- ⚠️ **Showroom.js 내부에 하드코딩된 메서드** 존재
- ⚠️ **ProductFactory와 중복 구현**
- ⚠️ **Static Material 공유 없음** (매번 `new THREE.MeshStandardMaterial()` 생성)

**경로 3: 이벤트 상품 하드코딩 (중복 코드)**
```javascript
// Showroom.js:633-660
createEventProduct(product, position) {
  const giftBox = new GiftBox3D(null, {...});
  // ⚠️ Showroom.js 내부에서 직접 생성
  this.scene.add(group);
  this.addProductSpotlight(position, 0xffd700);
}
```
- ⚠️ **ProductFactory.createEventProduct()와 중복**

### 1.2 가구 구현 방식 요약

| 가구 유형 | Factory Pattern | 하드코딩 메서드 | 상태 |
|---------|----------------|---------------|------|
| **Event 상품 (선물박스)** | ✅ `ProductFactory.createEventProduct()` | ⚠️ `Showroom.createEventProduct()` | **중복** |
| **Standard (코인)** | ✅ `ProductFactory.createStandardCoin()` | ⚠️ `Showroom.createStandardCoin()` | **중복** |
| **Premium (큐브)** | ✅ `ProductFactory.createPremiumCube()` | ⚠️ `Showroom.createPremiumCube()` | **중복** |
| **Gold (크라운)** | ✅ `ProductFactory.createGoldCrown()` | ⚠️ `Showroom.createGoldCrown()` | **중복** |
| **Fallback** | ✅ `ProductFactory.createFallbackProduct()` | ⚠️ `Showroom.createFallbackProduct()` | **중복** |

**결론**: 
- ✅ **Factory Pattern 이미 구현됨** (ProductFactory 클래스)
- ⚠️ **하드코딩 메서드가 중복으로 존재** (Showroom.js 내부)
- ⚠️ **현재는 Factory Pattern 경로를 사용 중** (Showroom.js:509, 522, 535, 548, 560)

---

## 🎨 2. 텍스처 로딩 방식 분석 (WebGL Risk Check)

### 2.1 텍스처 관리 현황

#### ✅ **Static Material 공유 시스템 (이미 구현됨)**

**ProductFactory.js**:
```javascript
// Static Material 공유
static sharedCoinMat = null;
static sharedCubeCoreMat = null;
static sharedGoldMat = null;
// ...

static getCoinMaterial() {
  if (!ProductFactory.sharedCoinMat) {
    ProductFactory.sharedCoinMat = new THREE.MeshStandardMaterial({...});
  }
  return ProductFactory.sharedCoinMat;  // ✅ 공유 Material 반환
}
```

**GiftBox3D.js**:
```javascript
// Static Material 공유
static sharedBoxMat = {};
static sharedLinerMat = null;
static sharedRibbonMat = {};
// ...

static getBoxMaterial(boxColor) {
  const colorKey = boxColor.toString();
  if (!GiftBox3D.sharedBoxMat[colorKey]) {
    GiftBox3D.sharedBoxMat[colorKey] = new THREE.MeshStandardMaterial({...});
  }
  return GiftBox3D.sharedBoxMat[colorKey];  // ✅ 공유 Material 반환
}
```

**ShowroomBuilder.js**:
```javascript
// Static Texture 공유
static sharedFloorTexture = null;
static sharedFloorMat = null;
// ...

static createMarbleTexture() {
  if (!ShowroomBuilder.sharedFloorTexture) {
    ShowroomBuilder.sharedFloorTexture = new THREE.CanvasTexture(canvas);
  }
  return ShowroomBuilder.sharedFloorTexture;  // ✅ 공유 Texture 반환
}
```

#### ⚠️ **하드코딩 메서드의 텍스처 관리 (위험)**

**Showroom.js 내부 하드코딩 메서드들**:
```javascript
// Showroom.js:709, 721, 749, 790, 828, 866
createStandardCoin(product, position) {
  const coinMat = new THREE.MeshStandardMaterial({...});  // ⚠️ 매번 새로 생성
  const toothMat = new THREE.MeshStandardMaterial({...}); // ⚠️ 매번 새로 생성
  const rimMat = new THREE.MeshStandardMaterial({...});   // ⚠️ 매번 새로 생성
}

createPremiumCube(product, position) {
  const coreMat = new THREE.MeshPhysicalMaterial({...}); // ⚠️ 매번 새로 생성 (MeshPhysicalMaterial!)
}

createGoldCrown(product, position) {
  const goldMat = new THREE.MeshPhysicalMaterial({...});  // ⚠️ 매번 새로 생성 (MeshPhysicalMaterial!)
  const coreMat = new THREE.MeshPhysicalMaterial({...});  // ⚠️ 매번 새로 생성 (MeshPhysicalMaterial!)
}
```

**문제점**:
- ⚠️ **Static Material 공유 없음**: 매번 새 Material 생성
- ⚠️ **MeshPhysicalMaterial 사용**: 텍스처 유닛을 더 많이 소비 (envMap, transmission 등)
- ⚠️ **WebGL 텍스처 유닛 초과 위험**: 가구를 여러 번 생성하면 위험

### 2.2 CanvasTexture 생성 현황

**CanvasTexture는 개별 생성되지만 Material은 공유됨**:
```javascript
// ProductFactory.js:645
const texture = new THREE.CanvasTexture(canvas);  // 개별 생성
const spriteMat = new THREE.SpriteMaterial({ map: texture });  // Material은 공유 가능

// GiftBox3D.js:604
const texture = new THREE.CanvasTexture(canvas);  // 개별 생성
this.textures.push(texture);  // 메모리 관리용 배열에 저장
```

**현재 상태**:
- ✅ **CanvasTexture는 개별 생성** (가격 라벨 등 동적 텍스트)
- ✅ **Material은 Static 공유** (ProductFactory, GiftBox3D)
- ⚠️ **하드코딩 메서드는 Material도 개별 생성** (위험)

### 2.3 WebGL 텍스처 유닛 초과 위험도 평가

#### ✅ **현재 Factory Pattern 경로 사용 시: 안전**

**이유**:
- ✅ Static Material 공유 시스템으로 텍스처 유닛 절약
- ✅ MeshStandardMaterial 사용 (MeshPhysicalMaterial보다 적은 유닛 소비)
- ✅ Geometry도 Static 공유로 메모리 절약

**예상 텍스처 유닛 사용량** (Factory Pattern 경로):
- 바닥 텍스처: 1개 (공유)
- ProductFactory Materials: ~10개 (Static 공유)
- GiftBox3D Materials: ~5개 (Static 공유)
- CanvasTexture (가격 라벨): 5개 (개별, 하지만 Material 공유)
- **총 예상**: ~16개 이하 (안전 범위)

#### ⚠️ **하드코딩 메서드 사용 시: 위험**

**이유**:
- ⚠️ 매번 새 Material 생성 (공유 없음)
- ⚠️ MeshPhysicalMaterial 사용 (더 많은 텍스처 유닛 소비)
- ⚠️ 가구를 여러 번 생성하면 텍스처 유닛 초과 가능

**예상 텍스처 유닛 사용량** (하드코딩 메서드 경로):
- 바닥 텍스처: 1개
- Standard Coin Materials: 3개 × N개 인스턴스
- Premium Cube Materials: 2개 × N개 인스턴스 (MeshPhysicalMaterial!)
- Gold Crown Materials: 3개 × N개 인스턴스 (MeshPhysicalMaterial!)
- **총 예상**: 16개 초과 가능 (위험)

### 2.4 가구 공장 분리 시 WebGL 위험도

#### ✅ **위험도: 낮음 (Low Risk)**

**이유**:
1. ✅ **Static Material 공유 시스템 이미 구현됨**
   - ProductFactory, GiftBox3D 모두 Static Material 사용
   - 가구를 별도 파일로 분리해도 Static 공유 유지 가능

2. ✅ **현재 Factory Pattern 경로 사용 중**
   - Showroom.js는 `this.factory.createRegularProduct()` 사용
   - 하드코딩 메서드는 사용되지 않음 (중복 코드)

3. ✅ **분리 시에도 Static 공유 유지 가능**
   - 가구 클래스를 별도 파일로 분리해도 Static 속성은 유지됨
   - 예: `FurnitureFactory.sharedCoinMat` (Static)

**주의사항**:
- ⚠️ **하드코딩 메서드 제거 필수**: 중복 코드 제거 시 위험도 제거
- ⚠️ **Static 공유 시스템 유지**: 분리 시에도 Static 속성 유지 필수

---

## 🔗 3. 결합도 분석 (Coupling Check)

### 3.1 Showroom 클래스와의 결합도

#### **강한 결합 (Tight Coupling)**

**1. 씬(Scene) 객체 결합**
```javascript
// Showroom.js:654, 693
this.scene.add(group);  // ⚠️ Showroom의 scene에 직접 추가

// ProductFactory.js:368
this.scene.add(group);  // ⚠️ ProductFactory도 scene에 직접 추가
```

**2. 조명(Light) 결합**
```javascript
// Showroom.js:512, 525, 538, 551, 563, 657, 701
this.addProductSpotlight(productPos, 0xffd700);  // ⚠️ Showroom의 조명 메서드 사용

// Showroom.js:184-201
addProductSpotlight(position, color) {
  const spotlight = new THREE.SpotLight(color, 2, 10, Math.PI / 6, 0.3, 2);
  this.scene.add(spotlight);  // ⚠️ Showroom의 scene에 조명 추가
  this.spotLights.push(spotlight);  // ⚠️ Showroom의 배열에 저장
}
```

**3. 카메라(Camera) 결합**
```javascript
// Showroom.js:690-691
const lookAtTarget = new THREE.Vector3(0, 3.8, 12); // 카메라 높이에 맞춤
group.lookAt(lookAtTarget);  // ⚠️ 카메라 위치 하드코딩
```

**4. 메시 배열 관리**
```javascript
// Showroom.js:511, 524, 537, 550, 562, 655, 694
this.meshes.push(productGroup);  // ⚠️ Showroom의 meshes 배열에 추가
```

### 3.2 ProductFactory와의 결합도

#### **중간 결합 (Medium Coupling)**

**1. 씬(Scene) 의존성**
```javascript
// ProductFactory.js:34
constructor(scene) {
  this.scene = scene;  // ⚠️ Scene 객체 의존
}

// ProductFactory.js:368
this.scene.add(group);  // ⚠️ Scene에 직접 추가
```

**2. 조명 독립성**
```javascript
// ProductFactory.js:368
this.scene.add(group);
// ⚠️ 조명은 추가하지 않음 (Showroom에서 관리)
```

**3. 카메라 독립성**
```javascript
// ProductFactory.js:366
group.rotation.set(0, 0, 0);  // ⚠️ lookAt() 제거됨 (카메라 독립)
```

### 3.3 가구 공장 분리 시 끊어질 연결고리

#### **필요한 인터페이스 설계**

**1. 씬(Scene) 인터페이스**
```javascript
// 현재: 직접 scene 객체 전달
constructor(scene) {
  this.scene = scene;
}

// 제안: 인터페이스 패턴
interface SceneManager {
  add(object: THREE.Object3D): void;
  remove(object: THREE.Object3D): void;
}
```

**2. 조명(Light) 인터페이스**
```javascript
// 현재: Showroom.addProductSpotlight() 직접 호출
this.addProductSpotlight(position, color);

// 제안: 콜백 패턴 또는 이벤트 시스템
interface LightManager {
  addSpotlight(position: THREE.Vector3, color: number): THREE.SpotLight;
}

// 또는
furniture.onCreated((furniture) => {
  lightManager.addSpotlight(furniture.position, furniture.lightColor);
});
```

**3. 메시 관리 인터페이스**
```javascript
// 현재: Showroom.meshes 배열에 직접 추가
this.meshes.push(productGroup);

// 제안: 레지스트리 패턴
interface MeshRegistry {
  register(mesh: THREE.Object3D, metadata: ProductData): void;
  unregister(mesh: THREE.Object3D): void;
}
```

---

## 📋 4. 리팩토링 난이도 평가

### 4.1 난이도: **중간 (Medium)**

#### **이유**:

**✅ 유리한 요소 (Low Difficulty)**:
1. ✅ **Factory Pattern 이미 구현됨**
   - ProductFactory 클래스가 이미 존재
   - Static Material 공유 시스템 구현됨
   - WebGL 최적화 완료

2. ✅ **가구 클래스 이미 분리됨**
   - GiftBox3D: 별도 파일로 분리 완료
   - ProductFactory: 별도 파일로 분리 완료

3. ✅ **현재 Factory Pattern 경로 사용 중**
   - Showroom.js는 `this.factory.createRegularProduct()` 사용
   - 하드코딩 메서드는 사용되지 않음

**⚠️ 어려운 요소 (Medium Difficulty)**:
1. ⚠️ **중복 코드 제거 필요**
   - Showroom.js의 하드코딩 메서드들 제거 필요
   - `createEventProduct()`, `createRegularProduct()`, `createStandardCoin()`, `createPremiumCube()`, `createGoldCrown()`, `createFallbackProduct()`

2. ⚠️ **결합도 해소 필요**
   - 씬(Scene) 의존성: 인터페이스 패턴 도입
   - 조명(Light) 의존성: 콜백 또는 이벤트 시스템 도입
   - 메시 관리: 레지스트리 패턴 도입

3. ⚠️ **테스트 필요**
   - 분리 후 기능 동작 확인
   - WebGL 텍스처 유닛 확인
   - 조명 및 카메라 동작 확인

---

## 🎯 5. 제안 (Technical Recommendations)

### 5.1 즉시 조치 (High Priority)

#### **1. 중복 코드 제거**
```javascript
// Showroom.js에서 제거할 메서드들:
- createEventProduct()      // ProductFactory.createEventProduct() 사용
- createRegularProduct()     // ProductFactory.createRegularProduct() 사용
- createStandardCoin()       // ProductFactory.createStandardCoin() 사용
- createPremiumCube()        // ProductFactory.createPremiumCube() 사용
- createGoldCrown()          // ProductFactory.createGoldCrown() 사용
- createFallbackProduct()    // ProductFactory.createFallbackProduct() 사용
```

**이유**:
- ✅ 중복 코드 제거로 유지보수성 향상
- ✅ WebGL 텍스처 유닛 위험 제거 (하드코딩 메서드는 Static 공유 없음)
- ✅ Factory Pattern 일관성 유지

#### **2. 인터페이스 패턴 도입**

**SceneManager 인터페이스**:
```javascript
// core/furniture_utils/SceneManager.js (연동 모듈)
class SceneManager {
  constructor(scene) {
    this.scene = scene;
    this.meshes = [];
  }
  
  add(object) {
    this.scene.add(object);
    this.meshes.push(object);
  }
  
  remove(object) {
    this.scene.remove(object);
    const index = this.meshes.indexOf(object);
    if (index > -1) this.meshes.splice(index, 1);
  }
}
```

**LightManager 인터페이스**:
```javascript
// core/furniture_utils/LightManager.js (연동 모듈)
class LightManager {
  constructor(scene) {
    this.scene = scene;
    this.spotLights = [];
  }
  
  addSpotlight(position, color, intensity = 2) {
    const spotlight = new THREE.SpotLight(color, intensity, 10, Math.PI / 6, 0.3, 2);
    spotlight.position.copy(position);
    spotlight.position.y += 2; // 상품 위 2m
    this.scene.add(spotlight);
    this.spotLights.push(spotlight);
    return spotlight;
  }
}
```

### 5.2 단기 조치 (Medium Priority)

#### **3. FurnitureFactory 클래스 통합**

**현재 구조**:
```
ProductFactory.js  (유료 상품)
GiftBox3D.js       (무료 상품)
```

**제안 구조** (연장형 원칙 준수):
```
ProductFactory.js  (메인 파일 - 분리 금지)
├── core/furniture_utils/
│   ├── StandardFurniture.js    (연동 모듈)
│   ├── PremiumFurniture.js     (연동 모듈)
│   ├── GoldFurniture.js        (연동 모듈)
│   └── EventFurniture.js        (연동 모듈)
```

**또는 통합 Factory**:
```javascript
// core/furniture_utils/FurnitureFactory.js (연동 모듈)
class FurnitureFactory {
  static createFurniture(type, product, position, sceneManager, lightManager) {
    switch(type) {
      case 'standard':
        return StandardFurniture.create(product, position, sceneManager, lightManager);
      case 'premium':
        return PremiumFurniture.create(product, position, sceneManager, lightManager);
      case 'gold':
        return GoldFurniture.create(product, position, sceneManager, lightManager);
      case 'event':
        return EventFurniture.create(product, position, sceneManager, lightManager);
    }
  }
}
```

### 5.3 장기 조치 (Low Priority)

#### **4. 완전한 분리 (선택적)**

**최종 목표 구조**:
```
Showroom.js              (공간 관리만)
├── 씬(Scene) 관리
├── 카메라(Camera) 관리
├── 조명(Light) 관리
└── 가구 배치 (FurnitureFactory 호출)

FurnitureFactory.js      (가구 생성만)
├── StandardFurniture
├── PremiumFurniture
├── GoldFurniture
└── EventFurniture
```

**인터페이스**:
```javascript
// Showroom → FurnitureFactory
const furniture = FurnitureFactory.create({
  type: 'standard',
  product: productData,
  position: position,
  sceneManager: this.sceneManager,  // 인터페이스
  lightManager: this.lightManager   // 인터페이스
});
```

---

## 🎯 6. 최종 평가 및 권고사항

### 6.1 가구 공장 패턴 도입 가능성: **✅ 가능 (Feasible)**

**이유**:
- ✅ Factory Pattern 이미 구현됨
- ✅ Static Material 공유 시스템으로 WebGL 안전
- ✅ 가구 클래스 이미 분리됨
- ⚠️ 중복 코드 제거만 필요

### 6.2 WebGL 텍스처 초과 위험도: **✅ 낮음 (Low Risk)**

**이유**:
- ✅ Static Material 공유 시스템으로 텍스처 유닛 절약
- ✅ 현재 Factory Pattern 경로 사용 중 (안전)
- ⚠️ 하드코딩 메서드 제거 시 위험 완전 제거

### 6.3 리팩토링 난이도: **⚠️ 중간 (Medium)**

**이유**:
- ✅ 기반 구조는 이미 완성됨
- ⚠️ 중복 코드 제거 필요
- ⚠️ 인터페이스 패턴 도입 필요

### 6.4 권고사항

#### **즉시 조치 (1단계)**:
1. ✅ **Showroom.js의 하드코딩 메서드 제거**
   - `createEventProduct()`, `createRegularProduct()`, `createStandardCoin()`, `createPremiumCube()`, `createGoldCrown()`, `createFallbackProduct()` 삭제
   - ProductFactory 경로만 사용하도록 통일

2. ✅ **검증**
   - 기능 동작 확인
   - WebGL 텍스처 유닛 확인

#### **단기 조치 (2단계)**:
3. ⚠️ **인터페이스 패턴 도입** (연동 모듈로 확장)
   - SceneManager 연동 모듈 생성
   - LightManager 연동 모듈 생성

4. ⚠️ **FurnitureFactory 통합** (선택적)
   - ProductFactory와 GiftBox3D를 통합하는 연동 모듈 생성

#### **장기 조치 (3단계)**:
5. ⚠️ **완전한 분리** (선택적)
   - Showroom은 공간 관리만
   - FurnitureFactory는 가구 생성만

---

## 📊 7. 종합 평가표

| 항목 | 현재 상태 | 분리 후 예상 | 위험도 |
|------|----------|-------------|--------|
| **가구 구현 방식** | 하이브리드 (Factory + 하드코딩) | Factory Pattern 통일 | ✅ 낮음 |
| **텍스처 관리** | Static 공유 (Factory) + 개별 생성 (하드코딩) | Static 공유 통일 | ✅ 낮음 |
| **WebGL 위험도** | 낮음 (Factory 경로 사용) | 낮음 (하드코딩 제거) | ✅ 낮음 |
| **결합도** | 중간 (Scene, Light 의존) | 낮음 (인터페이스 도입) | ⚠️ 중간 |
| **리팩토링 난이도** | - | 중간 | ⚠️ 중간 |

---

**분석 완료**: 2025-12-12  
**결론**: 가구 공장 패턴 도입 **가능**, WebGL 위험도 **낮음**, 리팩토링 난이도 **중간**

