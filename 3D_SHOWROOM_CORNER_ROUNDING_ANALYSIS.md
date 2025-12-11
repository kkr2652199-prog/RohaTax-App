# 3D 쇼룸 모서리 라운딩 분석 및 제안 보고서

**작업 디렉토리**: `homepage1/static/js/3d/ShowroomBuilder.js`  
**분석일**: 2024-12-XX  
**목적**: 벽-벽 및 벽-바닥 모서리 라운딩 방안 제시

---

## 📊 현재 코드 분석

### 1. 바닥 Geometry 생성 코드

**파일**: `ShowroomBuilder.js`  
**메서드**: `buildRoom()`  
**코드 라인**: **29-47줄**

```29:47:homepage1/static/js/3d/ShowroomBuilder.js
// 단순 바닥 시공 (PlaneGeometry - 검은색 버그 원천 봉쇄)
const floorSize = 30; // 벽과 동일한 크기
const floorGeo = new THREE.PlaneGeometry(floorSize, floorSize);

// 바닥 재질 (원본 설정 복구)
const floorMat = new THREE.MeshPhysicalMaterial({
  map: floorTexture,
  color: 0x111111, // 검은색 바닥 (원본)
  roughness: 0.05, // 매우 매끄러운 표면 (대리석 반사)
  metalness: 0.2,
  side: THREE.FrontSide,
  flatShading: false
});

const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI / 2; // 바닥에 눕힘
floor.position.y = 0; // 정확히 바닥
floor.receiveShadow = true;
this.scene.add(floor);
```

**바닥 사양**:
- **Geometry**: `PlaneGeometry(30, 30)` - 30m × 30m 평면
- **위치**: `y = 0` (바닥면)
- **회전**: `rotation.x = -Math.PI / 2` (XZ 평면에 눕힘)
- **재질**: `MeshPhysicalMaterial` (대리석 텍스처)

---

### 2. 벽 Geometry 생성 코드

**파일**: `ShowroomBuilder.js`  
**메서드**: `createSimpleWalls()`  
**코드 라인**: **182-231줄**

```182:231:homepage1/static/js/3d/ShowroomBuilder.js
createSimpleWalls() {
  // 단일 재질 강제 (모든 벽에 동일한 화이트 재질)
  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xFFFFFF, // 완전한 흰색
    roughness: 0.5,
    side: THREE.DoubleSide, // 양면 모두 하얗게
    flatShading: false
  });

  const wallHeight = 15; // 바닥 0에서 천장 15까지
  const wallY = wallHeight / 2; // 7.5 (높이 절반)

  // 뒷벽 (z = -15.5)
  const backWall = new THREE.Mesh(
    new THREE.BoxGeometry(30, 15, 1),
    wallMat
  );
  backWall.position.set(0, wallY, -15.5);
  backWall.receiveShadow = true;
  this.scene.add(backWall);

  // 왼벽 (x = -15.5)
  const leftWall = new THREE.Mesh(
    new THREE.BoxGeometry(1, 15, 30),
    wallMat
  );
  leftWall.position.set(-15.5, wallY, 0);
  leftWall.receiveShadow = true;
  this.scene.add(leftWall);

  // 오른벽 (x = 15.5)
  const rightWall = new THREE.Mesh(
    new THREE.BoxGeometry(1, 15, 30),
    wallMat
  );
  rightWall.position.set(15.5, wallY, 0);
  rightWall.receiveShadow = true;
  this.scene.add(rightWall);

  // 앞벽 (z = 15.5) - 반사를 위해 추가
  const frontWall = new THREE.Mesh(
    new THREE.BoxGeometry(30, 15, 1),
    wallMat
  );
  frontWall.position.set(0, wallY, 15.5);
  frontWall.receiveShadow = true;
  this.scene.add(frontWall);

  console.log("✅ [ShowroomBuilder] 단순 박스 벽 시공 완료 (Pure White Walls)");
}
```

**벽 사양**:
- **뒷벽**: `BoxGeometry(30, 15, 1)` - 위치 `(0, 7.5, -15.5)`
- **왼벽**: `BoxGeometry(1, 15, 30)` - 위치 `(-15.5, 7.5, 0)`
- **오른벽**: `BoxGeometry(1, 15, 30)` - 위치 `(15.5, 7.5, 0)`
- **앞벽**: `BoxGeometry(30, 15, 1)` - 위치 `(0, 7.5, 15.5)`
- **재질**: `MeshStandardMaterial` (화이트)
- **높이**: 15m (바닥 y=0 ~ 천장 y=15)

