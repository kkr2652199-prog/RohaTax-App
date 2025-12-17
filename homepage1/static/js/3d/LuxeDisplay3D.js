/**
 * LuxeDisplay3D - 럭셔리 디스플레이 3D 모델
 * React Three Fiber 컴포넌트를 순수 Three.js로 변환
 * Showcase (유리 케이스) + JewelryBox (보석 상자 5개)
 * 
 * @class LuxeDisplay3D
 * @description ProductFactory에서 사용하는 럭셔리 디스플레이 가구 클래스
 */
class LuxeDisplay3D {
  /**
   * Static Material 공유 (WebGL 텍스처 유닛 최적화)
   */
  static sharedGoldMat = null;
  static sharedWoodMat = null;
  static sharedVelvetMat = null;
  static sharedGlassMat = null;
  static sharedBlackVelvetMat = null;

  /**
   * 금색 Material 가져오기
   */
  static getGoldMaterial() {
    if (!LuxeDisplay3D.sharedGoldMat) {
      LuxeDisplay3D.sharedGoldMat = new THREE.MeshStandardMaterial({
        color: 0xCFB53B, // Champagne gold (#CFB53B)
        metalness: 0.95,
        roughness: 0.1
      });
    }
    return LuxeDisplay3D.sharedGoldMat;
  }

  /**
   * 우드 Material 가져오기
   */
  static getWoodMaterial() {
    if (!LuxeDisplay3D.sharedWoodMat) {
      LuxeDisplay3D.sharedWoodMat = new THREE.MeshStandardMaterial({
        color: 0x1a0f05, // Darker mahogany (#1a0f05)
        roughness: 0.1,
        metalness: 0.2
      });
    }
    return LuxeDisplay3D.sharedWoodMat;
  }

  /**
   * 벨벳 Material 가져오기 (바닥)
   */
  static getVelvetMaterial() {
    if (!LuxeDisplay3D.sharedVelvetMat) {
      LuxeDisplay3D.sharedVelvetMat = new THREE.MeshStandardMaterial({
        color: 0xf0f0f0, // Light gray velvet (#f0f0f0)
        roughness: 0.9
      });
    }
    return LuxeDisplay3D.sharedVelvetMat;
  }

  /**
   * 검은 벨벳 Material 가져오기 (JewelryBox 상단)
   */
  static getBlackVelvetMaterial() {
    if (!LuxeDisplay3D.sharedBlackVelvetMat) {
      LuxeDisplay3D.sharedBlackVelvetMat = new THREE.MeshStandardMaterial({
        color: 0x1a1a1a, // Black velvet (#1a1a1a)
        roughness: 0.9
      });
    }
    return LuxeDisplay3D.sharedBlackVelvetMat;
  }

  /**
   * 유리 Material 가져오기
   */
  static getGlassMaterial() {
    if (!LuxeDisplay3D.sharedGlassMat) {
      LuxeDisplay3D.sharedGlassMat = new THREE.MeshPhysicalMaterial({
        transmission: 0.98,
        thickness: 2.0,
        roughness: 0.0,
        ior: 1.5,
        color: 0xffffff,
        attenuationColor: 0xeeefff,
        attenuationDistance: 10,
        transparent: true,
        opacity: 0.3,
        envMapIntensity: 1.5
      });
    }
    return LuxeDisplay3D.sharedGlassMat;
  }

  /**
   * RoundedBox 근사치 생성 (BoxGeometry 사용)
   */
  static createRoundedBox(width, height, depth, radius = 0.05) {
    // 간단한 BoxGeometry로 근사 (실제 RoundedBox는 복잡하므로)
    return new THREE.BoxGeometry(width, height, depth);
  }

  /**
   * JewelryBox 생성 (왕관 디자인)
   * @param {Array} position - [x, y, z] 위치
   * @param {Object} size - 크기 설정 (선택적, 기본값: 골드 무제한 상품 크기)
   */
  static createJewelryBox(position, size = null) {
    const boxGroup = new THREE.Group();
    
    // 골드 무제한 상품 크기 기준 (기본값) - 크기 반으로 줄임, 높이도 조금 줄임
    const defaultSize = {
      height: 0.25, // 0.6 → 0.25 (반보다 조금 더 줄임)
      topRadius: 0.25, // 0.5 → 0.25 (반으로)
      bottomRadius: 0.3 // 0.6 → 0.3 (반으로)
    };
    
    // 크기 설정 (전달된 size가 있으면 사용, 없으면 기본값)
    const boxSize = size || defaultSize;
    const height = boxSize.height;
    const topRadius = boxSize.topRadius;
    const bottomRadius = boxSize.bottomRadius;
    
    // ✅ 왕관 디자인: 중앙 원형 링 (Circular Ring) - 두꺼운 골드 링
    const ringThickness = height * 0.15; // 링의 두께
    const ringRadius = bottomRadius;
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(ringRadius, ringThickness, 32, 64),
      LuxeDisplay3D.getGoldMaterial()
    );
    ring.rotation.x = Math.PI / 2; // 수평으로 눕히기
    ring.position.y = -height / 2 + ringThickness;
    ring.castShadow = true;
    ring.receiveShadow = true;
    boxGroup.add(ring);
    
