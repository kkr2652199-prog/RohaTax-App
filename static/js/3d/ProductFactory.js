/**
 * ProductFactory - 상품 3D 모델 생성 연동 모듈
 * Showroom.js의 상품 생성 기능을 담당
 */
class ProductFactory {
  /**
   * ✅ WebGL 텍스처 유닛 최적화: Static Material 공유
   * 모든 ProductFactory 인스턴스가 동일한 Material을 공유하여 텍스처 유닛 절약
   */
  static sharedCoinMat = null;          // Standard 코인 Material
  static sharedToothMat = null;          // 톱니바퀴 Material
  static sharedRimMat = null;            // 림 Material
  static sharedCubeCoreMat = null;       // Premium 큐브 코어 Material
  static sharedCubeLineMat = null;       // Premium 큐브 와이어프레임 Material
  static sharedCubeLineMatTransparent = null; // Premium 큐브 와이어프레임 Material (투명)
  static sharedGoldMat = null;            // Gold 크라운 Material
  static sharedGoldCoreMat = null;        // Gold 크라운 코어 Material
  static sharedGoldParticleMat = null;   // Gold 파티클 Material
  static sharedFallbackMat = null;        // Fallback Material
  
  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * 모든 ProductFactory 인스턴스가 동일한 Geometry를 공유하여 메모리 절약
   */
  static sharedCoinGeo = null;           // Standard 코인 Geometry
  static sharedToothGeo = null;          // 톱니바퀴 Geometry
  static sharedRimGeo = null;            // 림 Geometry
  static sharedCubeGeo = null;           // Premium 큐브 Geometry
  static sharedCubeInnerGeo = null;      // Premium 큐브 내부 Geometry
  static sharedRingGeo = null;           // Gold 링 Geometry
  static sharedCoreGeo = null;           // Gold 코어 Geometry
  static sharedFallbackGeo = null;       // Fallback Geometry