---

## 🎯 모서리 라운딩 방안 (Cove/Fillet)

### 현재 구조 분석

**방 크기**:
- **너비**: 30m (X축: -15 ~ +15)
- **깊이**: 30m (Z축: -15 ~ +15)
- **높이**: 15m (Y축: 0 ~ 15)

**모서리 위치**:
1. **벽-벽 모서리 (수직 모서리)**: 4개
   - 앞-좌: `(-15.5, 7.5, 15.5)`
   - 앞-우: `(15.5, 7.5, 15.5)`
   - 뒤-좌: `(-15.5, 7.5, -15.5)`
   - 뒤-우: `(15.5, 7.5, -15.5)`

2. **벽-바닥 모서리 (수평 모서리)**: 4개
   - 앞-좌: `(-15.5, 0, 15.5)` ~ `(15.5, 0, 15.5)`
   - 앞-우: `(15.5, 0, 15.5)` ~ `(15.5, 0, -15.5)`
   - 뒤-좌: `(-15.5, 0, -15.5)` ~ `(15.5, 0, -15.5)`
   - 뒤-우: `(-15.5, 0, -15.5)` ~ `(-15.5, 0, 15.5)`

---

## 🔧 제안: 1/4 원통 (Quarter-Cylinder) 코브 Geometry

### 방법론

**CylinderGeometry를 사용하여 1/4 원통 생성**:
- `THREE.CylinderGeometry`의 `thetaStart`와 `thetaLength` 파라미터 활용
- `thetaStart`: 시작 각도
- `thetaLength`: 호의 길이 (π/2 = 90도 = 1/4 원)

---

## 📐 수정 제안 코드

### 1. 벽-벽 모서리 라운딩 (수직 코브)

**추가 위치**: `createSimpleWalls()` 메서드 내부, 벽 생성 후

```javascript
/**
 * 벽-벽 모서리 라운딩 (수직 코브)
 * 4개의 수직 모서리에 1/4 원통 형태의 코브 추가
 */
createWallCornerCoves() {
  const coveRadius = 0.3; // 코브 반지름 (30cm)
  const coveHeight = 15; // 벽 높이와 동일 (15m)
  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xFFFFFF, // 벽과 동일한 화이트
    roughness: 0.5,
    side: THREE.DoubleSide
  });

  // 1/4 원통 Geometry 생성 (90도 호)
  const coveGeo = new THREE.CylinderGeometry(
    coveRadius,      // 상단 반지름
    coveRadius,      // 하단 반지름 (원통)
    coveHeight,      // 높이
    16,              // 방사형 세그먼트
    1,               // 높이 세그먼트
    false,           // openEnded
    Math.PI / 2,     // thetaStart: 90도부터 시작
    Math.PI / 2     // thetaLength: 90도 호 (1/4 원)
  );

  // 모서리 위치 (벽 교차점)
  const cornerPositions = [
    { x: -15.5, z: 15.5, rotationY: 0 },        // 앞-좌
    { x: 15.5, z: 15.5, rotationY: Math.PI / 2 }, // 앞-우
    { x: -15.5, z: -15.5, rotationY: -Math.PI / 2 }, // 뒤-좌
    { x: 15.5, z: -15.5, rotationY: Math.PI }    // 뒤-우
  ];

  cornerPositions.forEach((corner, index) => {
    const cove = new THREE.Mesh(coveGeo, wallMat);
    
    // 위치: 모서리 중심
    cove.position.set(corner.x, coveHeight / 2, corner.z);
    
    // 회전: 각 모서리에 맞게 Y축 회전
    cove.rotation.y = corner.rotationY;
    
    // 벽 안쪽으로 배치 (벽 두께 고려)
    // 벽 두께가 1m이므로, 벽 안쪽 면에서 coveRadius만큼 안쪽으로
    if (corner.x < 0) {
      // 좌측 벽 모서리
      cove.position.x += coveRadius;
    } else {
      // 우측 벽 모서리
      cove.position.x -= coveRadius;
    }
    
    if (corner.z < 0) {
      // 뒷벽 모서리
      cove.position.z += coveRadius;
    } else {
      // 앞벽 모서리
      cove.position.z -= coveRadius;
    }
    
    cove.receiveShadow = true;
    this.scene.add(cove);
  });

  console.log("✅ [ShowroomBuilder] 벽-벽 모서리 코브 추가 완료");
}
```