    // ✅ 왕관 디자인: 원형 링 외곽 8개의 흰색 점 (Rivets/Bolts)
    const rivetRadius = 0.01;
    const rivetCount = 8;
    for (let i = 0; i < rivetCount; i++) {
      const angle = (i / rivetCount) * Math.PI * 2;
      const rX = ringRadius * Math.cos(angle);
      const rZ = ringRadius * Math.sin(angle);
      const rivet = new THREE.Mesh(
        new THREE.SphereGeometry(rivetRadius, 16, 16),
        new THREE.MeshStandardMaterial({
          color: 0xFFFFFF, // 흰색 리벳
          roughness: 0.3,
          metalness: 0.5
        })
      );
      rivet.position.set(rX, -height / 2 + ringThickness, rZ);
      boxGroup.add(rivet);
    }
    
    // ✅ 왕관 디자인: 원형 링에 12시 방향부터 45도 간격으로 8개의 구멍
    const holeCount = 8;
    const holeRadius = ringThickness / 2; // 깊이의 반만큼
    const holeDepth = ringThickness * 1.5; // 구멍 깊이 (링 두께보다 깊게)
    
    for (let i = 0; i < holeCount; i++) {
      // 12시 방향(0도)부터 45도 간격
      // Three.js에서 0도는 오른쪽(3시), 12시는 -90도 (또는 270도)
      // 12시 방향부터 시작하려면 -Math.PI / 2에서 시작
      const angle = -Math.PI / 2 + (i / holeCount) * Math.PI * 2; // 12시부터 45도 간격
      const holeX = ringRadius * Math.cos(angle);
      const holeZ = ringRadius * Math.sin(angle);
      
      // 구멍을 나타내는 작은 원통 (링 내부에 배치하여 구멍처럼 보이게)
      // 원형 링이 수평으로 눕혀져 있으므로, 구멍도 수직으로 배치
      const hole = new THREE.Mesh(
        new THREE.CylinderGeometry(holeRadius, holeRadius, holeDepth, 32),
        new THREE.MeshStandardMaterial({
          color: 0x1a1a1a, // 어두운 색 (구멍처럼 보이게)
          roughness: 1.0,
          metalness: 0.0
        })
      );
      // 원형 링과 같은 방향으로 배치 (수평)
      hole.rotation.x = Math.PI / 2; // 수평으로 눕히기
      // 링의 내부에 배치 (링 두께의 중앙)
      hole.position.set(holeX, -height / 2 + ringThickness, holeZ);
      boxGroup.add(hole);
    }
    
    // ✅ 왕관 디자인: 중앙 보석 (Finial Gem) - 중앙의 밝은 파란색 보석 (다이아몬드/피라미드 형태)
    const gemRadius = 0.02;
    const gemY = -height / 2 + ringThickness + height * 0.3; // 원형 링 위의 적절한 높이
    const finialGem = new THREE.Mesh(
      new THREE.OctahedronGeometry(gemRadius), // 팔면체 (다이아몬드/피라미드 형태)
      new THREE.MeshStandardMaterial({
        color: 0x00BFFF, // 밝은 파란색 (Sky Blue)
        metalness: 0.2,
        roughness: 0.1,
        emissive: 0x00BFFF, // 발광 효과
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.9
      })
    );
    finialGem.position.set(0, gemY, 0); // 중앙 지점
    finialGem.castShadow = true;
    finialGem.receiveShadow = true;
    boxGroup.add(finialGem);
    
    boxGroup.position.set(position[0], position[1], position[2]);
    
