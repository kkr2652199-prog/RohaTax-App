/* eslint-env browser */
/* global THREE */
/**
 * Crown3D - Imperial Crown 3D 모델 (React 컴포넌트 기반 코드를 Three.js로 변환)
 * BaseCirclet, Diamonds, FleurDeLisSpikes, VelvetCap, CrossArches 포함
 *
 * @class Crown3D
 * @description ProductFactory에서 사용하는 3D 왕관 가구 클래스
 */
class Crown3D {
  /**
   * Static Material 공유 (WebGL 텍스처 유닛 최적화)
   */
  static sharedGoldMat = null;
  static sharedVelvetMat = null;
  static sharedPearlMat = null;
  static sharedDiamondMat = null;
  static sharedSapphireMat = null;
  static sharedRubyMat = null;
  static sharedEmeraldMat = null;

  /**
   * 골드 Material 가져오기
   */
  static getGoldMaterial() {
    if (!Crown3D.sharedGoldMat) {
      Crown3D.sharedGoldMat = new THREE.MeshStandardMaterial({
        color: 0xffd700, // #FFD700
        metalness: 1.0,
        roughness: 0.15,
        envMapIntensity: 1.5,
        side: THREE.DoubleSide,
      });
    }
    return Crown3D.sharedGoldMat;
  }

  /**
   * 벨벳 Material 가져오기
   */
  static getVelvetMaterial() {
    if (!Crown3D.sharedVelvetMat) {
      Crown3D.sharedVelvetMat = new THREE.MeshPhysicalMaterial({
        color: 0x3d0000, // Deepest blood red
        roughness: 1.0,
        metalness: 0.1,
        sheen: 1.2,
        sheenRoughness: 0.5,
        sheenColor: new THREE.Color('#ff1a1a'), // Red sheen highlights (원본과 동일)
        clearcoat: 0.0,
        side: THREE.DoubleSide,
      });
    }
    return Crown3D.sharedVelvetMat;
  }

  /**
   * 진주 Material 가져오기
   */
  static getPearlMaterial() {
    if (!Crown3D.sharedPearlMat) {
      Crown3D.sharedPearlMat = new THREE.MeshStandardMaterial({
        color: 0xfffff0, // Cream white
        roughness: 0.3,
        metalness: 0.1,
      });
    }
    return Crown3D.sharedPearlMat;
  }