---

### 2. 벽-바닥 모서리 라운딩 (수평 코브)

**추가 위치**: `buildRoom()` 메서드 내부, 바닥 생성 후

```javascript
/**
 * 벽-바닥 모서리 라운딩 (수평 코브)
 * 4개의 벽-바닥 접합부에 1/4 원통 형태의 코브 추가
 */
createFloorCornerCoves() {
  const coveRadius = 0.3; // 코브 반지름 (30cm)
  const wallLength = 30; // 벽 길이
  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xFFFFFF, // 벽과 동일한 화이트
    roughness: 0.5,
    side: THREE.DoubleSide
  });

  // 1/4 원통 Geometry 생성 (90도 호, 수평으로 눕힘)
  const coveGeo = new THREE.CylinderGeometry(
    coveRadius,      // 반지름
    coveRadius,      // 반지름 (원통)
    wallLength,      // 길이 (벽 길이와 동일)
    16,              // 방사형 세그먼트
    1,               // 높이 세그먼트
    false,           // openEnded
    Math.PI / 2,     // thetaStart: 90도부터 시작
    Math.PI / 2      // thetaLength: 90도 호 (1/4 원)
  );

  // 4개의 벽-바닥 모서리
  const floorCoves = [
    {
      // 앞벽-바닥 (Z = 15.5, X: -15.5 ~ 15.5)
      position: { x: 0, y: coveRadius, z: 15.5 },
      rotation: { x: Math.PI / 2, y: 0, z: 0 }
    },
    {
      // 뒷벽-바닥 (Z = -15.5, X: -15.5 ~ 15.5)
      position: { x: 0, y: coveRadius, z: -15.5 },
      rotation: { x: Math.PI / 2, y: 0, z: Math.PI }
    },
    {
      // 왼벽-바닥 (X = -15.5, Z: -15.5 ~ 15.5)
      position: { x: -15.5, y: coveRadius, z: 0 },
      rotation: { x: Math.PI / 2, y: 0, z: Math.PI / 2 }
    },
    {
      // 오른벽-바닥 (X = 15.5, Z: -15.5 ~ 15.5)
      position: { x: 15.5, y: coveRadius, z: 0 },
      rotation: { x: Math.PI / 2, y: 0, z: -Math.PI / 2 }
    }
  ];

  floorCoves.forEach((coveConfig) => {
    const cove = new THREE.Mesh(coveGeo, wallMat);
    
    // 위치: 벽-바닥 접합부
    cove.position.set(
      coveConfig.position.x,
      coveConfig.position.y, // 바닥 위로 coveRadius만큼 올림
      coveConfig.position.z
    );
    
    // 회전: 수평으로 눕히고 방향 조정
    cove.rotation.set(
      coveConfig.rotation.x, // X축 90도 회전 (수평으로 눕힘)
      coveConfig.rotation.y,
      coveConfig.rotation.z  // Z축 회전으로 방향 조정
    );
    
    cove.receiveShadow = true;
    this.scene.add(cove);
  });

  console.log("✅ [ShowroomBuilder] 벽-바닥 모서리 코브 추가 완료");
}
```

---

## 🔄 buildRoom() 메서드 수정 제안

**현재 코드 구조** (15-87줄):
```javascript
buildRoom() {
  // ... 충돌 범위 업데이트 ...
  
  // 바닥 생성 (29-47줄)
  const floor = ...;
  this.scene.add(floor);
  
  // 천장 베이스 (49-65줄)
  const ceilingBase = ...;
  this.scene.add(ceilingBase);
  
  // 벽 생성 (68줄)
  this.createSimpleWalls();
  
  // 천장 생성 (71줄)
  this.createCofferedCeiling();
  
  return { ... };
}
```

**수정 제안** (코드 추가 위치):
```javascript
buildRoom() {
  // ... 기존 코드 ...
  
  // 바닥 생성
  const floor = ...;
  this.scene.add(floor);
  
  // ✅ [추가] 벽-바닥 모서리 코브 추가
  this.createFloorCornerCoves();
  
  // 천장 베이스
  const ceilingBase = ...;
  this.scene.add(ceilingBase);
  
  // 벽 생성
  this.createSimpleWalls();
  
  // ✅ [추가] 벽-벽 모서리 코브 추가
  this.createWallCornerCoves();
  
  // 천장 생성
  this.createCofferedCeiling();
  
  return { ... };
}
```