  constructor(scene) {
    this.scene = scene;
    this.standardCoins = [];
    this.premiumCubes = [];
    this.goldCrowns = [];
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Standard 코인 Material 가져오기
   */
  static getCoinMaterial() {
    if (!ProductFactory.sharedCoinMat) {
      ProductFactory.sharedCoinMat = new THREE.MeshStandardMaterial({
        color: 0xc0c0c0,
        metalness: 1.0,
        roughness: 0.2
      });
    }
    return ProductFactory.sharedCoinMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 톱니바퀴 Material 가져오기
   */
  static getToothMaterial() {
    if (!ProductFactory.sharedToothMat) {
      ProductFactory.sharedToothMat = new THREE.MeshStandardMaterial({
        color: 0x888888,
        metalness: 0.8,
        roughness: 0.3
      });
    }
    return ProductFactory.sharedToothMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 림 Material 가져오기
   */
  static getRimMaterial() {
    if (!ProductFactory.sharedRimMat) {
      ProductFactory.sharedRimMat = new THREE.MeshStandardMaterial({
        color: 0xfffff0,
        metalness: 1,
        roughness: 0.1
      });
    }
    return ProductFactory.sharedRimMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Premium 큐브 코어 Material 가져오기 (MeshStandardMaterial로 변경)
   */
  static getCubeCoreMaterial() {
    if (!ProductFactory.sharedCubeCoreMat) {
      ProductFactory.sharedCubeCoreMat = new THREE.MeshStandardMaterial({
        color: 0x00FFFF,
        roughness: 0.1,
        metalness: 0.8,
        emissive: 0x004444,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.8
        // MeshPhysicalMaterial의 transmission, clearcoat 제거: MeshStandardMaterial로 변경하여 텍스처 유닛 절약
      });
    }
    return ProductFactory.sharedCubeCoreMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Premium 큐브 와이어프레임 Material 가져오기
   */
  static getCubeLineMaterial() {
    if (!ProductFactory.sharedCubeLineMat) {
      ProductFactory.sharedCubeLineMat = new THREE.LineBasicMaterial({ 
        color: 0x00FFFF // 네온 시안
      });
    }
    return ProductFactory.sharedCubeLineMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Premium 큐브 와이어프레임 Material 가져오기 (투명)
   */
  static getCubeLineMaterialTransparent() {
    if (!ProductFactory.sharedCubeLineMatTransparent) {
      ProductFactory.sharedCubeLineMatTransparent = new THREE.LineBasicMaterial({ 
        color: 0x00FFFF, 
        transparent: true, 
        opacity: 0.5 
      });
    }
    return ProductFactory.sharedCubeLineMatTransparent;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Gold 크라운 Material 가져오기 (MeshStandardMaterial로 변경)
   */
  static getGoldMaterial() {
    if (!ProductFactory.sharedGoldMat) {
      ProductFactory.sharedGoldMat = new THREE.MeshStandardMaterial({
        color: 0xFFD700,
        metalness: 1.0,
        roughness: 0.1,
        emissive: 0x332200,
        emissiveIntensity: 0.3
        // MeshPhysicalMaterial의 clearcoat 제거: MeshStandardMaterial로 변경하여 텍스처 유닛 절약
      });
    }
    return ProductFactory.sharedGoldMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Gold 크라운 코어 Material 가져오기 (MeshStandardMaterial로 변경)
   */
  static getGoldCoreMaterial() {
    if (!ProductFactory.sharedGoldCoreMat) {
      ProductFactory.sharedGoldCoreMat = new THREE.MeshStandardMaterial({
        color: 0xFFD700,
        metalness: 0.8,
        roughness: 0.1,
        emissive: 0xFFAA00,
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.9
      });
    }
    return ProductFactory.sharedGoldCoreMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Gold 파티클 Material 가져오기
   */
  static getGoldParticleMaterial() {
    if (!ProductFactory.sharedGoldParticleMat) {
      ProductFactory.sharedGoldParticleMat = new THREE.PointsMaterial({ 
        color: 0xFFD700, 
        size: 0.05,
        transparent: true,
        opacity: 0.8
      });
    }
    return ProductFactory.sharedGoldParticleMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * Fallback Material 가져오기
   */
  static getFallbackMaterial() {
    if (!ProductFactory.sharedFallbackMat) {
      ProductFactory.sharedFallbackMat = new THREE.MeshStandardMaterial({ 
        color: 0x808080, 
        roughness: 0.4 
      });
    }
    return ProductFactory.sharedFallbackMat;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Standard 코인 Geometry 가져오기
   */
  static getCoinGeometry(radius = 1.2, height = 0.25) {
    if (!ProductFactory.sharedCoinGeo) {
      ProductFactory.sharedCoinGeo = new THREE.CylinderGeometry(radius, radius, height, 64);
    }
    return ProductFactory.sharedCoinGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * 톱니바퀴 Geometry 가져오기
   */
  static getToothGeometry(width = 0.08, height = 0.15) {
    if (!ProductFactory.sharedToothGeo) {
      ProductFactory.sharedToothGeo = new THREE.BoxGeometry(width, height, width);
    }
    return ProductFactory.sharedToothGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * 림 Geometry 가져오기
   */
  static getRimGeometry(radius = 1.25, tube = 0.08) {
    if (!ProductFactory.sharedRimGeo) {
      ProductFactory.sharedRimGeo = new THREE.TorusGeometry(radius, tube, 16, 100);
    }
    return ProductFactory.sharedRimGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Premium 큐브 Geometry 가져오기
   */
  static getCubeGeometry(size = 1.6) {
    if (!ProductFactory.sharedCubeGeo) {
      ProductFactory.sharedCubeGeo = new THREE.BoxGeometry(size, size, size);
    }
    return ProductFactory.sharedCubeGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Premium 큐브 내부 Geometry 가져오기
   */
  static getCubeInnerGeometry(size = 1) {
    if (!ProductFactory.sharedCubeInnerGeo) {
      ProductFactory.sharedCubeInnerGeo = new THREE.BoxGeometry(size, size, size);
    }
    return ProductFactory.sharedCubeInnerGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Gold 링 Geometry 가져오기
   */
  static getRingGeometry(radius = 0.7, tube = 0.12) {
    if (!ProductFactory.sharedRingGeo) {
      ProductFactory.sharedRingGeo = new THREE.TorusGeometry(radius, tube, 32, 100);
    }
    return ProductFactory.sharedRingGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Gold 코어 Geometry 가져오기
   */
  static getCoreGeometry(radius = 0.25) {
    if (!ProductFactory.sharedCoreGeo) {
      ProductFactory.sharedCoreGeo = new THREE.SphereGeometry(radius, 32, 32);
    }
    return ProductFactory.sharedCoreGeo;
  }

  /**
   * ✅ WebGL 최적화: Static Geometry 공유
   * Fallback Geometry 가져오기
   */
  static getFallbackGeometry(size = 0.9) {
    if (!ProductFactory.sharedFallbackGeo) {
      ProductFactory.sharedFallbackGeo = new THREE.BoxGeometry(size, size, size);
    }
    return ProductFactory.sharedFallbackGeo;
  }

  /**
   * 이벤트 상품 생성 (GiftBox3D 사용)
   * position.y는 진열대 상단(1.4m) + 상품 높이의 절반
   */
  createEventProduct(product, position) {
    if (typeof GiftBox3D === "undefined") {
      console.error("❌ [ProductFactory] GiftBox3D 클래스를 찾을 수 없습니다!");
      return null;
    }

    console.log(`      → [ProductFactory] 이벤트 상품 생성: "${product.name}"`);
    const giftBox = new GiftBox3D(null, {
      boxColor: 0x7b1113,
      ribbonColor: 0xffd700
    });
    const giftBoxGroup = giftBox.createModel();
    
    // GiftBox의 실제 높이 계산 (boxHeight 0.9 + lidHeight 0.3 = 1.2, 스케일 0.9 적용)
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2, 높이 1.2
    const giftBoxHeight = 1.2 * 0.9; // 1.08m (골드무제한 높이 1.2에 맞춤)
    const giftBoxHalfHeight = giftBoxHeight / 2; // 0.54m
    
    // 래퍼 그룹 생성 (상품의 바닥면이 진열대 상단에 닿도록 조정)
    const wrapperGroup = new THREE.Group();
    // 물리 법칙: GiftBox의 바닥면이 그룹의 position.y에 오도록 중심을 올림
    // GiftBox 중심을 giftBoxHalfHeight만큼 위로 올려서 바닥면이 position.y에 오도록 함
    giftBoxGroup.position.y = giftBoxHalfHeight; // 상자 중심을 위로 올림 (바닥면이 position.y에 붙음)
    giftBoxGroup.scale.set(0.9, 0.9, 0.9);
    wrapperGroup.add(giftBoxGroup);
    
    wrapperGroup.userData = wrapperGroup.userData || {};
    wrapperGroup.userData.productData = product;
    
    // 가격 라벨 추가 (이벤트 상품은 "무료" 또는 "이벤트" 표시)
    const label = this.createPriceLabel(product);
    label.position.set(0, giftBoxHeight + 0.2, 0); // 상자 상단 위
    wrapperGroup.add(label);
    
    // 그룹 위치 설정: position.y는 진열대 상단 또는 원형 다이 윗면
    // 물리 법칙: 상품의 바닥면이 진열대 상단에 닿도록 조정
    wrapperGroup.position.set(position.x, position.y, position.z);
    
    // ⚠️ 물리 법칙: 진열대와 평행하게 유지 (기울이지 않음)
    // lookAt() 제거 - 상품은 바닥과 평행해야 함
    wrapperGroup.rotation.set(0, 0, 0); // 완벽한 수평 유지
    
    this.scene.add(wrapperGroup);
    
    console.log(`      ✅ [ProductFactory] 선물 상자 추가됨: 위치 (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
    return wrapperGroup;
  }

  /**
   * 일반 상품 생성 (Standard, Premium, Gold)
   */
  createRegularProduct(product, position) {
    console.log(`      → [ProductFactory] 일반 상품 생성: "${product.name}"`);
    const normalized = product.name.toLowerCase().replace(/\s+/g, "");
    console.log(`         정규화된 이름: "${normalized}"`);
    
    let group = null;
    if (normalized === "standard") {
      group = this.createStandardCoin(product, position);
      console.log(`         ✨ Standard 코인 생성됨`);
    } else if (normalized === "premium") {
      group = this.createPremiumCube(product, position);
      console.log(`         ✨ Premium 큐브 생성됨`);
    } else if (normalized === "gold") {
      group = this.createGoldCrown(product, position);
      console.log(`         ✨ Gold 크라운 생성됨`);
    } else {
      group = this.createFallbackProduct(product, position);
      console.log(`         ✨ 기본 오브젝트 생성됨`);
    }

    if (!group) {
      console.error(`      ❌ [ProductFactory] 그룹 생성 실패!`);
      return null;
    }

    group.userData.productData = product;
    
    // ⚠️ 물리 법칙: 진열대와 평행하게 유지 (기울이지 않음)
    // lookAt() 제거 - 상품은 바닥과 평행해야 함
    group.rotation.set(0, 0, 0); // 완벽한 수평 유지
    
    this.scene.add(group);
    
    console.log(`      ✅ [ProductFactory] 씬에 추가됨: 위치 (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
    return group;
  }

  /**
   * Standard 상품 생성 (은색 코인 + 톱니바퀴 디테일)
   * position.y는 진열대 상단(1.4m) + 상품 높이의 절반
   */
  createStandardCoin(product, position) {
    const group = new THREE.Group();
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2 (반지름 0.6)
    const coinHeight = 0.25; // 코인 높이
    const coinRadius = 0.6; // 골드무제한과 동일한 크기 (0.7 → 0.6)
    
    // ✅ WebGL 최적화: 공유 Material 사용
    const coinMat = ProductFactory.getCoinMaterial();
    const coin = new THREE.Mesh(
      ProductFactory.getCoinGeometry(coinRadius, coinHeight),
      coinMat
    );
    coin.rotation.x = Math.PI / 2; // 옆으로 눕힘 (원기둥을 Z축 방향으로)
    // ⚠️ 물리 법칙: 회전 후 가장 낮은 면(Y = -coinRadius)이 Y=0에 닿도록 올림
    coin.position.y = coinRadius; // 1.2m (코인 밑면이 진열대 상단에 정확히 붙음)
    coin.castShadow = true;
    coin.receiveShadow = true;
    group.add(coin);

    // 옆면 톱니바퀴 디테일
    // ✅ WebGL 최적화: 공유 Material 사용
    const toothMat = ProductFactory.getToothMaterial();
    const toothCount = 24;
    const radius = 0.6; // 골드무제한과 동일한 크기 (0.7 → 0.6)
    const toothHeight = 0.15;
    const toothWidth = 0.08;
    
    for (let i = 0; i < toothCount; i++) {
      const angle = (i / toothCount) * Math.PI * 2;
      const tooth = new THREE.Mesh(
        ProductFactory.getToothGeometry(toothWidth, toothHeight),
        toothMat
      );
      tooth.position.set(
        Math.cos(angle) * radius,
        coinRadius, // 1.2m (코인과 같은 높이)
        Math.sin(angle) * radius
      );
      tooth.rotation.y = angle + Math.PI / 2;
      tooth.castShadow = true;
      group.add(tooth);
    }

    // 림 (테두리)
    // ✅ WebGL 최적화: 공유 Material 사용
    const rimMat = ProductFactory.getRimMaterial();
    const rim = new THREE.Mesh(
      ProductFactory.getRimGeometry(0.65, 0.08), // 골드무제한과 동일한 크기 (0.75 → 0.65)
      rimMat
    );
    rim.rotation.x = Math.PI / 2;
    rim.position.y = coinRadius; // 1.2m (코인과 같은 높이)
    group.add(rim);

    // 가격 라벨 (코인 위에 배치)
    const label = this.createPriceLabel(product);
    label.position.set(0, coinHeight / 2 + 0.9, 0);
    group.add(label);

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    group.userData.productData = product;
    this.standardCoins.push(group);
    return group;
  }

  /**
   * Premium 상품 생성 (테크 큐브: 네온 시안 와이어프레임)
   * position.y는 진열대 상단(1.4m) + 상품 높이의 절반
   */
  createPremiumCube(product, position) {
    const group = new THREE.Group();
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2
    const outerSize = 1.2; // 골드무제한과 동일한 크기 (1.4 → 1.2)
    const cubeHalfHeight = outerSize / 2; // 0.6
    
    // 외부 와이어프레임 (네온 시안)
    // ✅ WebGL 최적화: 공유 Material 사용
    const lineMat = ProductFactory.getCubeLineMaterial();
    const lines = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        ProductFactory.getCubeGeometry(outerSize)
      ),
      lineMat
    );
    // ⚠️ 물리 법칙: 큐브의 가장 낮은 면(Y = -cubeHalfHeight)이 Y=0에 닿도록 올림
    lines.position.y = cubeHalfHeight; // 0.8m (큐브 밑면이 진열대 상단에 정확히 붙음)
    group.add(lines);

    // ✅ WebGL 최적화: 공유 Material 사용
    const lineMatTransparent = ProductFactory.getCubeLineMaterialTransparent();
    const lines2 = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        ProductFactory.getCubeGeometry(outerSize * 0.98)
      ),
      lineMatTransparent
    );
    lines2.position.y = cubeHalfHeight; // 0.8m (큐브 밑면이 진열대 상단에 정확히 붙음)
    group.add(lines2);

    // 내부 큐브 (반대 방향으로 빠르게 회전)
    // ✅ WebGL 최적화: MeshPhysicalMaterial → MeshStandardMaterial 변경 및 공유 Material 사용
    const coreMat = ProductFactory.getCubeCoreMaterial();
    const inner = new THREE.Mesh(
      ProductFactory.getCubeInnerGeometry(1),
      coreMat
    );
    inner.position.set(0, cubeHalfHeight - 0.1, 0); // 큐브 중심에서 살짝 아래
    inner.castShadow = true;
    group.add(inner);

    // 가격 라벨 (큐브 위에 배치)
    const label = this.createPriceLabel(product);
    label.position.set(0, outerSize + 0.2, 0); // 큐브 상단 위
    group.add(label);

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    
    // 반대 방향 회전을 위한 속도 저장
    this.premiumCubes.push({ 
      group, 
      inner,
      outerRotation: 0,
      innerRotation: 0,
      offset: Math.random() * Math.PI 
    });
    group.userData.productData = product;
    return group;
  }

  /**
   * Gold 상품 생성 (자이로스코프: 3개의 교차하는 링 + 에너지 코어)
   * position.y는 진열대 상단(1.4m) + 상품 높이의 절반
   */
  createGoldCrown(product, position) {
    const group = new THREE.Group();
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2 (반지름 0.6)
    const ringRadius = 0.6; // 링 반지름 조금 줄임 (0.7 → 0.6, 가로폭/세로폭 1.4 → 1.2)
    const ringThickness = 0.12; // 링 두께
    const crownHalfHeight = ringRadius; // 0.6 (가장 낮은 부분이 -0.6, 가장 높은 부분이 +0.6)
    
    // 골드 재질
    // ✅ WebGL 최적화: MeshPhysicalMaterial → MeshStandardMaterial 변경 및 공유 Material 사용
    const goldMat = ProductFactory.getGoldMaterial();
    
    // 3개의 교차하는 Torus 링
    // ⚠️ 물리 법칙: 링의 가장 낮은 면(Y = -ringRadius)이 Y=0에 닿도록 올림
    // ✅ WebGL 최적화: 공유 Geometry 사용
    const ring1 = new THREE.Mesh(
      ProductFactory.getRingGeometry(ringRadius, ringThickness),
      goldMat
    );
    ring1.rotation.x = Math.PI / 2;
    ring1.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring1.castShadow = true;
    group.add(ring1);
    
    const ring2 = new THREE.Mesh(
      ProductFactory.getRingGeometry(ringRadius, ringThickness),
      goldMat
    );
    ring2.rotation.y = Math.PI / 2;
    ring2.rotation.z = Math.PI / 4;
    ring2.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring2.castShadow = true;
    group.add(ring2);
    
    const ring3 = new THREE.Mesh(
      ProductFactory.getRingGeometry(ringRadius, ringThickness),
      goldMat
    );
    ring3.rotation.x = Math.PI / 4;
    ring3.rotation.z = Math.PI / 2;
    ring3.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring3.castShadow = true;
    group.add(ring3);
    
    // 중앙 에너지 코어
    // ✅ WebGL 최적화: MeshPhysicalMaterial → MeshStandardMaterial 변경 및 공유 Material 사용
    const coreMat = ProductFactory.getGoldCoreMaterial();
    const core = new THREE.Mesh(
      ProductFactory.getCoreGeometry(0.25),
      coreMat
    );
    core.position.y = ringRadius; // 0.7m (링과 같은 높이)
    core.castShadow = true;
    group.add(core);
    
    // 파티클 효과
    const particleGeo = new THREE.BufferGeometry();
    const positions = [];
    for (let i = 0; i < 50; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const radius = 0.3 + Math.random() * 0.3;
      positions.push(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi) + ringRadius, // 0.7m (링 중심 높이)
        radius * Math.sin(phi) * Math.sin(theta)
      );
    }
    particleGeo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3)
    );
    // ✅ WebGL 최적화: 공유 Material 사용
    const particleMat = ProductFactory.getGoldParticleMaterial();
    const particles = new THREE.Points(
      particleGeo,
      particleMat
    );
    group.add(particles);

    // 가격 라벨 (크라운 위에 배치)
    const label = this.createPriceLabel(product);
    label.position.set(0, ringRadius * 2 + 0.2, 0); // 크라운 상단 위
    group.add(label);

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    this.goldCrowns.push({ group, ring1, ring2, ring3, core, particles });
    group.userData.productData = product;
    return group;
  }

  /**
   * 기본 상품 생성 (Fallback)
   */
  createFallbackProduct(product, position) {
    const group = new THREE.Group();
    // ✅ WebGL 최적화: 공유 Material 및 Geometry 사용
    const geometry = ProductFactory.getFallbackGeometry(0.9);
    const material = ProductFactory.getFallbackMaterial();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    group.add(mesh);
    group.position.copy(position);

    const label = this.createPriceLabel(product);
    label.position.set(position.x, 1.5, position.z);
    group.add(label);

    group.userData.productData = product;
    return group;
  }

  /**
   * 가격 라벨 생성
   */
  createPriceLabel(product) {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "rgba(0,0,0,0.7)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = "bold 28px 'Pretendard'";
    ctx.fillStyle = "#fff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    
    // 실제 상품 데이터에서 가격 가져오기 (하드코딩 제거)
    let priceText = "FREE";
    
    if (product) {
      // 이벤트 상품 여부 확인 (우선순위: type 확인)
      const isEventType = product.type === 'event' || product.type === 'event_period';
      const isFreePrice = product.price === 0 || product.price === null || product.price === undefined;
      
      if (isEventType) {
        // 이벤트 상품: "EVENT"로 명확하게 표시
        priceText = "EVENT";
      } else if (isFreePrice) {
        // 무료 상품 (이벤트가 아닌 경우)
        priceText = "FREE";
      } else {
        // 유료 상품: 실제 가격 표시
        priceText = `${Number(product.price).toLocaleString('ko-KR')}원`;
      }
    } else {
      console.warn("⚠️ [ProductFactory] 상품 정보가 없습니다:", product);
      priceText = "N/A";
    }
    
    ctx.fillText(priceText, canvas.width / 2, canvas.height / 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    
    const spriteMat = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(1.5, 0.75, 1);
    
    return sprite;
  }

  /**
   * 상품 애니메이션 업데이트
   */
  updateProductAnimations() {
    // Standard Coin 회전
    this.standardCoins.forEach(group => {
      if (group && group.rotation) {
        group.rotation.y += 0.01;
      }
    });

    // Premium 큐브 회전
    this.premiumCubes.forEach(cube => {
      cube.outerRotation += 0.01;
      cube.innerRotation -= 0.02; // 반대 방향, 더 빠름
      if (cube.group) {
        cube.group.rotation.y = cube.outerRotation + cube.offset;
      }
      if (cube.inner) {
        cube.inner.rotation.y = cube.innerRotation;
        cube.inner.rotation.x = cube.innerRotation * 0.5;
      }
    });

    // Gold 자이로스코프 회전
    this.goldCrowns.forEach(crown => {
      if (crown.group) {
        crown.group.rotation.y += 0.002; // 전체 그룹 회전 (느리게)
      }
      if (crown.ring1) {
        crown.ring1.rotation.y += 0.01;
        crown.ring1.rotation.z += 0.005;
      }
      if (crown.ring2) {
        crown.ring2.rotation.x += 0.015;
        crown.ring2.rotation.z += 0.01;
      }
      if (crown.ring3) {
        crown.ring3.rotation.x += 0.012;
        crown.ring3.rotation.y += 0.006;
      }
      if (crown.core) {
        crown.core.rotation.x += 0.02;
        crown.core.rotation.y += 0.02;
      }
      if (crown.particles) {
        crown.particles.rotation.y += 0.02;
      }
    });
  }

  /**
   * Pedestal (진열대) 생성
   * @param {Object|THREE.Vector3} position - 위치 (x, y, z 또는 {x, y, z})
   * @returns {THREE.Group} 진열대 그룹
   */
  createPedestal(position) {
    console.log(`      → [ProductFactory] Pedestal 생성`);
    
    // Pedestal3D 클래스 확인
    if (typeof Pedestal3D === 'undefined' && typeof window.Pedestal3D === 'undefined') {
      console.error('      ❌ [ProductFactory] Pedestal3D 클래스를 찾을 수 없습니다.');
      return null;
    }
    
    // 위치가 없으면 기본값 (0,0,0)
    const pos = position || { x: 0, y: 0, z: 0 };
    
    // 전역 클래스 window.Pedestal3D 사용
    const Pedestal3DClass = Pedestal3D || window.Pedestal3D;
    const pedestal = new Pedestal3DClass(pos);
    
    if (!pedestal || !pedestal.group) {
      console.error('      ❌ [ProductFactory] Pedestal 그룹 생성 실패!');
      return null;
    }
    
    console.log(`      ✅ [ProductFactory] Pedestal 생성 완료: 위치 (${pos.x}, ${pos.y}, ${pos.z})`);
    return pedestal.group;
  }

  /**
   * 3D TV 상품 생성 (GLTFLoader 사용)
   * @param {Object} product - 상품 데이터
   * @param {THREE.Vector3|Object} position - 위치
   * @param {string} modelPath - 모델 파일 경로 (선택적)
   * @returns {THREE.Group} TV 모델 그룹
   */
  createTV3D(product, position, modelPath = null) {
    console.log(`      → [ProductFactory] 3D TV 생성: "${product?.name || '3D TV'}"`);
    
    // TV3D 클래스 확인
    if (typeof TV3D === 'undefined' && typeof window.TV3D === 'undefined') {
      console.error('      ❌ [ProductFactory] TV3D 클래스를 찾을 수 없습니다.');
      return this.createFallbackProduct(product, position);
    }
    
    const TV3DClass = TV3D || window.TV3D;
    
    // 위치 변환
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );
    
    // TV 모델 생성
    const group = TV3DClass.createModel(product, pos, modelPath);
    
    if (!group) {
      console.error('      ❌ [ProductFactory] 3D TV 그룹 생성 실패!');
      return this.createFallbackProduct(product, pos);
    }
    
    // 씬에 추가
    this.scene.add(group);
    
    console.log(`      ✅ [ProductFactory] 3D TV 추가됨: 위치 (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`);
    return group;
  }

  /**
   * Neon Ring 상품 생성
   * @param {Object} product - 상품 데이터
   * @param {THREE.Vector3} position - 위치
   * @returns {THREE.Group} 네온 링 그룹
   */
  createNeonRing(product, position) {
    console.log(`      → [ProductFactory] Neon Ring 생성: "${product.name || 'Neon Ring'}"`);
    
    // NeonRing 클래스 확인
    if (typeof NeonRing === 'undefined' && typeof window.NeonRing === 'undefined') {
      console.error('      ❌ [ProductFactory] NeonRing 클래스를 찾을 수 없습니다.');
      return null;
    }
    
    const NeonRingClass = NeonRing || window.NeonRing;
    
    // 네온 링 모델 생성
    const group = NeonRingClass.createModel(product, position);
    
    if (!group) {
      console.error('      ❌ [ProductFactory] Neon Ring 그룹 생성 실패!');
      return null;
    }
    
    // 씬에 추가
    this.scene.add(group);
    
    console.log(`      ✅ [ProductFactory] Neon Ring 추가됨: 위치 (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
    return group;
  }

  /**
   * LuxeDisplay3D 상품 생성 (순수 Three.js 구현)
   * @param {Object} product - 상품 데이터
   * @param {THREE.Vector3|Object} position - 위치
   * @returns {THREE.Group} 모델 그룹
   */
  createLuxeDisplay3D(product, position) {
    console.log(`      → [ProductFactory] LuxeDisplay3D 생성: "${product?.name || 'LuxeDisplay3D'}"`);
    
    // LuxeDisplay3D 클래스 확인
    if (typeof LuxeDisplay3D === 'undefined' && typeof window.LuxeDisplay3D === 'undefined') {
      console.error('      ❌ [ProductFactory] LuxeDisplay3D 클래스를 찾을 수 없습니다.');
      return null;
    }
    
    const LuxeDisplay3DClass = LuxeDisplay3D || window.LuxeDisplay3D;
    
    // 위치 변환
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );
    
    try {
      // 모델 생성 (동기)
      const group = LuxeDisplay3DClass.createModel(product, pos);
      
      if (!group) {
        console.error('      ❌ [ProductFactory] LuxeDisplay3D 그룹 생성 실패!');
        return null;
      }
      
      // 씬에 추가
      this.scene.add(group);
      
      console.log(`      ✅ [ProductFactory] LuxeDisplay3D 추가됨: 위치 (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`);
      return group;
      
    } catch (error) {
      console.error('      ❌ [ProductFactory] LuxeDisplay3D 생성 중 오류:', error);
      return null;
    }
  }

  /**
   * 모든 상품 메시 배열 반환
   */
  getAllMeshes() {
    const meshes = [];
    this.standardCoins.forEach(coin => meshes.push(coin));
    this.premiumCubes.forEach(cube => meshes.push(cube.group));
    this.goldCrowns.forEach(crown => meshes.push(crown.group));
    return meshes;
  }
}

// 전역 객체로 노출
window.ProductFactory = ProductFactory;
console.log("✅ [ProductFactory] 전역 객체로 노출 완료:", typeof window.ProductFactory);