  /**
   * 다이아몬드 Material 가져오기
   */
  static getDiamondMaterial() {
    if (!Crown3D.sharedDiamondMat) {
      Crown3D.sharedDiamondMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        metalness: 0.0,
        roughness: 0.0,
        transmission: 1.0,
        thickness: 0.8,
        ior: 2.4,
        dispersion: 6,
        clearcoat: 1.0,
        clearcoatRoughness: 0.0,
        envMapIntensity: 2.0,
        attenuationColor: new THREE.Color(0xe6e6fa),
        attenuationDistance: 1.0,
      });
    }
    return Crown3D.sharedDiamondMat;
  }

  /**
   * 사파이어 Material 가져오기
   */
  static getSapphireMaterial() {
    if (!Crown3D.sharedSapphireMat) {
      Crown3D.sharedSapphireMat = new THREE.MeshPhysicalMaterial({
        color: 0x0f2c6b, // #0f2c6b
        metalness: 0.1,
        roughness: 0.05,
        transmission: 0.6,
        thickness: 2,
        ior: 1.77,
      });
    }
    return Crown3D.sharedSapphireMat;
  }

  /**
   * 루비 Material 가져오기
   */
  static getRubyMaterial() {
    if (!Crown3D.sharedRubyMat) {
      Crown3D.sharedRubyMat = new THREE.MeshPhysicalMaterial({
        color: 0x8a0303, // #8a0303
        metalness: 0.1,
        roughness: 0.05,
        transmission: 0.5,
        thickness: 2,
        ior: 1.76,
      });
    }
    return Crown3D.sharedRubyMat;
  }

  /**
   * 에메랄드 Material 가져오기
   */
  static getEmeraldMaterial() {
    if (!Crown3D.sharedEmeraldMat) {
      Crown3D.sharedEmeraldMat = new THREE.MeshPhysicalMaterial({
        color: 0x034b03, // #034b03
        metalness: 0.1,
        roughness: 0.05,
        transmission: 0.5,
        thickness: 2,
        ior: 1.57,
      });
    }
    return Crown3D.sharedEmeraldMat;
  }

  /**
   * BaseCirclet 생성 (원형 밴드, 상단/하단 림, 8개의 장식 패널)
   */
  static createBaseCirclet() {
    const group = new THREE.Group();

    // Main Band - Cylinder
    const mainBand = new THREE.Mesh(
      new THREE.CylinderGeometry(2.5, 2.5, 1.2, 64),
      Crown3D.getGoldMaterial()
    );
    mainBand.castShadow = true;
    mainBand.receiveShadow = true;
    group.add(mainBand);

    // Top Rim
    const topRim = new THREE.Mesh(
      new THREE.CylinderGeometry(2.6, 2.6, 0.15, 64),
      Crown3D.getGoldMaterial()
    );
    topRim.position.y = 0.65;
    group.add(topRim);

    // Top Rim Detail (Torus)
    const topRimDetail = new THREE.Mesh(
      new THREE.TorusGeometry(2.6, 0.05, 16, 64),
      Crown3D.getGoldMaterial()
    );
    topRimDetail.position.y = 0.65;
    topRimDetail.rotation.x = Math.PI / 2;
    group.add(topRimDetail);

    // Bottom Rim
    const bottomRim = new THREE.Mesh(
      new THREE.CylinderGeometry(2.6, 2.6, 0.15, 64),
      Crown3D.getGoldMaterial()
    );
    bottomRim.position.y = -0.65;
    group.add(bottomRim);

    // Bottom Rim Detail (Torus)
    const bottomRimDetail = new THREE.Mesh(
      new THREE.TorusGeometry(2.6, 0.05, 16, 64),
      Crown3D.getGoldMaterial()
    );
    bottomRimDetail.position.y = -0.65;
    bottomRimDetail.rotation.x = Math.PI / 2;
    group.add(bottomRimDetail);

    // Decorative Panels on Band (8개)
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const x = Math.cos(angle) * 2.52;
      const z = Math.sin(angle) * 2.52;

      const panelGroup = new THREE.Group();
      panelGroup.position.set(x, 0, z);
      panelGroup.rotation.y = -angle;

      // Square Gem Frame (Bezel)
      const bezel = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.55, 0.55),
        Crown3D.getGoldMaterial()
      );
      panelGroup.add(bezel);

      // Main Gem - OVAL CUT (Ruby or Emerald)
      const gemGroup = new THREE.Group();
      gemGroup.position.set(0.1, 0, 0);

      const gemMaterial =
        i % 2 === 0 ? Crown3D.getRubyMaterial() : Crown3D.getEmeraldMaterial();
      const gem = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.25, 0),
        gemMaterial
      );
      gem.scale.set(0.3, 1, 0.7);
      gemGroup.add(gem);

      // Gold Setting/Prongs (4개)
      const prongPositions = [
        [0, 0.2, 0.15],
        [0, -0.2, 0.15],
        [0, 0.2, -0.15],
        [0, -0.2, -0.15],
      ];
      const prongRotations = [
        [0.2, 0, 0],
        [-0.2, 0, 0],
        [0.2, 0, 0],
        [-0.2, 0, 0],
      ];

      for (let j = 0; j < 4; j++) {
        const prong = new THREE.Mesh(
          new THREE.CylinderGeometry(0.02, 0.02, 0.1, 8),
          Crown3D.getGoldMaterial()
        );
        prong.position.set(...prongPositions[j]);
        prong.rotation.set(...prongRotations[j]);
        gemGroup.add(prong);
      }

      panelGroup.add(gemGroup);

      // Small Diamond accents (4개)
      const diamondPositions = [
        [0.04, 0.42, 0.42],
        [0.04, -0.42, 0.42],
        [0.04, 0.42, -0.42],
        [0.04, -0.42, -0.42],
      ];

      for (let j = 0; j < 4; j++) {
        const diamond = new THREE.Mesh(
          new THREE.DodecahedronGeometry(0.06, 0),
          Crown3D.getDiamondMaterial()
        );
        diamond.position.set(...diamondPositions[j]);
        diamond.scale.set(1, 0.4, 1);
        panelGroup.add(diamond);
      }

      group.add(panelGroup);
    }

    return group;
  }

  /**
   * Diamonds 생성 (상단/하단에 64개씩)
   */
  static createDiamonds() {
    const group = new THREE.Group();

    // Top Row Diamonds (64개)
    for (let i = 0; i < 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const x = Math.cos(angle) * 2.61;
      const z = Math.sin(angle) * 2.61;

      const diamond = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.08, 0),
        Crown3D.getDiamondMaterial()
      );
      diamond.position.set(x, 0.65, z);
      diamond.scale.set(0.5, 0.5, 0.5);
      diamond.castShadow = true;
      group.add(diamond);
    }

    // Bottom Row Diamonds (64개)
    for (let i = 0; i < 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const x = Math.cos(angle) * 2.61;
      const z = Math.sin(angle) * 2.61;

      const diamond = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.08, 0),
        Crown3D.getDiamondMaterial()
      );
      diamond.position.set(x, -0.65, z);
      diamond.scale.set(0.5, 0.5, 0.5);
      diamond.castShadow = true;
      group.add(diamond);
    }

    return group;
  }

  /**
   * FleurDeLisSpikes 생성 (4개)
   */
  static createFleurDeLisSpikes() {
    const group = new THREE.Group();

    for (let i = 0; i < 4; i++) {
      const angle = Math.PI / 4 + (i / 4) * Math.PI * 2;
      const x = Math.cos(angle) * 2.55;
      const z = Math.sin(angle) * 2.55;

      const spikeGroup = new THREE.Group();
      spikeGroup.position.set(x, 0.7, z);
      spikeGroup.rotation.y = -angle;

      // Center Petal (CapsuleGeometry 대신 CylinderGeometry + SphereGeometry 조합)
      const centerPetalGroup = new THREE.Group();
      centerPetalGroup.position.set(0, 0.5, 0);
      centerPetalGroup.scale.set(1, 1, 0.5);

      // Cylinder body
      const centerCylinder = new THREE.Mesh(
        new THREE.CylinderGeometry(0.15, 0.15, 0.6, 8),
        Crown3D.getGoldMaterial()
      );
      centerCylinder.position.y = 0;
      centerPetalGroup.add(centerCylinder);

      // Top sphere
      const topSphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.15, 8, 8),
        Crown3D.getGoldMaterial()
      );
      topSphere.position.y = 0.3;
      centerPetalGroup.add(topSphere);

      // Bottom sphere
      const bottomSphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.15, 8, 8),
        Crown3D.getGoldMaterial()
      );
      bottomSphere.position.y = -0.3;
      centerPetalGroup.add(bottomSphere);

      spikeGroup.add(centerPetalGroup);

      // Center Diamond Jewel
      const centerDiamond = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.12, 0),
        Crown3D.getDiamondMaterial()
      );
      centerDiamond.position.set(0.12, 0.5, 0);
      centerDiamond.scale.set(0.6, 0.8, 0.6);
      spikeGroup.add(centerDiamond);

      // Side Scrolls (2개)
      const scroll1 = new THREE.Mesh(
        new THREE.TorusGeometry(0.15, 0.05, 8, 16, Math.PI * 1.5),
        Crown3D.getGoldMaterial()
      );
      scroll1.position.set(0, 0.3, 0.25);
      scroll1.rotation.set(0.5, 0, 0);
      spikeGroup.add(scroll1);

      const scroll2 = new THREE.Mesh(
        new THREE.TorusGeometry(0.15, 0.05, 8, 16, Math.PI * 1.5),
        Crown3D.getGoldMaterial()
      );
      scroll2.position.set(0, 0.3, -0.25);
      scroll2.rotation.set(-0.5, 0, 0);
      spikeGroup.add(scroll2);

      // Base connection
      const base = new THREE.Mesh(
        new THREE.CylinderGeometry(0.2, 0.25, 0.2, 8),
        Crown3D.getGoldMaterial()
      );
      base.position.set(0, 0.1, 0);
      spikeGroup.add(base);

      group.add(spikeGroup);
    }

    return group;
  }

  /**
   * VelvetCap 생성
   */
  static createVelvetCap() {
    const group = new THREE.Group();

    // Base Cylinder
    const baseCylinder = new THREE.Mesh(
      new THREE.CylinderGeometry(2.3, 2.3, 1.2, 64),
      Crown3D.getVelvetMaterial()
    );
    group.add(baseCylinder);

    // Puffy Top (4 Lobes)
    const topGroup = new THREE.Group();
    topGroup.position.y = 0.6;

    const lobeAngles = [45, 135, 225, 315];
    for (const deg of lobeAngles) {
      const lobeGroup = new THREE.Group();
      lobeGroup.rotation.y = THREE.MathUtils.degToRad(deg);

      const lobe = new THREE.Mesh(
        new THREE.SphereGeometry(1.1, 48, 32),
        Crown3D.getVelvetMaterial()
      );
      lobe.position.set(0.6, 0.1, 0);
      lobe.scale.set(1.1, 0.8, 1.1);
      lobeGroup.add(lobe);

      topGroup.add(lobeGroup);
    }

    // Central Filler Dome
    const centralDome = new THREE.Mesh(
      new THREE.SphereGeometry(1.35, 48, 32),
      Crown3D.getVelvetMaterial()
    );
    centralDome.position.set(0, 0.3, 0);
    centralDome.scale.set(1, 0.85, 1);
    topGroup.add(centralDome);

    // --- 신라시대 황관 스타일 상단 원형 면 장식 추가 (윗면 바닥에 붙이고 크기 확대) ---
    // Central Dome 상단 표면에 정확히 붙이기: topGroup.y (0.6) + centralDome.y (0.3) + (반지름 * scale.y)
    const domeTopSurface = 0.6 + 0.3 + 1.35 * 0.85; // 약 2.0475
    const topOrnamentGroup = new THREE.Group();
    topOrnamentGroup.position.y = domeTopSurface; // 윗면 바닥에 정확히 붙이기
    topOrnamentGroup.scale.set(1.5, 1.5, 1.5); // 전체 크기 1.5배 확대

    // 1. 중앙 대형 황금 원판 (왕의 권위 상징) - 크기 확대
    const centralGoldPlate = new THREE.Mesh(
      new THREE.CylinderGeometry(1.2, 1.2, 0.08, 64), // 0.8 -> 1.2, 높이 0.05 -> 0.08
      Crown3D.getGoldMaterial()
    );
    centralGoldPlate.rotation.x = Math.PI / 2; // 수평으로 눕히기
    centralGoldPlate.position.y = 0; // 윗면 바닥에 붙이기
    topOrnamentGroup.add(centralGoldPlate);

    // 2. 중앙 대형 루비 보석 (왕의 심장) - 크기 확대
    const centralRuby = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.4, 0), // 0.25 -> 0.4
      Crown3D.getRubyMaterial()
    );
    centralRuby.position.y = 0.08; // 원판 위에 위치
    centralRuby.rotation.set(Math.PI / 4, Math.PI / 4, 0);
    centralRuby.scale.set(1, 1.8, 1); // 1.5 -> 1.8
    topOrnamentGroup.add(centralRuby);

    // 3. 황금 원판 주변 복잡한 기하학적 패턴 (신라시대 스타일) - 크기 확대
    const patternRadius = 1.35; // 0.9 -> 1.35
    const patternCount = 16; // 12 -> 16 (더 화려하게)
    for (let i = 0; i < patternCount; i++) {
      const angle = (i / patternCount) * Math.PI * 2;
      const x = Math.cos(angle) * patternRadius;
      const z = Math.sin(angle) * patternRadius;

      // 황금 장식 스파이크 (신라시대 스타일) - 크기 확대
      const decorativeSpike = new THREE.Mesh(
        new THREE.ConeGeometry(0.1, 0.2, 8), // 0.06 -> 0.1, 0.12 -> 0.2
        Crown3D.getGoldMaterial()
      );
      decorativeSpike.position.set(x, 0.05, z); // 0.03 -> 0.05
      decorativeSpike.rotation.y = angle;
      topOrnamentGroup.add(decorativeSpike);

      // 작은 진주 장식 - 크기 확대
      const pearl = new THREE.Mesh(
        new THREE.SphereGeometry(0.08, 16, 16), // 0.05 -> 0.08
        Crown3D.getPearlMaterial()
      );
      pearl.position.set(x * 0.7, 0.08, z * 0.7); // 0.05 -> 0.08
      topOrnamentGroup.add(pearl);
    }

    // 4. 중간 원형 황금 테두리 (3개 층으로 확대) - 크기 확대
    for (let layer = 0; layer < 3; layer++) {
      const ringRadius = 0.75 + layer * 0.3; // 0.5 -> 0.75, 간격 0.2 -> 0.3
      const ringTorus = new THREE.Mesh(
        new THREE.TorusGeometry(ringRadius, 0.05, 16, 64), // 0.03 -> 0.05
        Crown3D.getGoldMaterial()
      );
      ringTorus.position.y = 0.03 + layer * 0.015; // 0.02 -> 0.03
      ringTorus.rotation.x = Math.PI / 2;
      topOrnamentGroup.add(ringTorus);

      // 테두리 주변 작은 다이아몬드 (12개로 증가) - 크기 확대
      for (let j = 0; j < 12; j++) {
        const gemAngle = (j / 12) * Math.PI * 2;
        const gemX = Math.cos(gemAngle) * ringRadius;
        const gemZ = Math.sin(gemAngle) * ringRadius;

        const smallDiamond = new THREE.Mesh(
          new THREE.DodecahedronGeometry(0.06, 0), // 0.04 -> 0.06
          Crown3D.getDiamondMaterial()
        );
        smallDiamond.position.set(gemX, 0.06 + layer * 0.015, gemZ); // 0.04 -> 0.06
        smallDiamond.scale.set(1, 1, 1); // 0.8 -> 1
        topOrnamentGroup.add(smallDiamond);
      }
    }

    // 5. 외곽 황금 장식 링 (신라시대 복잡한 패턴) - 크기 확대
    const outerRingRadius = 1.65; // 1.1 -> 1.65
    const outerRingCount = 24; // 16 -> 24 (더 화려하게)
    for (let i = 0; i < outerRingCount; i++) {
      const angle = (i / outerRingCount) * Math.PI * 2;
      const x = Math.cos(angle) * outerRingRadius;
      const z = Math.sin(angle) * outerRingRadius;

      // 교차 패턴 (신라시대 스타일)
      if (i % 2 === 0) {
        // 황금 장식 스파이크 - 크기 확대
        const outerSpike = new THREE.Mesh(
          new THREE.ConeGeometry(0.08, 0.15, 8), // 0.05 -> 0.08, 0.1 -> 0.15
          Crown3D.getGoldMaterial()
        );
        outerSpike.position.set(x, 0.04, z); // 0.02 -> 0.04
        outerSpike.rotation.y = angle;
        topOrnamentGroup.add(outerSpike);
      } else {
        // 사파이어/에메랄드 교차 배치 - 크기 확대
        const gemMaterial =
          i % 4 === 1
            ? Crown3D.getSapphireMaterial()
            : Crown3D.getEmeraldMaterial();
        const outerGem = new THREE.Mesh(
          new THREE.DodecahedronGeometry(0.1, 0), // 0.06 -> 0.1
          gemMaterial
        );
        outerGem.position.set(x, 0.05, z); // 0.03 -> 0.05
        outerGem.scale.set(1, 1, 1); // 0.7 -> 1
        topOrnamentGroup.add(outerGem);
      }
    }

    // 6. 최상단 황금 별 장식 (왕의 상징) - 크기 확대 및 더 화려하게
    const topStarGroup = new THREE.Group();
    topStarGroup.position.y = 0.2; // 0.15 -> 0.2

    // 12각 별 만들기 (신라시대 스타일, 더 화려하게)
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2 - Math.PI / 2;
      const x = Math.cos(angle) * 0.25; // 0.15 -> 0.25
      const z = Math.sin(angle) * 0.25;

      const starPoint = new THREE.Mesh(
        new THREE.ConeGeometry(0.06, 0.25, 8), // 0.04 -> 0.06, 0.15 -> 0.25
        Crown3D.getGoldMaterial()
      );
      starPoint.position.set(x, 0, z);
      starPoint.rotation.y = angle;
      starPoint.rotation.x = -Math.PI / 6;
      topStarGroup.add(starPoint);
    }

    // 중앙 대형 다이아몬드 (왕의 정점) - 크기 확대
    const centerStarDiamond = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.15, 0), // 0.08 -> 0.15
      Crown3D.getDiamondMaterial()
    );
    centerStarDiamond.position.y = 0.15; // 0.1 -> 0.15
    centerStarDiamond.scale.set(1, 1.5, 1);
    topStarGroup.add(centerStarDiamond);

    // 7. 왕을 상징하는 추가 고급 장식 - 용 문양 (신라시대 스타일)
    const dragonOrnamentGroup = new THREE.Group();
    dragonOrnamentGroup.position.y = 0.12;

    // 용의 머리 (중앙 루비 주변)
    for (let i = 0; i < 4; i++) {
      const angle = (i / 4) * Math.PI * 2;
      const x = Math.cos(angle) * 0.5;
      const z = Math.sin(angle) * 0.5;

      // 용의 머리 (황금)
      const dragonHead = new THREE.Mesh(
        new THREE.ConeGeometry(0.08, 0.15, 8),
        Crown3D.getGoldMaterial()
      );
      dragonHead.position.set(x, 0, z);
      dragonHead.rotation.y = angle;
      dragonHead.rotation.x = -Math.PI / 4;
      dragonOrnamentGroup.add(dragonHead);

      // 용의 눈 (루비)
      const dragonEye = new THREE.Mesh(
        new THREE.SphereGeometry(0.04, 8, 8),
        Crown3D.getRubyMaterial()
      );
      dragonEye.position.set(x * 1.1, 0.05, z * 1.1);
      dragonOrnamentGroup.add(dragonEye);
    }

    topStarGroup.add(dragonOrnamentGroup);

    // 8. 왕관의 최상단 - 황금 십자가 (왕의 권위)
    const royalCross = new THREE.Group();
    royalCross.position.y = 0.35;

    // 십자가 수직선
    const verticalBar = new THREE.Mesh(
      new THREE.BoxGeometry(0.1, 0.4, 0.1),
      Crown3D.getGoldMaterial()
    );
    verticalBar.position.y = 0.2;
    royalCross.add(verticalBar);

    // 십자가 수평선
    const horizontalBar = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, 0.1, 0.1),
      Crown3D.getGoldMaterial()
    );
    horizontalBar.position.y = 0.3;
    royalCross.add(horizontalBar);

    // 십자가 중앙 보석
    const crossGem = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.08, 0),
      Crown3D.getDiamondMaterial()
    );
    crossGem.position.y = 0.3;
    royalCross.add(crossGem);

    topStarGroup.add(royalCross);
    topOrnamentGroup.add(topStarGroup);
    // --- 신라시대 황관 스타일 상단 원형 면 장식 추가 끝 ---

    group.add(topGroup);
    group.add(topOrnamentGroup); // 상단 장식 그룹 추가

    return group;
  }

  /**
   * SingleArch 생성 (진주 15개)
   */
  static createSingleArch() {
    const group = new THREE.Group();
    const arcRadius = 2.55;
    const numPearls = 15;

    // Gold Strap
    const strap = new THREE.Mesh(
      new THREE.TorusGeometry(arcRadius, 0.25, 16, 64, Math.PI),
      Crown3D.getGoldMaterial()
    );
    strap.scale.set(1, 0.85, 0.2);
    group.add(strap);

    // Gold Piping (Edges) - 원본과 동일하게 group으로 감싸기
    const pipingGroup = new THREE.Group();
    pipingGroup.scale.set(1, 0.85, 1);

    const piping1 = new THREE.Mesh(
      new THREE.TorusGeometry(arcRadius, 0.04, 8, 64, Math.PI),
      Crown3D.getGoldMaterial()
    );
    piping1.position.z = 0.15;
    pipingGroup.add(piping1);

    const piping2 = new THREE.Mesh(
      new THREE.TorusGeometry(arcRadius, 0.04, 8, 64, Math.PI),
      Crown3D.getGoldMaterial()
    );
    piping2.position.z = -0.15;
    pipingGroup.add(piping2);

    group.add(pipingGroup);

    // Pearls along the spine (15개)
    for (let i = 0; i < numPearls; i++) {
      const t = i / (numPearls - 1);
      const adjustedAngle = 0.2 + t * (Math.PI - 0.4);
      const x = Math.cos(adjustedAngle) * arcRadius;
      const y = Math.sin(adjustedAngle) * arcRadius * 0.85;

      const pearl = new THREE.Mesh(
        new THREE.SphereGeometry(0.09, 16, 16),
        Crown3D.getPearlMaterial()
      );
      pearl.position.set(x, y, 0);
      group.add(pearl);
    }

    return group;
  }

  /**
   * CrossArches 생성 (십자형 아치)
   */
  static createCrossArches() {
    const group = new THREE.Group();
    group.position.y = 0.5;
    group.rotation.y = Math.PI / 4;

    // Arch 1: Spans X axis
    const arch1 = Crown3D.createSingleArch();
    group.add(arch1);

    // Arch 2: Spans Z axis (Rotated 90 deg) - 원본과 동일하게 group으로 감싸기
    const arch2Group = new THREE.Group();
    arch2Group.rotation.y = Math.PI / 2;
    const arch2 = Crown3D.createSingleArch();
    arch2Group.add(arch2);
    group.add(arch2Group);

    // Central Intersection Ornament (Monde Base) - 왕을 상징하는 고급 장식
    const mondeGroup = new THREE.Group();
    mondeGroup.position.y = 2.55 * 0.85;

    // Base Cylinder (더 크고 화려하게)
    const mondeBase = new THREE.Mesh(
      new THREE.CylinderGeometry(0.45, 0.45, 0.2, 32),
      Crown3D.getGoldMaterial()
    );
    mondeGroup.add(mondeBase);

    // Decorative Ring (중간 장식)
    const mondeTorus = new THREE.Mesh(
      new THREE.TorusGeometry(0.25, 0.06, 16, 32),
      Crown3D.getGoldMaterial()
    );
    mondeTorus.position.y = 0.15;
    mondeTorus.rotation.x = Math.PI / 2;
    mondeGroup.add(mondeTorus);

    // 중앙 대형 루비 보석 (왕의 권위 상징)
    const centerRuby = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.35, 0),
      Crown3D.getRubyMaterial()
    );
    centerRuby.position.y = 0.25;
    centerRuby.rotation.set(Math.PI / 4, Math.PI / 4, 0);
    centerRuby.scale.set(1, 1.3, 1);
    mondeGroup.add(centerRuby);

    // 루비 주변 황금 장식 (4개 방향)
    for (let i = 0; i < 4; i++) {
      const angle = (i / 4) * Math.PI * 2;
      const x = Math.cos(angle) * 0.3;
      const z = Math.sin(angle) * 0.3;

      // 황금 장식 스파이크
      const spike = new THREE.Mesh(
        new THREE.ConeGeometry(0.08, 0.15, 8),
        Crown3D.getGoldMaterial()
      );
      spike.position.set(x, 0.25, z);
      spike.rotation.y = angle;
      mondeGroup.add(spike);

      // 작은 다이아몬드 장식
      const smallDiamond = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.06, 0),
        Crown3D.getDiamondMaterial()
      );
      smallDiamond.position.set(x * 1.5, 0.35, z * 1.5);
      smallDiamond.scale.set(0.8, 1.2, 0.8);
      mondeGroup.add(smallDiamond);
    }

    // 최상단 다이아몬드 (왕관의 정점)
    const topDiamond = new THREE.Mesh(
      new THREE.DodecahedronGeometry(0.25, 0),
      Crown3D.getDiamondMaterial()
    );
    topDiamond.position.y = 0.6;
    topDiamond.rotation.set(Math.PI / 4, Math.PI / 4, 0);
    topDiamond.scale.set(1, 1.5, 1);
    mondeGroup.add(topDiamond);

    // 최상단 다이아몬드 주변 작은 보석들 (별 모양 배치)
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const radius = i % 2 === 0 ? 0.2 : 0.15; // 교차 배치
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      const starGem = new THREE.Mesh(
        new THREE.DodecahedronGeometry(0.04, 0),
        i % 2 === 0
          ? Crown3D.getSapphireMaterial()
          : Crown3D.getEmeraldMaterial()
      );
      starGem.position.set(x, 0.55, z);
      starGem.scale.set(1, 0.6, 1);
      mondeGroup.add(starGem);
    }

    // 황금 별 장식 (최상단)
    const starGroup = new THREE.Group();
    starGroup.position.y = 0.7;

    // 5각 별 만들기
    for (let i = 0; i < 5; i++) {
      const angle = (i / 5) * Math.PI * 2 - Math.PI / 2;
      const x = Math.cos(angle) * 0.12;
      const z = Math.sin(angle) * 0.12;

      const starPoint = new THREE.Mesh(
        new THREE.ConeGeometry(0.05, 0.2, 8),
        Crown3D.getGoldMaterial()
      );
      starPoint.position.set(x, 0, z);
      starPoint.rotation.y = angle;
      starPoint.rotation.x = -Math.PI / 6;
      starGroup.add(starPoint);
    }
    mondeGroup.add(starGroup);

    group.add(mondeGroup);

    return group;
  }

  /**
   * 3D 모델 생성
   * @param {Object} product - 상품 데이터 (선택적)
   * @param {THREE.Vector3|Object} position - 위치
   * @param {boolean} addToScene - 씬에 자동 추가 여부
   * @returns {THREE.Group} 왕관 모델 그룹
   */
  static createModel(product = null, position = null, addToScene = true) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: 'Crown3D.js:571',
        message: 'createModel ENTRY',
        data: {
          product: !!product,
          position: position,
          addToScene: addToScene,
        },
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId: 'A',
      }),
    }).catch(() => {});
    // #endregion
    const group = new THREE.Group();
    group.name = 'Crown3D_Group';

    // 위치 설정
    if (position) {
      const pos =
        position instanceof THREE.Vector3
          ? position
          : new THREE.Vector3(
              position?.x || 0,
              position?.y || 0,
              position?.z || 0
            );
      group.position.copy(pos);
    }

    // 모든 구성 요소 추가 (원본 파일과 동일하게)
    const baseCirclet = Crown3D.createBaseCirclet();
    group.add(baseCirclet);

    const diamonds = Crown3D.createDiamonds();
    group.add(diamonds);

    const fleurDeLisSpikes = Crown3D.createFleurDeLisSpikes();
    group.add(fleurDeLisSpikes);

    const velvetCap = Crown3D.createVelvetCap();
    group.add(velvetCap);

    const crossArches = Crown3D.createCrossArches();
    group.add(crossArches);

    // 바운딩 박스 계산
    const box = new THREE.Box3().setFromObject(group);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    // 중앙 정렬
    group.position.sub(center);

    // userData에 정보 저장
    group.userData.modelLoaded = true;
    group.userData.boundingBox = {
      size: size,
      center: new THREE.Vector3(0, 0, 0),
    };

    // 애니메이션 설정 (천천히 회전)
    group.userData.rotationSpeed = 0.005;

    console.log(
      `✅ [Crown3D] Imperial Crown 생성 완료: 크기 (${size.x.toFixed(2)}, ${size.y.toFixed(2)}, ${size.z.toFixed(2)})`
    );

    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: 'Crown3D.js:621',
        message: 'createModel EXIT',
        data: {
          groupName: group.name,
          childrenCount: group.children.length,
          size: {
            x: size.x.toFixed(2),
            y: size.y.toFixed(2),
            z: size.z.toFixed(2),
          },
        },
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId: 'A',
      }),
    }).catch(() => {});
    // #endregion
    return group;
  }

  /**
   * 애니메이션 업데이트 (회전)
   * @param {THREE.Group} group - 왕관 그룹
   */
  static animate(group) {
    if (!group || !group.userData.modelLoaded) {
      return;
    }

    // Y축 회전 (천천히)
    if (group.userData.rotationSpeed) {
      group.rotation.y += group.userData.rotationSpeed;
    }
  }
}

// 전역 객체로 노출
window.Crown3D = Crown3D;
console.log('✅ [Crown3D] 전역 객체로 노출 완료:', typeof window.Crown3D);
