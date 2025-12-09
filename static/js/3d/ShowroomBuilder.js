/**
 * ShowroomBuilder - 쇼룸 인테리어 구성 연동 모듈
 * Showroom.js의 인테리어 요소 생성 기능을 담당
 */
class ShowroomBuilder {
  constructor(scene) {
    this.scene = scene;
    this.roomSize = { width: 30, height: 15, depth: 30 };
    this.room = null;
    this.chandelierRings = null;
  }

  /**
   * 방 전체 구성 (바닥, 벽, 천장, 몰딩)
   */
  buildRoom() {
    // 충돌 범위 업데이트
    this.wallLimitX = this.roomSize.width / 2 - 1; // ±14 (벽 두께 고려)
    this.wallLimitZ = this.roomSize.depth / 2 - 1; // ±14

    // 바닥 텍스처 생성
    const floorTexture = this.createMarbleTexture();
    console.log("✅ [ShowroomBuilder] 바닥 텍스처:", floorTexture);

    // 각 면마다 다른 재질 적용 (블랙 & 화이트 모던 라운지)
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xFFFFFF, // 완전한 흰색
      roughness: 0.5, // 빛이 부드럽게 퍼지도록
      side: THREE.BackSide,
      flatShading: false
    });

    const materials = [
      wallMat, // 우측 벽 (화이트)
      wallMat, // 좌측 벽 (화이트)
      new THREE.MeshStandardMaterial({
        color: 0xFFFFFF, // 천장 (화이트)
        roughness: 0.5,
        side: THREE.BackSide,
        flatShading: false
      }), // 천장 (화이트)
      new THREE.MeshPhysicalMaterial({
        map: floorTexture,
        color: 0x111111, // 블랙 마블 (유지)
        roughness: 0.05, // 매우 매끄러움 (거울처럼 반사)
        metalness: 0.2,
        side: THREE.BackSide,
        flatShading: false
      }), // 바닥 (블랙 마블 - 거울처럼 반사)
      wallMat, // 앞벽 (화이트)
      wallMat  // 뒷벽 (화이트)
    ];

    const roomGeo = new THREE.BoxGeometry(
      this.roomSize.width,
      this.roomSize.height,
      this.roomSize.depth
    );
    this.room = new THREE.Mesh(roomGeo, materials);
    this.room.position.set(0, this.roomSize.height / 2, 0); // 방 중심
    this.room.receiveShadow = true;
    this.scene.add(this.room);

    // 몰딩 (Baseboard) - 벽 하단 띠
    this.addBaseboard();

    // 창문 삭제 (Commander 지시)
    // this.createWindows();

    // 문 추가
    this.createDoor();

    // 벽 선반 추가
    this.createWallShelves();

    return {
      room: this.room,
      wallLimitX: this.wallLimitX,
      wallLimitZ: this.wallLimitZ
    };
  }

  /**
   * 블랙 마블 텍스처 생성
   */
  createMarbleTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 2048;
    const ctx = canvas.getContext("2d");

    // 베이스 색상 (거의 검정)
    ctx.fillStyle = "#111111";
    ctx.fillRect(0, 0, 2048, 2048);

    // 타일 격자 그리기 (흰색/회색 줄무늬)
    const tileSize = 128;
    ctx.strokeStyle = "#888888";
    ctx.lineWidth = 4;

    for (let i = 0; i <= 16; i++) {
      ctx.beginPath();
      ctx.moveTo(i * tileSize, 0);
      ctx.lineTo(i * tileSize, 2048);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, i * tileSize);
      ctx.lineTo(2048, i * tileSize);
      ctx.stroke();
    }

    // 대리석 무늬 (흰색/회색 베인)
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 2;
    for (let i = 0; i < 80; i++) {
      ctx.beginPath();
      ctx.moveTo(Math.random() * 2048, Math.random() * 2048);
      for (let j = 0; j < 8; j++) {
        ctx.lineTo(Math.random() * 2048, Math.random() * 2048);
      }
      ctx.stroke();
    }

    // 추가 회색 베인
    ctx.strokeStyle = "rgba(200, 200, 200, 0.15)";
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 50; i++) {
      ctx.beginPath();
      ctx.moveTo(Math.random() * 2048, Math.random() * 2048);
      for (let j = 0; j < 5; j++) {
        ctx.lineTo(Math.random() * 2048, Math.random() * 2048);
      }
      ctx.stroke();
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = true;
    texture.anisotropy = 16;
    texture.repeat.set(5, 5);
    texture.needsUpdate = true;

    return texture;
  }

  /**
   * 벽 하단 몰딩 추가
   */
  addBaseboard() {
    const baseboardMat = new THREE.MeshStandardMaterial({
      color: 0x222222, // 다크 그레이/블랙
      roughness: 0.7,
      metalness: 0.1,
      side: THREE.FrontSide,
      flatShading: false
    });

    const height = 1.5;
    const thickness = 0.1; // 두께 절반으로 줄임 (세련된 라인)
    const wallOffset = 0.02;
    const cornerGap = 0.15;

    // 앞벽 몰딩
    const frontBaseboard = new THREE.BoxGeometry(
      this.roomSize.width - cornerGap * 2,
      height,
      thickness
    );
    const front = new THREE.Mesh(frontBaseboard, baseboardMat);
    front.position.set(0, height / 2, this.roomSize.depth / 2 - wallOffset);
    this.scene.add(front);

    // 뒷벽 몰딩
    const back = new THREE.Mesh(frontBaseboard, baseboardMat);
    back.position.set(0, height / 2, -this.roomSize.depth / 2 + wallOffset);
    this.scene.add(back);

    // 좌측벽 몰딩
    const sideBaseboard = new THREE.BoxGeometry(
      thickness,
      height,
      this.roomSize.depth - cornerGap * 2
    );
    const left = new THREE.Mesh(sideBaseboard, baseboardMat);
    left.position.set(
      -this.roomSize.width / 2 + wallOffset,
      height / 2,
      0
    );
    this.scene.add(left);

    // 우측벽 몰딩
    const right = new THREE.Mesh(sideBaseboard, baseboardMat);
    right.position.set(
      this.roomSize.width / 2 - wallOffset,
      height / 2,
      0
    );
    this.scene.add(right);

    // 모서리 연결부 (4개 모서리)
    const cornerSize = cornerGap;
    const cornerGeo = new THREE.BoxGeometry(cornerSize, height, cornerSize);

    const cornerFL = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerFL.position.set(
      -this.roomSize.width / 2 + cornerSize / 2,
      height / 2,
      this.roomSize.depth / 2 - wallOffset
    );
    this.scene.add(cornerFL);

    const cornerFR = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerFR.position.set(
      this.roomSize.width / 2 - cornerSize / 2,
      height / 2,
      this.roomSize.depth / 2 - wallOffset
    );
    this.scene.add(cornerFR);

    const cornerBL = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerBL.position.set(
      -this.roomSize.width / 2 + cornerSize / 2,
      height / 2,
      -this.roomSize.depth / 2 + wallOffset
    );
    this.scene.add(cornerBL);

    const cornerBR = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerBR.position.set(
      this.roomSize.width / 2 - cornerSize / 2,
      height / 2,
      -this.roomSize.depth / 2 + wallOffset
    );
    this.scene.add(cornerBR);
  }

  /**
   * 창문 생성 (좌/우 벽면에 아치형 통유리 창문)
   */
  createWindows() {
    const windowWidth = 4.0;
    const windowHeight = 3.0;
    const windowDepth = 0.3;

    // 창문 프레임 재질 (다크 우드)
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0x4a3728, // 다크 우드
      roughness: 0.7,
      metalness: 0.1
    });

    // 창문 유리 재질 (푸른 빛)
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.3,
      roughness: 0.1,
      metalness: 0.0,
      transmission: 0.9,
      emissive: 0xdddfff, // 푸른 빛 (밖에서 빛이 들어오는 효과)
      emissiveIntensity: 0.5
    });

    // 좌측 벽 창문 (Z-Fighting 방지를 위해 벽에서 0.2 안쪽으로)
    this.createArchWindow(
      -this.roomSize.width / 2 + 0.2, // -15 + 0.2 = -14.8
      windowWidth,
      windowHeight,
      windowDepth,
      frameMat,
      glassMat,
      Math.PI / 2 // Y축 회전 (벽면에 수직)
    );

    // 우측 벽 창문 (Z-Fighting 방지를 위해 벽에서 0.2 안쪽으로)
    this.createArchWindow(
      this.roomSize.width / 2 - 0.2, // 15 - 0.2 = 14.8
      windowWidth,
      windowHeight,
      windowDepth,
      frameMat,
      glassMat,
      -Math.PI / 2 // 반대 방향
    );
  }

  /**
   * 아치형 창문 생성 (간단한 버전)
   */
  createArchWindow(x, width, height, depth, frameMat, glassMat, rotationY) {
    const windowGroup = new THREE.Group();
    const windowY = height / 2 + 2; // 벽 중간 높이

    // [1] 창문 프레임 (사각형)
    const frameGeo = new THREE.BoxGeometry(width, height, depth);
    const frame = new THREE.Mesh(frameGeo, frameMat);
    frame.position.y = windowY;
    windowGroup.add(frame);

    // [2] 아치형 상단 (반원형 Torus를 사용하여 간단하게)
    const archRadius = width / 2;
    const archTorus = new THREE.Mesh(
      new THREE.TorusGeometry(archRadius, 0.15, 16, 32, Math.PI),
      frameMat
    );
    archTorus.rotation.x = Math.PI / 2;
    archTorus.position.y = windowY + height / 2;
    windowGroup.add(archTorus);

    // [3] 유리 (사각형)
    const glassGeo = new THREE.BoxGeometry(width * 0.9, height * 0.9, depth * 0.1);
    const glass = new THREE.Mesh(glassGeo, glassMat);
    glass.position.y = windowY;
    glass.position.z = depth / 2 - 0.05; // 프레임 앞쪽
    windowGroup.add(glass);

    // 아치형 유리 (반원형 Plane)
    const archGlassGeo = new THREE.PlaneGeometry(width * 0.9, archRadius * 0.9);
    const archGlass = new THREE.Mesh(archGlassGeo, glassMat);
    archGlass.rotation.x = -Math.PI / 2;
    archGlass.position.y = windowY + height / 2;
    archGlass.position.z = depth / 2 - 0.05;
    windowGroup.add(archGlass);

    // 위치 및 회전 설정
    windowGroup.position.set(x, 0, 0);
    windowGroup.rotation.y = rotationY;

    this.scene.add(windowGroup);

    // 창문에서 빛이 들어오는 효과 (DirectionalLight)
    const windowLight = new THREE.DirectionalLight(0xdddfff, 0.3);
    windowLight.position.set(x * 2, windowY, 0);
    this.scene.add(windowLight);

    return windowGroup;
  }

  /**
   * 문 생성 (뒷벽 중앙에 양개형 도어)
   */
  createDoor() {
    const doorGroup = new THREE.Group();
    const doorWidth = 3.0;
    const doorHeight = 4.0;
    const doorDepth = 0.2;

    // 다크 우드 재질
    const doorMat = new THREE.MeshStandardMaterial({
      color: 0x3a2a1a, // 다크 우드
      roughness: 0.6,
      metalness: 0.1
    });

    // 골드 손잡이 재질
    const handleMat = new THREE.MeshStandardMaterial({
      color: 0xffd700, // 골드
      roughness: 0.2,
      metalness: 0.9,
      emissive: 0x332200,
      emissiveIntensity: 0.2
    });

    // 왼쪽 문
    const leftDoorGeo = new THREE.BoxGeometry(
      doorWidth / 2,
      doorHeight,
      doorDepth
    );
    const leftDoor = new THREE.Mesh(leftDoorGeo, doorMat);
    leftDoor.position.x = -doorWidth / 4;
    leftDoor.position.y = doorHeight / 2;
    leftDoor.castShadow = true;
    doorGroup.add(leftDoor);

    // 오른쪽 문
    const rightDoor = new THREE.Mesh(leftDoorGeo, doorMat);
    rightDoor.position.x = doorWidth / 4;
    rightDoor.position.y = doorHeight / 2;
    rightDoor.castShadow = true;
    doorGroup.add(rightDoor);

    // 왼쪽 문 손잡이
    const handleGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.15, 16);
    const leftHandle = new THREE.Mesh(handleGeo, handleMat);
    leftHandle.position.set(
      -doorWidth / 4 + 0.1,
      doorHeight / 2,
      doorDepth / 2 + 0.05
    );
    leftHandle.rotation.z = Math.PI / 2;
    doorGroup.add(leftHandle);

    // 오른쪽 문 손잡이
    const rightHandle = new THREE.Mesh(handleGeo, handleMat);
    rightHandle.position.set(
      doorWidth / 4 - 0.1,
      doorHeight / 2,
      doorDepth / 2 + 0.05
    );
    rightHandle.rotation.z = Math.PI / 2;
    doorGroup.add(rightHandle);

    // 문 프레임
    const frameGeo = new THREE.BoxGeometry(doorWidth + 0.2, doorHeight + 0.2, 0.15);
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0x2a1a0a, // 더 어두운 우드
      roughness: 0.7,
      metalness: 0.1
    });
    const doorFrame = new THREE.Mesh(frameGeo, frameMat);
    doorFrame.position.y = doorHeight / 2;
    doorFrame.position.z = -doorDepth / 2 - 0.075;
    doorGroup.add(doorFrame);

    // 뒷벽 중앙에 배치 (Z-Fighting 방지를 위해 벽에서 0.2 앞으로)
    doorGroup.position.set(0, 0, -this.roomSize.depth / 2 + 0.2); // -15 + 0.2 = -14.8
    this.scene.add(doorGroup);

    return doorGroup;
  }

  /**
   * 벽 선반 생성 (창문 사이사이에 모던한 벽 선반)
   */
  createWallShelves() {
    const shelfMat = new THREE.MeshStandardMaterial({
      color: 0x444444, // 다크 그레이
      roughness: 0.6,
      metalness: 0.2
    });

    // 좌측 벽 선반 (창문 옆)
    const leftShelf = this.createShelf(-this.roomSize.width / 2 + 0.1, shelfMat);
    leftShelf.position.set(-8, 6, 0);
    leftShelf.rotation.y = Math.PI / 2;
    this.scene.add(leftShelf);

    // 우측 벽 선반 (창문 옆)
    const rightShelf = this.createShelf(this.roomSize.width / 2 - 0.1, shelfMat);
    rightShelf.position.set(8, 6, 0);
    rightShelf.rotation.y = -Math.PI / 2;
    this.scene.add(rightShelf);

    // 선반 위 장식 (화병 등)
    this.addShelfDecorations(-8, 6);
    this.addShelfDecorations(8, 6);
  }

  /**
   * 선반 생성
   */
  createShelf(wallX, material) {
    const shelfGroup = new THREE.Group();
    const shelfWidth = 2.0;
    const shelfDepth = 0.3;
    const shelfHeight = 0.05;

    // 선반 판
    const shelfGeo = new THREE.BoxGeometry(shelfWidth, shelfHeight, shelfDepth);
    const shelf = new THREE.Mesh(shelfGeo, material);
    shelf.castShadow = true;
    shelfGroup.add(shelf);

    // 선반 받침대 (좌우)
    const bracketGeo = new THREE.BoxGeometry(0.1, 0.5, 0.1);
    const leftBracket = new THREE.Mesh(bracketGeo, material);
    leftBracket.position.set(-shelfWidth / 2 + 0.05, -0.25, 0);
    shelfGroup.add(leftBracket);

    const rightBracket = new THREE.Mesh(bracketGeo, material);
    rightBracket.position.set(shelfWidth / 2 - 0.05, -0.25, 0);
    shelfGroup.add(rightBracket);

    return shelfGroup;
  }

  /**
   * 선반 위 장식 추가 (화병 등)
   */
  addShelfDecorations(x, y) {
    // 화병 (원통형)
    const vaseGeo = new THREE.CylinderGeometry(0.15, 0.2, 0.4, 16);
    const vaseMat = new THREE.MeshStandardMaterial({
      color: 0x8b4513, // 브라운
      roughness: 0.5,
      metalness: 0.1
    });
    const vase = new THREE.Mesh(vaseGeo, vaseMat);
    vase.position.set(x, y + 0.25, 0.2);
    vase.castShadow = true;
    this.scene.add(vase);

    // 작은 구체 장식
    const sphereGeo = new THREE.SphereGeometry(0.1, 16, 16);
    const sphereMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      roughness: 0.4,
      metalness: 0.6
    });
    const sphere1 = new THREE.Mesh(sphereGeo, sphereMat);
    sphere1.position.set(x - 0.3, y + 0.25, 0.2);
    this.scene.add(sphere1);

    const sphere2 = new THREE.Mesh(sphereGeo, sphereMat);
    sphere2.position.set(x + 0.3, y + 0.25, 0.2);
    this.scene.add(sphere2);
  }

  /**
   * 샹들리에 생성
   */
  createChandelier() {
    const chandelierGroup = new THREE.Group();

    // 발광 재질 (MeshStandardMaterial로 변경)
    const ringMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0xffffff,
      emissiveIntensity: 2.0,
      roughness: 0.1,
      metalness: 0.9
    });

    // 고리 3개
    const ring1 = new THREE.Mesh(
      new THREE.TorusGeometry(3.0, 0.15, 16, 100),
      ringMat
    );
    ring1.position.y = 0;
    ring1.rotation.x = Math.PI / 2;
    chandelierGroup.add(ring1);

    const ring2 = new THREE.Mesh(
      new THREE.TorusGeometry(2.0, 0.12, 16, 100),
      ringMat
    );
    ring2.position.y = -0.3;
    ring2.rotation.x = Math.PI / 2;
    ring2.rotation.z = Math.PI / 6;
    chandelierGroup.add(ring2);

    const ring3 = new THREE.Mesh(
      new THREE.TorusGeometry(1.0, 0.1, 16, 100),
      ringMat
    );
    ring3.position.y = -0.6;
    ring3.rotation.x = Math.PI / 2;
    ring3.rotation.z = -Math.PI / 6;
    chandelierGroup.add(ring3);

    // 천장 중앙에 매달기
    chandelierGroup.position.set(0, 14.5, 0);

    // 실제 광원
    const chandelierLight = new THREE.PointLight(0xffffff, 2.0, 30);
    chandelierLight.position.set(0, 14.5, 0);
    chandelierLight.castShadow = true;
    chandelierLight.shadow.mapSize.set(1024, 1024);
    this.scene.add(chandelierLight);

    this.scene.add(chandelierGroup);

    // 애니메이션을 위한 참조 저장
    this.chandelierRings = { ring1, ring2, ring3 };

    console.log("✅ [ShowroomBuilder] 샹들리에 설치 완료");
    return chandelierGroup;
  }

  /**
   * 진열대 생성 (바닥에 정확히 붙음)
   */
  createPedestal(position) {
    const pedestalGroup = new THREE.Group();
    const pedestalHeight = 1.4;
    const pedestalRadius = 0.5; // ⚠️ 둘레를 작게: 0.6 → 0.5
    const zFightingOffset = 0.001; // Z-Fighting 방지를 위한 최소 오프셋

    // 메인 기둥 - 투명한 유리 재질 (이쁘게!)
    const pedestalGeo = new THREE.CylinderGeometry(pedestalRadius, pedestalRadius, pedestalHeight, 32);
    const pedestalMat = new THREE.MeshPhysicalMaterial({
      color: 0xe8f4f8, // 약간 푸른빛이 도는 흰색 (프로스트 글래스 느낌)
      transparent: true,
      opacity: 0.9, // 약간 더 보이도록 (유리 느낌 유지)
      roughness: 0.05, // 매우 매끄러운 표면 (고급 유리)
      metalness: 0.0, // 비금속
      transmission: 0.92, // 거의 완전 투명 (유리 효과)
      ior: 1.5, // 유리의 굴절률 (Glass Index of Refraction)
      thickness: 0.6, // 두께감 (약간 증가하여 더 명확하게)
      side: THREE.DoubleSide, // 양면 렌더링 (투명 재질 필수)
      envMapIntensity: 1.2 // 환경 반사 강도 (유리가 주변을 반사하도록)
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    // 원기둥의 중심이 높이의 절반에 위치 (바닥면이 Y=0에 정확히 닿음)
    pedestal.position.y = pedestalHeight / 2; // 0.7 (바닥면이 Y=0.0에 정확히 닿음 - 물리법칙 준수)
    pedestal.castShadow = true;
    pedestal.receiveShadow = true; // 유리는 그림자를 받을 수 있음
    pedestalGroup.add(pedestal);

    // 상단 금색 링 (진열대 상단에 정확히 배치) - 유리와 대비되는 세련된 금색
    const topRimGeo = new THREE.TorusGeometry(pedestalRadius, 0.045, 16, 32); // 링 두께 약간 증가 (더 눈에 띄게)
    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      roughness: 0.1, // 매우 반짝이는 느낌 (고급 금속)
      metalness: 0.98, // 거의 완전한 금속 느낌
      emissive: 0xffd700, // 약간의 발광 효과
      emissiveIntensity: 0.15 // 은은한 발광
    });
    const topRim = new THREE.Mesh(topRimGeo, goldMat);
    topRim.position.y = pedestalHeight; // 1.4 (진열대 상단)
    topRim.rotation.x = Math.PI / 2;
    topRim.castShadow = true;
    pedestalGroup.add(topRim);

    // 하단 금색 링 (바닥에서 최소한의 간격으로 Z-Fighting만 방지) - 상단과 동일한 세련된 금색
    const bottomRim = new THREE.Mesh(topRimGeo, goldMat);
    bottomRim.position.y = zFightingOffset; // 0.001 (바닥에 거의 붙어 있지만 Z-Fighting 방지)
    bottomRim.rotation.x = Math.PI / 2;
    bottomRim.castShadow = true;
    pedestalGroup.add(bottomRim);

    // 위치 설정 (그룹의 Y=0으로 설정하여 바닥에 정확히 붙음)
    pedestalGroup.position.set(position.x, 0, position.z);

    // ⚠️ 물리 법칙 준수: 진열대는 바닥과 정확히 90도 수직!
    // lookAt()을 사용하면 진열대가 기울어질 수 있으므로 제거
    // rotation은 기본값(0, 0, 0)으로 유지하여 완벽한 수직 상태 보장
    pedestalGroup.rotation.set(0, 0, 0);

    this.scene.add(pedestalGroup);
    return pedestalGroup;
  }

  /**
   * 샹들리에 애니메이션 업데이트
   */
  updateChandelierAnimation() {
    if (this.chandelierRings) {
      if (this.chandelierRings.ring1) {
        this.chandelierRings.ring1.rotation.y += 0.003;
        this.chandelierRings.ring1.rotation.z += 0.001;
      }
      if (this.chandelierRings.ring2) {
        this.chandelierRings.ring2.rotation.y += 0.004;
        this.chandelierRings.ring2.rotation.x += 0.002;
      }
      if (this.chandelierRings.ring3) {
        this.chandelierRings.ring3.rotation.y += 0.005;
        this.chandelierRings.ring3.rotation.x += 0.001;
      }
    }
  }
}

// 전역 객체로 노출
window.ShowroomBuilder = ShowroomBuilder;
console.log("✅ [ShowroomBuilder] 전역 객체로 노출 완료:", typeof window.ShowroomBuilder);