---

## 📐 상세 위치 및 회전 계산

### 벽-벽 모서리 (수직 코브)

| 모서리 | X 위치 | Z 위치 | Y 위치 | Y축 회전 | 설명 |
|--------|--------|--------|--------|----------|------|
| **앞-좌** | -15.5 + 0.3 | 15.5 - 0.3 | 7.5 | 0° | 앞벽과 왼벽 교차점 |
| **앞-우** | 15.5 - 0.3 | 15.5 - 0.3 | 7.5 | 90° | 앞벽과 오른벽 교차점 |
| **뒤-좌** | -15.5 + 0.3 | -15.5 + 0.3 | 7.5 | -90° | 뒷벽과 왼벽 교차점 |
| **뒤-우** | 15.5 - 0.3 | -15.5 + 0.3 | 7.5 | 180° | 뒷벽과 오른벽 교차점 |

**위치 계산 로직**:
```javascript
// 벽 두께: 1m
// 벽 안쪽 면: ±15.0 (벽 중심 ±15.5에서 0.5m 안쪽)
// 코브 반지름: 0.3m
// 코브 중심: 벽 안쪽 면에서 coveRadius만큼 더 안쪽

// 예: 앞-좌 모서리
// X: -15.5 (왼벽 중심) + 0.5 (벽 두께의 절반) + 0.3 (코브 반지름) = -14.7
// Z: 15.5 (앞벽 중심) - 0.5 (벽 두께의 절반) - 0.3 (코브 반지름) = 14.7
```

---

### 벽-바닥 모서리 (수평 코브)

| 모서리 | X 위치 | Y 위치 | Z 위치 | X축 회전 | Z축 회전 | 설명 |
|--------|--------|--------|--------|----------|----------|------|
| **앞벽** | 0 | 0.3 | 15.5 | 90° | 0° | 앞벽-바닥 접합부 |
| **뒷벽** | 0 | 0.3 | -15.5 | 90° | 180° | 뒷벽-바닥 접합부 |
| **왼벽** | -15.5 | 0.3 | 0 | 90° | 90° | 왼벽-바닥 접합부 |
| **오른벽** | 15.5 | 0.3 | 0 | 90° | -90° | 오른벽-바닥 접합부 |

**위치 계산 로직**:
```javascript
// 바닥: y = 0
// 벽 하단: y = 0 (벽 높이의 절반이 7.5이므로 하단은 0)
// 코브 반지름: 0.3m
// 코브 중심 Y: coveRadius (바닥 위로 0.3m)

// 예: 앞벽-바닥 모서리
// X: 0 (벽 중심)
// Y: 0.3 (바닥 위로 코브 반지름만큼)
// Z: 15.5 (앞벽 중심)
// 회전: X축 90도 (수평으로 눕힘), Z축 0도 (앞쪽 방향)
```

---

## 🎨 재질 및 시각적 효과

### 재질 제안

```javascript
// 옵션 1: 벽과 동일한 재질 (매끄러운 전환)
const coveMat = new THREE.MeshStandardMaterial({
  color: 0xFFFFFF, // 벽과 동일한 화이트
  roughness: 0.5,
  metalness: 0.0,
  side: THREE.DoubleSide
});

// 옵션 2: 약간 다른 재질 (디테일 강조)
const coveMat = new THREE.MeshStandardMaterial({
  color: 0xF5F5F5, // 약간 더 밝은 화이트
  roughness: 0.3,   // 더 매끄러움
  metalness: 0.0,
  side: THREE.DoubleSide
});

// 옵션 3: 골드 악센트 (럭셔리 효과)
const coveMat = new THREE.MeshStandardMaterial({
  color: 0xFFD700, // 골드
  roughness: 0.2,
  metalness: 0.9,
  emissive: 0xFFD700,
  emissiveIntensity: 0.1,
  side: THREE.DoubleSide
});
```

---

## 📏 코브 크기 권장 사항

### 반지름 선택 가이드

| 반지름 | 시각적 효과 | 권장 용도 |
|--------|------------|----------|
| **0.1m** | 미세한 라운딩 | 미니멀한 디자인 |
| **0.3m** | 부드러운 전환 | **권장** (균형잡힌 효과) |
| **0.5m** | 뚜렷한 라운딩 | 강조된 모서리 |
| **0.8m** | 매우 부드러운 전환 | 매우 부드러운 느낌 |

