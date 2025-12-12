/**
 * 보석상 스타일 유리 진열대 (테이블) 생성 클래스
 * 디자인: 미니멀리즘 플로팅 큐브
 */
class JewelryDisplay {
  constructor(scene, position, size = { width: 2, height: 1.5, depth: 2 }) {
    this.scene = scene;
    this.position = position || { x: 0, y: 0, z: 0 };
    this.size = size;
    this.group = null;
  }

  /**
   * 미니멀리즘 플로팅 큐브 진열대 생성
   */
  create() {
    this.group = new THREE.Group();

    // 골드 프레임 재질 (더 밝고 눈에 띄게)
    const goldFrameMat = new THREE.MeshStandardMaterial({
      color: 0xFFD700, // 골드 색상
      metalness: 1.0,
      roughness: 0.1, // 더 반짝이게 (0.2 -> 0.1)
      emissive: 0x332200, // 약간의 발광 효과
      emissiveIntensity: 0.2,
      side: THREE.DoubleSide
    });

    // 프레임 두께
    const frameThickness = 0.02; // 2cm 얇은 프레임
    const { width, height, depth } = this.size;

    // [1] 상단 프레임 (4개 모서리 + 4개 변)
    // 상단 모서리 4개 (둥근 세로 기둥 - CylinderGeometry 사용)
    const cornerHeight = height;
    const cornerRadius = frameThickness / 2; // 기둥 반지름 = 프레임 두께의 절반 (테두리를 벗어나지 않게)
    const radialSegments = 16; // 원통의 세그먼트 수 (부드러운 곡면)
    const cornerGeo = new THREE.CylinderGeometry(cornerRadius, cornerRadius, cornerHeight, radialSegments);
    
    // 앞-왼 모서리 (둥근 기둥)
    const cornerFL = new THREE.Mesh(cornerGeo, goldFrameMat);
    cornerFL.position.set(-width / 2, cornerHeight / 2, -depth / 2);
    this.group.add(cornerFL);

    // 앞-오른 모서리 (둥근 기둥)
    const cornerFR = new THREE.Mesh(cornerGeo, goldFrameMat);
    cornerFR.position.set(width / 2, cornerHeight / 2, -depth / 2);
    this.group.add(cornerFR);

    // 뒤-왼 모서리 (둥근 기둥)
    const cornerBL = new THREE.Mesh(cornerGeo, goldFrameMat);
    cornerBL.position.set(-width / 2, cornerHeight / 2, depth / 2);
    this.group.add(cornerBL);

    // 뒤-오른 모서리 (둥근 기둥)
    const cornerBR = new THREE.Mesh(cornerGeo, goldFrameMat);
    cornerBR.position.set(width / 2, cornerHeight / 2, depth / 2);
    this.group.add(cornerBR);

    // 상단 가로 프레임 (4개 변)
    // 앞쪽 가로 프레임
    const topFrontGeo = new THREE.BoxGeometry(width, frameThickness, frameThickness);
    const topFront = new THREE.Mesh(topFrontGeo, goldFrameMat);
    topFront.position.set(0, height, -depth / 2);
    this.group.add(topFront);

    // 뒤쪽 가로 프레임
    const topBack = new THREE.Mesh(topFrontGeo, goldFrameMat);
    topBack.position.set(0, height, depth / 2);
    this.group.add(topBack);

    // 왼쪽 가로 프레임
    const topLeftGeo = new THREE.BoxGeometry(frameThickness, frameThickness, depth);
    const topLeft = new THREE.Mesh(topLeftGeo, goldFrameMat);
    topLeft.position.set(-width / 2, height, 0);
    this.group.add(topLeft);

    // 오른쪽 가로 프레임
    const topRight = new THREE.Mesh(topLeftGeo, goldFrameMat);
    topRight.position.set(width / 2, height, 0);
    this.group.add(topRight);

    // [2] 하단 프레임 (4개 변 - 바닥 프레임)
    // 앞쪽 가로 프레임
    const bottomFront = new THREE.Mesh(topFrontGeo, goldFrameMat);
    bottomFront.position.set(0, 0, -depth / 2);
    this.group.add(bottomFront);

    // 뒤쪽 가로 프레임
    const bottomBack = new THREE.Mesh(topFrontGeo, goldFrameMat);
    bottomBack.position.set(0, 0, depth / 2);
    this.group.add(bottomBack);

    // 왼쪽 가로 프레임
    const bottomLeft = new THREE.Mesh(topLeftGeo, goldFrameMat);
    bottomLeft.position.set(-width / 2, 0, 0);
    this.group.add(bottomLeft);

    // 오른쪽 가로 프레임
    const bottomRight = new THREE.Mesh(topLeftGeo, goldFrameMat);
    bottomRight.position.set(width / 2, 0, 0);
    this.group.add(bottomRight);

    // [3] 유리 상자 (타원형 - Ellipsoid Geometry)
    // 타원체를 만들기 위해 SphereGeometry를 사용하고 scale로 타원형으로 변형
    const glassWidth = width - frameThickness * 2;  // 프레임 두께 제외
    const glassHeight = height - frameThickness * 2; // 프레임 두께 제외
    const glassDepth = depth - frameThickness * 2;   // 프레임 두께 제외
    
    // 구 Geometry 생성 (반지름 1로 생성 후 scale로 타원체로 변형)
    const segments = 32; // 타원체의 세그먼트 수 (부드러운 곡면)
    const glassGeo = new THREE.SphereGeometry(1, segments, segments); // 반지름 1로 생성
    
    // 유리 재질: 더 잘 보이도록 설정
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.5, // 투명도 더 증가 (0.3 -> 0.5)
      transmission: 0.8, // 투과율 80% (더 보이게)
      ior: 1.5, // 유리의 굴절률
      thickness: 0.6, // 유리 두께
      roughness: 0.1, // 약간의 거칠기 (반사 효과)
      metalness: 0.0,
      side: THREE.DoubleSide,
      envMapIntensity: 1.0 // 환경 맵 강도
    });

    const glassCase = new THREE.Mesh(glassGeo, glassMat);
    
    // 타원체로 변형: 각 축에 대해 다른 scale 적용
    // 반지름 1인 구를 각 축의 절반 크기로 scale
    glassCase.scale.set(
      glassWidth / 2,   // X축 scale (width 방향) - 반지름 1을 width/2로 확장
      glassHeight / 2,  // Y축 scale (height 방향) - 반지름 1을 height/2로 확장
      glassDepth / 2    // Z축 scale (depth 방향) - 반지름 1을 depth/2로 확장
    );
    
    glassCase.position.set(0, height / 2, 0); // 상자 중심을 높이의 절반에 배치
    glassCase.castShadow = false; // 유리는 그림자 투사 안 함
    glassCase.receiveShadow = false; // 유리는 그림자 수신 안 함
    this.group.add(glassCase);
    
    console.log(`   - 타원형 유리 상자 크기: ${glassWidth.toFixed(2)} × ${glassHeight.toFixed(2)} × ${glassDepth.toFixed(2)}`);
    console.log(`   - 타원형 scale: (${(glassWidth/2).toFixed(2)}, ${(glassHeight/2).toFixed(2)}, ${(glassDepth/2).toFixed(2)})`);

    // [4] 내부 조명 (따뜻한 색상 0xFFF0E0)
    // 상단 중앙에 PointLight 배치
    const interiorLight = new THREE.PointLight(0xFFF0E0, 2.0, 5); // 따뜻한 색상, 강도 2.0, 거리 5m
    interiorLight.position.set(0, height - 0.1, 0); // 상단 프레임 바로 아래
    interiorLight.castShadow = true;
    this.group.add(interiorLight);

    // 추가 조명: 하단 중앙 (상향 조명)
    const bottomLight = new THREE.PointLight(0xFFF0E0, 1.5, 4); // 약간 약한 조명
    bottomLight.position.set(0, 0.1, 0); // 하단 프레임 바로 위
    bottomLight.castShadow = true;
    this.group.add(bottomLight);

    // [5] 진열대 위치 설정
    this.group.position.set(
      this.position.x,
      this.position.y,
      this.position.z
    );

    // 씬에 추가
    this.scene.add(this.group);

    console.log(`✅ [JewelryDisplay] 보석상 스타일 유리 진열대 생성 완료:`);
    console.log(`   - 위치: (${this.position.x}, ${this.position.y}, ${this.position.z})`);
    console.log(`   - 크기: ${this.size.width} × ${this.size.height} × ${this.size.depth}`);
    console.log(`   - 그룹 자식 수: ${this.group.children.length}`);

    return this.group;
  }

  /**
   * 진열대 제거
   */
  remove() {
    if (this.group) {
      this.scene.remove(this.group);
      // 조명 정리
      this.group.traverse((child) => {
        if (child instanceof THREE.Light) {
          child.dispose();
        }
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (child.material) {
            if (Array.isArray(child.material)) {
              child.material.forEach(mat => mat.dispose());
            } else {
              child.material.dispose();
            }
          }
        }
      });
      this.group = null;
    }
  }
}

// 전역 객체에 등록 (Showroom.js에서 사용하기 위해)
if (typeof window !== 'undefined') {
  window.JewelryDisplay = JewelryDisplay;
}