    return boxGroup;
  }

  /**
   * Showcase 생성
   */
  static createShowcase(width, height, depth, legHeight = null) {
    const showcaseGroup = new THREE.Group();
    
    const woodColor = 0x1a0f05;
    const goldColor = 0xCFB53B;
    const frameThickness = 0.06;
    // 다리를 바닥에 붙이기: legHeight를 0으로 설정
    // 총 높이 = height (다리 없음)
    const finalLegHeight = legHeight !== null ? legHeight : 0;
    
    // 깊이 비율 계산 (기준 깊이 3.0 대비)
    const depthRatio = depth / 3.0; // 깊이에 비례한 오프셋 조정
    const legOffset = 0.5 * depthRatio; // 다리 오프셋 비례 조정
    const floorOffset = 0.2 * depthRatio; // 바닥 오프셋 비례 조정
    const glassOffset = 0.05 * depthRatio; // 유리 오프셋 비례 조정
    
    // --- Legs (4개) - 바닥에 붙이기 ---
    // 다리 높이가 0이면 다리를 생성하지 않거나, 매우 작은 높이로 바닥에 붙임
    if (finalLegHeight > 0) {
      const legPositions = [
        [-width/2 + 0.5, -height/2 - finalLegHeight/2, depth/2 - legOffset],  // Front Left
        [width/2 - 0.5, -height/2 - finalLegHeight/2, depth/2 - legOffset],   // Front Right
        [-width/2 + 0.5, -height/2 - finalLegHeight/2, -depth/2 + legOffset], // Back Left
        [width/2 - 0.5, -height/2 - finalLegHeight/2, -depth/2 + legOffset]   // Back Right
      ];
      
      legPositions.forEach(pos => {
        const leg = new THREE.Mesh(
          new THREE.CylinderGeometry(0.1, 0.05, finalLegHeight, 16),
          LuxeDisplay3D.getGoldMaterial()
        );
        leg.position.set(pos[0], pos[1], pos[2]);
        leg.castShadow = true;
        leg.receiveShadow = true;
        showcaseGroup.add(leg);
      });
    }
    
    // --- Base Cabinet ---
    const base = new THREE.Mesh(
      LuxeDisplay3D.createRoundedBox(width, 0.2, depth, 0.05),
      LuxeDisplay3D.getWoodMaterial()
    );
    base.position.y = -height/2 + 0.1;
    base.castShadow = true;
    base.receiveShadow = true;
    showcaseGroup.add(base);
    
    // --- Floor of the display (Velvet Bed) ---
    const floor = new THREE.Mesh(
      LuxeDisplay3D.createRoundedBox(width - floorOffset, 0.1, depth - floorOffset, 0.1),
      LuxeDisplay3D.getVelvetMaterial()
    );
    floor.position.y = -height/2 + 0.2;
    floor.receiveShadow = true;
    showcaseGroup.add(floor);
    
    // --- Metal Frame ---
    
    // Vertical Pillars (4개 모서리)
    const pillarPositions = [
      [-width/2 + frameThickness, 0, depth/2 - frameThickness],
      [width/2 - frameThickness, 0, depth/2 - frameThickness],
      [-width/2 + frameThickness, 0, -depth/2 + frameThickness],
      [width/2 - frameThickness, 0, -depth/2 + frameThickness]
    ];
    
    pillarPositions.forEach(pos => {
      const pillar = new THREE.Mesh(
        new THREE.CylinderGeometry(frameThickness, frameThickness, height, 16),
        LuxeDisplay3D.getGoldMaterial()
      );
      pillar.position.set(pos[0], pos[1], pos[2]);
      pillar.castShadow = true;
      pillar.receiveShadow = true;
      showcaseGroup.add(pillar);
    });
    
    // Top Frame (상단 프레임)
    const topFrameParts = [
      { size: [width, frameThickness*2, frameThickness*2], pos: [0, height/2, depth/2 - frameThickness] },
      { size: [width, frameThickness*2, frameThickness*2], pos: [0, height/2, -depth/2 + frameThickness] },
      { size: [frameThickness*2, frameThickness*2, depth], pos: [-width/2 + frameThickness, height/2, 0] },
      { size: [frameThickness*2, frameThickness*2, depth], pos: [width/2 - frameThickness, height/2, 0] }
    ];
    
    topFrameParts.forEach(part => {
      const frame = new THREE.Mesh(
        LuxeDisplay3D.createRoundedBox(part.size[0], part.size[1], part.size[2], 0.02),
        LuxeDisplay3D.getGoldMaterial()
      );
      frame.position.set(part.pos[0], part.pos[1], part.pos[2]);
      frame.castShadow = true;
      showcaseGroup.add(frame);
    });
    
    // Bottom Frame (하단 프레임)
    const bottomFrameParts = [
      { size: [width, frameThickness*2, frameThickness*2], pos: [0, -height/2, depth/2 - frameThickness] },
      { size: [width, frameThickness*2, frameThickness*2], pos: [0, -height/2, -depth/2 + frameThickness] },
      { size: [frameThickness*2, frameThickness*2, depth], pos: [-width/2 + frameThickness, -height/2, 0] },
      { size: [frameThickness*2, frameThickness*2, depth], pos: [width/2 - frameThickness, -height/2, 0] }
    ];
    
    bottomFrameParts.forEach(part => {
      const frame = new THREE.Mesh(
        LuxeDisplay3D.createRoundedBox(part.size[0], part.size[1], part.size[2], 0.02),
        LuxeDisplay3D.getGoldMaterial()
      );
      frame.position.set(part.pos[0], part.pos[1], part.pos[2]);
      frame.castShadow = true;
      showcaseGroup.add(frame);
    });
    
    // --- The Glass Enclosure ---
    const glass = new THREE.Mesh(
      LuxeDisplay3D.createRoundedBox(width - glassOffset, height - glassOffset, depth - glassOffset, glassOffset),
      LuxeDisplay3D.getGlassMaterial()
    );
    glass.castShadow = true;
    glass.receiveShadow = true;
    showcaseGroup.add(glass);
    
    return showcaseGroup;
  }

  /**
   * 3D 모델 생성
   * @param {Object} product - 상품 데이터 (선택적)
   * @param {THREE.Vector3|Object} position - 위치
   * @returns {THREE.Group} 모델 그룹
   */
  static createModel(product = null, position = new THREE.Vector3(0, 0, 0)) {
    const group = new THREE.Group();
    
    // 위치 설정
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );
    
    // Showcase 크기 설정
    // 쇼룸 너비(30)의 70% = 21, 기존 진열대 높이(1.4)와 동일하게
    const showcaseWidth = 21; // 30 * 0.7 = 21 (쇼룸보다 30% 작게)
    const showcaseHeight = 1.4; // 기존 진열대 높이와 동일 (다리 없음)
    const showcaseDepth = 2.3; // 깊이 조금 더 줄임 (2.5 → 2.3)
    const boxCount = 5;
    
    // Showcase 생성
    // 다리가 없으므로 케이스가 바닥에 직접 닿음
    // 케이스 중심 Y = height/2 = 1.4/2 = 0.7
    const showcase = LuxeDisplay3D.createShowcase(showcaseWidth, showcaseHeight, showcaseDepth);
    showcase.position.set(0, showcaseHeight / 2, 0); // 바닥에 붙임 (0.7)
    group.add(showcase);
    
    // JewelryBox 위치 계산
    // showcase 상단 = showcase.position.y + showcaseHeight/2 = 0.7 + 0.7 = 1.4
    // JewelryBox 높이 = 0.6, 중심 = 1.4 + 0.3 = 1.7
    const innerWidth = showcaseWidth - 3;
    const spacing = innerWidth / (boxCount - 1);
    
    // 골드 무제한 상품(첫 번째) 크기 기준 설정 - 크기 반으로 줄임, 높이도 조금 줄임
    const goldUnlimitedSize = {
      height: 0.25, // 0.6 → 0.25 (반보다 조금 더 줄임)
      topRadius: 0.25, // 0.5 → 0.25 (반으로)
      bottomRadius: 0.3 // 0.6 → 0.3 (반으로)
    };
    
    for (let i = 0; i < boxCount; i++) {
      const x = -innerWidth / 2 + (i * spacing);
      // showcase 상단 위에 배치: showcase.position.y(0.7) + showcaseHeight/2(0.7) + JewelryBox 높이/2(0.125)
      const boxY = showcaseHeight / 2 + showcaseHeight / 2 + goldUnlimitedSize.height / 2; // = 0.7 + 0.7 + 0.125 = 1.525
      
      // 모든 상품을 골드 무제한 상품 크기와 동일하게 생성
      const jewelryBox = LuxeDisplay3D.createJewelryBox([x, boxY, 0], goldUnlimitedSize);
      group.add(jewelryBox);
    }
    
    // 전체 그룹 위치 설정
    group.position.copy(pos);
    
    // 애니메이션 플래그 설정
    group.userData.isAnimating = false;
    
    console.log('[LuxeDisplay3D] 모델 생성 완료');
    return group;
  }
  
  /**
   * 애니메이션 업데이트 (천천히 회전)
   * @param {THREE.Group} group - 모델 그룹
   */
  static animate(group) {
    if (!group || !group.userData.isAnimating) {
      return;
    }
    
    // Y축 기준으로 천천히 회전
    group.rotation.y += 0.005; // 회전 속도 조정 가능
  }
}

// 전역 객체로 노출
window.LuxeDisplay3D = LuxeDisplay3D;
console.log("✅ [LuxeDisplay3D] 전역 객체로 노출 완료:", typeof window.LuxeDisplay3D);