**권장값**: `0.3m` (30cm)
- 벽 두께(1m)의 약 30%
- 시각적으로 자연스러운 전환
- 성능 영향 최소화

---

## ⚙️ 구현 시 주의사항

### 1. Z-Fighting 방지
```javascript
// 코브를 벽/바닥보다 약간 안쪽으로 배치
const zFightingOffset = 0.001; // 1mm 오프셋
cove.position.x += zFightingOffset; // 또는 적절한 방향으로
```

### 2. Geometry 재사용
```javascript
// 성능 최적화: Geometry를 한 번만 생성하고 재사용
const coveGeo = new THREE.CylinderGeometry(...);
// 여러 Mesh에서 동일한 Geometry 사용
```

### 3. 그림자 설정
```javascript
cove.castShadow = true;    // 그림자 생성
cove.receiveShadow = true; // 그림자 수신
```

### 4. 세그먼트 수 조정
```javascript
// 세그먼트 수가 많을수록 부드럽지만 성능 저하
// 권장: 16-32 세그먼트
const coveGeo = new THREE.CylinderGeometry(
  coveRadius,
  coveRadius,
  coveHeight,
  16,  // 방사형 세그먼트 (16 = 부드러움과 성능의 균형)
  1    // 높이 세그먼트 (1 = 원통이므로 충분)
);
```

---

## 🔄 통합 코드 예시

### 완전한 구현 예시 (참고용)

```javascript
/**
 * ShowroomBuilder 클래스에 추가할 메서드들
 */

/**
 * 모든 모서리 코브 생성 (통합 메서드)
 */
createCornerCoves() {
  // 벽-바닥 모서리 코브
  this.createFloorCornerCoves();
  
  // 벽-벽 모서리 코브
  this.createWallCornerCoves();
  
  console.log("✅ [ShowroomBuilder] 모든 모서리 코브 추가 완료");
}

/**
 * buildRoom() 메서드 수정 예시
 */
buildRoom() {
  // ... 기존 코드 ...
  
  // 바닥 생성
  const floor = ...;
  this.scene.add(floor);
  
  // ✅ [추가] 모서리 코브 추가
  this.createCornerCoves();
  
  // 벽 생성
  this.createSimpleWalls();
  
  // 천장 생성
  this.createCofferedCeiling();
  
  return { ... };
}
```

---

## 📊 성능 영향 분석

### Geometry 복잡도

| 항목 | 기존 | 추가 후 | 증가율 |
|------|------|---------|--------|
| **Mesh 개수** | 5개 (바닥 1 + 벽 4) | 13개 (+ 코브 8) | +160% |
| **삼각형 수** | ~200 | ~400 | +100% |
| **예상 FPS 영향** | - | -2~5% | 미미 |

**결론**: 성능 영향은 미미하며, 시각적 품질 향상이 큼

---

## ✅ 체크리스트

### 구현 전 확인 사항
- [ ] 코브 반지름 결정 (권장: 0.3m)
- [ ] 재질 선택 (벽과 동일 vs 골드 악센트)
- [ ] 세그먼트 수 결정 (권장: 16)
- [ ] Z-Fighting 방지 오프셋 설정

### 구현 후 확인 사항
- [ ] 모든 모서리에 코브가 정확히 배치되었는지 확인
- [ ] 벽/바닥과의 겹침 없음 확인
- [ ] 그림자가 정상적으로 표시되는지 확인
- [ ] 성능 저하 없음 확인 (FPS 모니터링)

---

## 🎯 최종 권장 사항

### 1. 단계적 구현
- **1단계**: 벽-바닥 모서리 코브만 추가 (4개)
- **2단계**: 벽-벽 모서리 코브 추가 (4개)
- **3단계**: 재질 및 크기 미세 조정

### 2. 반지름 선택
- **초기값**: `0.3m` (30cm)
- **테스트 후 조정 가능**: 0.2m ~ 0.5m 범위에서 조정

### 3. 재질 선택
- **권장**: 벽과 동일한 화이트 재질 (자연스러운 전환)
- **옵션**: 골드 악센트 (럭셔리 효과 강조)

---

**마지막 업데이트**: 2024-12-XX  
**작성자**: AI Assistant  
**상태**: ✅ 분석 완료, 코드 수정 전 단계


