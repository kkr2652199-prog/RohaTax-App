/**
 * ProductFactory - 상품 3D 모델 생성 연동 모듈
 * Showroom.js의 상품 생성 기능을 담당
 */
class ProductFactory {
  constructor(scene) {
    this.scene = scene;
    this.standardCoins = [];
    this.premiumCubes = [];
    this.goldCrowns = [];
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
    
    // GiftBox의 실제 높이 계산 (boxHeight 1.8 + lidHeight 0.3 = 2.1, 스케일 0.9 적용)
    const giftBoxHeight = 2.1 * 0.9; // 1.89m
    const giftBoxHalfHeight = giftBoxHeight / 2; // 0.945m
    
    // 래퍼 그룹 생성 (상품의 바닥면이 진열대 상단에 닿도록 조정)
    const wrapperGroup = new THREE.Group();
    // GiftBox의 바닥면이 그룹의 position.y에 오도록 중심을 올림
    giftBoxGroup.position.y = 0; // 그룹 중심 (진열대에 정확히 붙음)
    giftBoxGroup.scale.set(0.9, 0.9, 0.9);
    wrapperGroup.add(giftBoxGroup);
    
    wrapperGroup.userData = wrapperGroup.userData || {};
    wrapperGroup.userData.productData = product;
    
    // 그룹 위치 설정: position.y는 진열대 상단(1.4m)
    // 상품의 바닥면이 진열대 상단에 닿도록 조정
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
    const coinHeight = 0.25; // 코인 높이
    const coinRadius = 1.2;
    
    const coinMat = new THREE.MeshStandardMaterial({
      color: 0xc0c0c0,
      metalness: 1.0,
      roughness: 0.2
    });
    const coin = new THREE.Mesh(
      new THREE.CylinderGeometry(coinRadius, coinRadius, coinHeight, 64),
      coinMat
    );
    coin.rotation.x = Math.PI / 2; // 옆으로 눕힘 (원기둥을 Z축 방향으로)
    // ⚠️ 물리 법칙: 회전 후 가장 낮은 면(Y = -coinRadius)이 Y=0에 닿도록 올림
    coin.position.y = coinRadius; // 1.2m (코인 밑면이 진열대 상단에 정확히 붙음)
    coin.castShadow = true;
    coin.receiveShadow = true;
    group.add(coin);

    // 옆면 톱니바퀴 디테일
    const toothMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      metalness: 0.8,
      roughness: 0.3
    });
    const toothCount = 24;
    const radius = 1.2;
    const toothHeight = 0.15;
    const toothWidth = 0.08;
    
    for (let i = 0; i < toothCount; i++) {
      const angle = (i / toothCount) * Math.PI * 2;
      const tooth = new THREE.Mesh(
        new THREE.BoxGeometry(toothWidth, toothHeight, toothWidth),
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
    const rimMat = new THREE.MeshStandardMaterial({
      color: 0xfffff0,
      metalness: 1,
      roughness: 0.1
    });
    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(1.25, 0.08, 16, 100),
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
    const outerSize = 1.6;
    const cubeHalfHeight = outerSize / 2; // 0.8
    
    // 외부 와이어프레임 (네온 시안)
    const lines = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        new THREE.BoxGeometry(outerSize, outerSize, outerSize)
      ),
      new THREE.LineBasicMaterial({ 
        color: 0x00FFFF // 네온 시안
      })
    );
    // ⚠️ 물리 법칙: 큐브의 가장 낮은 면(Y = -cubeHalfHeight)이 Y=0에 닿도록 올림
    lines.position.y = cubeHalfHeight; // 0.8m (큐브 밑면이 진열대 상단에 정확히 붙음)
    group.add(lines);
    
    const lines2 = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        new THREE.BoxGeometry(outerSize * 0.98, outerSize * 0.98, outerSize * 0.98)
      ),
      new THREE.LineBasicMaterial({ 
        color: 0x00FFFF, 
        transparent: true, 
        opacity: 0.5 
      })
    );
    lines2.position.y = cubeHalfHeight; // 0.8m (큐브 밑면이 진열대 상단에 정확히 붙음)
    group.add(lines2);

    // 내부 큐브 (반대 방향으로 빠르게 회전)
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x00FFFF,
      transmission: 0.8,
      transparent: true,
      roughness: 0.1,
      metalness: 0.8,
      emissive: 0x004444,
      emissiveIntensity: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05
    });
    const inner = new THREE.Mesh(
      new THREE.BoxGeometry(1, 1, 1),
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
    const ringRadius = 0.7; // 링 반지름
    const ringThickness = 0.12; // 링 두께
    const crownHalfHeight = ringRadius; // 0.7 (가장 낮은 부분이 -0.7, 가장 높은 부분이 +0.7)
    
    // 골드 재질
    const goldMat = new THREE.MeshPhysicalMaterial({
      color: 0xFFD700,
      metalness: 1.0,
      roughness: 0.1,
      emissive: 0x332200,
      emissiveIntensity: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05
    });
    
    // 3개의 교차하는 Torus 링
    // ⚠️ 물리 법칙: 링의 가장 낮은 면(Y = -ringRadius)이 Y=0에 닿도록 올림
    const ring1 = new THREE.Mesh(
      new THREE.TorusGeometry(ringRadius, ringThickness, 32, 100),
      goldMat
    );
    ring1.rotation.x = Math.PI / 2;
    ring1.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring1.castShadow = true;
    group.add(ring1);
    
    const ring2 = new THREE.Mesh(
      new THREE.TorusGeometry(ringRadius, ringThickness, 32, 100),
      goldMat
    );
    ring2.rotation.y = Math.PI / 2;
    ring2.rotation.z = Math.PI / 4;
    ring2.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring2.castShadow = true;
    group.add(ring2);
    
    const ring3 = new THREE.Mesh(
      new THREE.TorusGeometry(ringRadius, ringThickness, 32, 100),
      goldMat
    );
    ring3.rotation.x = Math.PI / 4;
    ring3.rotation.z = Math.PI / 2;
    ring3.position.y = ringRadius; // 0.7m (링 밑면이 진열대 상단에 정확히 붙음)
    ring3.castShadow = true;
    group.add(ring3);
    
    // 중앙 에너지 코어
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0xFFD700,
      metalness: 0.8,
      roughness: 0.1,
      emissive: 0xFFAA00,
      emissiveIntensity: 0.8,
      transparent: true,
      opacity: 0.9
    });
    const core = new THREE.Mesh(
      new THREE.SphereGeometry(0.25, 32, 32),
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
    const particles = new THREE.Points(
      particleGeo,
      new THREE.PointsMaterial({ 
        color: 0xFFD700, 
        size: 0.05,
        transparent: true,
        opacity: 0.8
      })
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
    const geometry = new THREE.BoxGeometry(0.9, 0.9, 0.9);
    const material = new THREE.MeshStandardMaterial({ 
      color: 0x808080, 
      roughness: 0.4 
    });
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
    
    const priceText = product.price === 0 
      ? "무료" 
      : `${product.price.toLocaleString()}원`;
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
      if (crown.ring1) crown.ring1.rotation.y += 0.01;
      if (crown.ring2) crown.ring2.rotation.x += 0.015;
      if (crown.ring3) crown.ring3.rotation.z += 0.012;
      if (crown.core) {
        crown.core.rotation.x += 0.02;
        crown.core.rotation.y += 0.02;
      }
    });
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

