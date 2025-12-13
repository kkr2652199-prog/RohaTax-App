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
    
    // GiftBox의 실제 높이 계산 (boxHeight 0.9 + lidHeight 0.3 = 1.2, 유료 상품과 동일한 높이)
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2, 높이 1.2
    const giftBoxHeight = 1.2; // 1.2m (유료 상품과 동일한 높이)
    const giftBoxHalfHeight = giftBoxHeight / 2; // 0.6m
    
    // 래퍼 그룹 생성 (상품의 바닥면이 진열대 상단에 닿도록 조정)
    const wrapperGroup = new THREE.Group();
    // 물리 법칙: GiftBox의 바닥면이 그룹의 position.y에 오도록 중심을 올림
    // GiftBox 중심을 giftBoxHalfHeight만큼 위로 올려서 바닥면이 position.y에 오도록 함
    giftBoxGroup.position.y = giftBoxHalfHeight; // 상자 중심을 위로 올림 (바닥면이 position.y에 붙음)
    giftBoxGroup.scale.set(1.0, 1.0, 1.0); // 스케일 1.0으로 변경하여 유료 상품과 동일한 높이 확보
    wrapperGroup.add(giftBoxGroup);
    
    wrapperGroup.userData = wrapperGroup.userData || {};
    wrapperGroup.userData.productData = product;
    
    // 그룹 위치 설정: position.y는 진열대 상단 또는 원형 다이 윗면
    // 물리 법칙: 상품의 바닥면이 진열대 상단에 닿도록 조정
    wrapperGroup.position.set(position.x, position.y, position.z);
    
    // 가격 라벨 추가 (3D 홀로그램 콘솔) - Scene에 직접 추가 (회전 분리)
    // createPriceLabel 내부에서 scene.add()를 수행하므로 여기서는 호출만
    this.createPriceLabel(product, position);
    
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

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    
    // 가격 라벨 (3D 홀로그램 콘솔) - Scene에 직접 추가 (회전 분리)
    // createPriceLabel 내부에서 scene.add()를 수행하므로 여기서는 호출만
    this.createPriceLabel(product, position);
    
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

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    
    // 가격 라벨 (3D 홀로그램 콘솔) - Scene에 직접 추가 (회전 분리)
    // createPriceLabel 내부에서 scene.add()를 수행하므로 여기서는 호출만
    this.createPriceLabel(product, position);
    
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

    // 그룹 위치 설정: position.y는 진열대 상단(1.4m) + 상품 높이의 절반
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
    group.position.set(position.x, position.y, position.z);
    
    // 가격 라벨 (3D 홀로그램 콘솔) - Scene에 직접 추가 (회전 분리)
    // createPriceLabel 내부에서 scene.add()를 수행하므로 여기서는 호출만
    this.createPriceLabel(product, position);
    
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

    // ✅ 3D 홀로그램 콘솔 생성 (상품 앞쪽 하단에 배치) - Scene에 직접 추가 (회전 분리)
    // createPriceLabel 내부에서 scene.add()를 수행하므로 여기서는 호출만
    this.createPriceLabel(product, position);

    group.userData.productData = product;
    return group;
  }

  /**
   * 가격 라벨 생성 (Real 3D Mesh - CanvasTexture 기반)
   * @param {Object} product - 상품 데이터
   * @param {Object|THREE.Vector3} position - 상품의 월드 좌표 위치
   */
  createPriceLabel(product, position) {
    // ✅ MarketingCopy 모듈 사용 (CanvasTexture 생성)
    if (typeof window.MarketingCopy === 'undefined' && typeof MarketingCopy === 'undefined') {
      console.error('❌ [ProductFactory] MarketingCopy 모듈을 찾을 수 없습니다.');
      return null;
    }
    
    const MarketingCopyClass = window.MarketingCopy || MarketingCopy;
    
    // ✅ CanvasTexture 생성
    let texture;
    try {
      texture = MarketingCopyClass.getMenuTexture(product);
    } catch (error) {
      console.error('❌ [ProductFactory] CanvasTexture 생성 실패:', error);
      return null;
    }
    
    // ✅ 텍스처 설정 초기화 (기본값)
    texture.center.set(0, 0);     // 기본값
    texture.repeat.set(1, 1);     // 기본값
    texture.rotation = 0;         // 기본값
    texture.flipY = true;         // Three.js는 Canvas Y축과 반대이므로 true가 정석
    
    // ✅ 텍스처 필터링 최상급 설정 (4K 해상도 최적화)
    texture.minFilter = THREE.LinearMipMapLinearFilter; // 최상급 필터링
    texture.magFilter = THREE.LinearFilter;             // 확대 시 선명도 유지
    texture.anisotropy = 16;                            // 기울여서 봐도 선명하게 (최대값)
    
    // ✅ BoxGeometry 생성 (가로 1.5m, 세로 1.0m, 두께 0.1m) - 4K 해상도(1024x700) 비율에 맞게 조정
    const geometry = new THREE.BoxGeometry(1.5, 1.0, 0.1);
    
    // ✅ 재질 배열 생성 (BoxGeometry: [right, left, top, bottom, front, back])
    const sideMaterial = new THREE.MeshStandardMaterial({
      color: 0x333333, // 다크 메탈
      roughness: 0.4,
      metalness: 0.7
    });
    
    // 앞면(Index 4)에만 텍스처 적용 (발광 효과)
    const frontMaterial = new THREE.MeshStandardMaterial({
      map: texture,
      transparent: true,
      opacity: 1.0,
      side: THREE.FrontSide,
      roughness: 0.2,        // 매끈한 유리 느낌
      metalness: 0.5,         // 약간의 금속성
      emissive: 0xffffff,     // 발광 색상 (흰색)
      emissiveMap: texture,   // 텍스처 자체가 빛나게 함
      emissiveIntensity: 0.5  // 은은하게 스스로 빛남
    });
    
    // 재질 배열: [오른쪽, 왼쪽, 위, 아래, 앞, 뒤]
    const materials = [
      sideMaterial, // 0: 오른쪽
      sideMaterial, // 1: 왼쪽
      sideMaterial, // 2: 위
      sideMaterial, // 3: 아래
      frontMaterial, // 4: 앞면 (텍스처)
      sideMaterial   // 5: 뒤
    ];
    
    // ✅ Mesh 생성 (재질 배열 사용)
    const menuMesh = new THREE.Mesh(geometry, materials);
    
    // ✅ 월드 좌표로 위치 설정 (상품 앞쪽 하단에 배치)
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );
    
    // ✅ 무료 상품(이벤트) 메뉴판 높이를 골드 상품과 동일하게 조정
    const productType = (product?.type || '').trim().toLowerCase();
    const isEventType = productType === 'event' || productType === 'event_period';
    const labelYOffset = isEventType ? -0.4 : -1.0; // 무료 상품은 -0.4, 유료 상품은 -1.0
    
    // ✅ 천장 방향으로 조금 올림 (Y축 +0.3)
    // ✅ 유리 장식장(LuxeDisplay3D) 방향으로 조금 이동 (Z축 -0.5)
    menuMesh.position.set(pos.x, pos.y + labelYOffset + 0.3, pos.z + 1.5);
    
    // ✅ 사용자가 내려다보기 편하게 기울임 (물리적 회전)
    menuMesh.rotation.x = -0.5;      // 보기 편한 각도 기울기
    menuMesh.rotation.y = 0;         // Y축 회전 없음
    menuMesh.rotation.z = 0;         // 일단 0으로 두고, 결과 보고 뒤집혔으면 그때 돌린다
    
    // ✅ 클릭 감지용 userData 설정
    menuMesh.userData.isMenu = true;
    menuMesh.userData.isLabel = true;
    menuMesh.userData.isPriceLabel = true;
    menuMesh.userData.productData = product;
    
    // ✅ 버튼 영역 UV 좌표 저장 (클릭 감지용)
    // Canvas 크기: 512x300, 버튼 영역: 하단 20% (y: 240-290)
    menuMesh.userData.buttonUVRect = {
      x: 0.05,      // 좌측 여백 5%
      y: 0.8,       // 하단 20% 시작 (240/300)
      width: 0.9,   // 너비 90%
      height: 0.167 // 높이 16.7% (50/300)
    };
    
    // ✅ Scene에 직접 추가 (회전하는 그룹에서 분리)
    if (this.scene) {
      this.scene.add(menuMesh);
    }
    
    console.log('✅ [ProductFactory] Real 3D Mesh 메뉴판 생성 완료:', product?.name || 'Unknown');
    
    return menuMesh;
  }
  
  /**
   * 가격 라벨 Sprite 생성 (Fallback)
   */
  _createPriceLabelSprite(product, cardContent) {
    const canvas = document.createElement("canvas");
    canvas.width = 400;
    canvas.height = 200;
    const ctx = canvas.getContext("2d");
    
    // 배경
    ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
    const radius = 20;
    ctx.beginPath();
    ctx.moveTo(radius, 0);
    ctx.lineTo(canvas.width - radius, 0);
    ctx.quadraticCurveTo(canvas.width, 0, canvas.width, radius);
    ctx.lineTo(canvas.width, canvas.height - radius);
    ctx.quadraticCurveTo(canvas.width, canvas.height, canvas.width - radius, canvas.height);
    ctx.lineTo(radius, canvas.height);
    ctx.quadraticCurveTo(0, canvas.height, 0, canvas.height - radius);
    ctx.lineTo(0, radius);
    ctx.quadraticCurveTo(0, 0, radius, 0);
    ctx.closePath();
    ctx.fill();
    
    // 테두리
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // 텍스트 렌더링 (간단한 버전)
    ctx.fillStyle = "#ffd700";
    ctx.font = "700 24px 'Pretendard', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(cardContent.title, canvas.width / 2, 40);
    
    ctx.fillStyle = "#c0c0c0";
    ctx.font = "500 18px 'Pretendard', sans-serif";
    ctx.fillText(cardContent.sub, canvas.width / 2, 70);
    
    ctx.fillStyle = "#ffffff";
    ctx.font = "400 20px 'Pretendard', sans-serif";
    ctx.fillText(cardContent.detail.replace(/<[^>]*>/g, ''), canvas.width / 2, 110);
    
    ctx.fillStyle = "#ffffff";
    ctx.font = "700 36px 'Pretendard', sans-serif";
    ctx.fillText(cardContent.price.replace(/<[^>]*>/g, ''), canvas.width / 2, 160);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    
    const spriteMat = new THREE.SpriteMaterial({ 
      map: texture,
      transparent: true,
      opacity: 0.95
    });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(2.0, 1.0, 1);
    sprite.userData.isLabel = true;
    
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
    
    // MagicFire 불꽃 애니메이션
    if (this.magicFires) {
      this.magicFires.forEach(magicFire => {
        if (magicFire && typeof magicFire.animate === 'function') {
          magicFire.animate();
        }
      });
    }
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
   * MagicFire 가구 생성 (불꽃 효과가 있는 액자)
   */
  createMagicFire(position, options = {}) {
    if (typeof MagicFire === 'undefined' && typeof window.MagicFire === 'undefined') {
      console.error('      ❌ [ProductFactory] MagicFire 클래스를 찾을 수 없습니다.');
      return null;
    }
    
    const MagicFireClass = MagicFire || window.MagicFire;
    
    // 위치 변환
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );
    
    try {
      // MagicFire 인스턴스 생성
      const magicFire = new MagicFireClass(options);
      const group = magicFire.getGroup();
      
      if (!group) {
        console.error('      ❌ [ProductFactory] MagicFire 그룹 생성 실패!');
        return null;
      }
      
      // 위치 설정
      group.position.copy(pos);
      
      // 씬에 추가
      this.scene.add(group);
      
      // 애니메이션을 위한 참조 저장
      if (!this.magicFires) {
        this.magicFires = [];
      }
      this.magicFires.push(magicFire);
      
      console.log(`      ✅ [ProductFactory] MagicFire 추가됨: 위치 (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)})`);
      return group;
      
    } catch (error) {
      console.error('      ❌ [ProductFactory] MagicFire 생성 중 오류:', error);
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

