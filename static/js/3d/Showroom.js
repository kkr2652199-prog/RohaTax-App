/**
 * Showroom - 3D 진열 공간 구성
 */
class Showroom {
  constructor(containerId) {
    this.container =
      typeof containerId === "string"
        ? document.getElementById(containerId)
        : containerId;

    if (!this.container) {
      console.error("[Showroom] 컨테이너를 찾을 수 없습니다.");
      return;
    }

    if (!window.PRODUCT_DATA || !Array.isArray(window.PRODUCT_DATA)) {
      console.error(
        "[Showroom] window.PRODUCT_DATA가 없습니다. 쇼룸이 렌더링되지 않습니다."
      );
      return;
    }

    this.canvas = document.createElement("canvas");
    this.canvas.style.display = "block";
    this.canvas.style.width = "100%";
    this.canvas.style.height = "100%";
    this.container.appendChild(this.canvas);
    
    console.log(`[Showroom] 🎨 Canvas 추가: ${this.container.clientWidth}x${this.container.clientHeight}`);
    console.log(`[Showroom] 🎨 Canvas element: width=${this.canvas.width}, height=${this.canvas.height}`);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: false, // 배경색을 보기 위해 alpha 비활성화
      antialias: true,
      powerPreference: "high-performance" // 고성능 모드
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputEncoding = THREE.sRGBEncoding; // 색상 인코딩 개선
    
    console.log(`[Showroom] 🎨 Renderer 생성: ${this.canvas.width}x${this.canvas.height}`);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0a0a); // 미드나잇 럭셔리 - 어두운 배경
    
    this.camera = new THREE.PerspectiveCamera(
      50, // ⚠️ 물리 법칙: 인간의 자연스러운 시야각 (약 50도) - 원근법 왜곡 최소화
      this.container.clientWidth / this.container.clientHeight,
      0.1, // Near plane
      100  // Far plane (필요한 범위만)
    );
    this.camera.position.set(0, 3.5, 10); // ⚠️ 물리 법칙: 인간이 상품보다 훨씬 크게 느껴지는 시점 (350cm)
    this.camera.rotation.order = "YXZ"; // FPS 회전 순서
    
    // FPS 컨트롤 변수
    this.moveForward = false;
    this.moveBackward = false;
    this.moveLeft = false;
    this.moveRight = false;
    this.yaw = 0; // 좌우 회전 (Y축)
    this.pitch = -0.4; // 상하 회전 (X축) - 상품 전체를 내려다보기 (약 23도 아래)
    
    // ⚠️ 물리 법칙: 인체 측정학 (Anthropometry) - 상품보다 훨씬 높은 인간의 시점
    this.standingEyeLevel = 3.5; // 서 있을 때 눈높이 (350cm = 상자보다 훨씬 높은 시점)
    this.sittingEyeLevel = 1.4;  // 앉았을 때 눈높이 (140cm = 진열대와 같은 높이, 유지)
    this.eyeLevel = this.standingEyeLevel; // 초기값: 서 있는 상태
    this.isSitting = false; // 앉기 상태
    this.eyeLevelTransition = 0; // 부드러운 전환을 위한 값 (0~1)
    this.transitionSpeed = 0.08; // 앉기/일어서기 전환 속도
    
    this.moveSpeed = 0.08; // 이동 속도 (더 느리게 조정)
    
    // 부드러운 이동을 위한 velocity 변수
    this.velocity = new THREE.Vector3(0, 0, 0);
    this.velocityDamping = 0.88; // 감속 계수 (더 빠른 감속)
    this.maxVelocity = 0.15; // 최대 속도 제한
    this.isMouseDown = false; // 마우스 드래그 중인지

    // OrbitControls를 시선 회전용으로만 사용 (줌 유지, 이동은 WASD)
    // FPS 컨트롤로 대체 (OrbitControls 제거)
    this.controls = null;

    // 연동 모듈 초기화 (window 객체에서 명시적으로 확인)
    if (typeof window.ShowroomBuilder === "undefined") {
      console.error("❌ [Showroom] ShowroomBuilder 클래스를 찾을 수 없습니다!");
      console.error("   - window.ShowroomBuilder:", typeof window.ShowroomBuilder);
      console.error("   - ShowroomBuilder (전역):", typeof ShowroomBuilder);
      return;
    }
    if (typeof window.ProductFactory === "undefined") {
      console.error("❌ [Showroom] ProductFactory 클래스를 찾을 수 없습니다!");
      console.error("   - window.ProductFactory:", typeof window.ProductFactory);
      console.error("   - ProductFactory (전역):", typeof ProductFactory);
      return;
    }

    console.log("✅ [Showroom] 연동 모듈 확인 완료:");
    console.log("   - ShowroomBuilder:", typeof window.ShowroomBuilder);
    console.log("   - ProductFactory:", typeof window.ProductFactory);

    this.builder = new window.ShowroomBuilder(this.scene);
    this.factory = new window.ProductFactory(this.scene);

    this.addLights();
    
    // 연동 모듈을 사용하여 방 구성
    const roomData = this.builder.buildRoom();
    this.wallLimitX = roomData.wallLimitX;
    this.wallLimitZ = roomData.wallLimitZ;
    
    this.builder.createChandelier(); // 샹들리에 설치

    // 진열대 위치 정의 (U자형 배치용)
    this.pedestalPositions = [
      new THREE.Vector3(0, 0, -6),        // 중앙: Gold
      new THREE.Vector3(-4, 0, -4.5),     // 좌측 중간: Standard
      new THREE.Vector3(4, 0, -4.5),      // 우측 중간: Premium
      new THREE.Vector3(-7, 0, -1),       // 좌측 끝: Event 1
      new THREE.Vector3(7, 0, -1)         // 우측 끝: Event 2
    ];

    this.products = window.PRODUCT_DATA;
    this.meshes = [];
    this.standardCoins = this.factory.standardCoins;
    this.premiumCubes = this.factory.premiumCubes;
    this.goldCrowns = this.factory.goldCrowns;
    this.podiums = []; // 진열대 배열
    this.podiumLights = []; // 진열대 내부 조명
    this.spotLights = []; // 스포트라이트 배열
    this.particles = null; // 떠다니는 입자
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.clock = new THREE.Clock();

    this.layoutProducts();
    this.setupEvents();
    this.onResize();
    window.addEventListener("resize", () => this.onResize());
    this.animate();
  }

  addLights() {
    // 블랙 & 화이트 모던 라운지 - 화사한 조명
    // 주변광 증가 (밝은 분위기)
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambient);

    // 천장 중앙 조명 (약한 PointLight) - 초소형 룸에 맞게
    const ceilingLight = new THREE.PointLight(0xFFE4B5, 0.8, 20);
    ceilingLight.position.set(0, 13, 0); // 낮아진 천장에 맞게 (15/2 - 2 = 5.5, 하지만 중앙이므로 13)
    ceilingLight.castShadow = true;
    ceilingLight.shadow.mapSize.set(1024, 1024);
    this.scene.add(ceilingLight);
    
    // 보조 조명 제거 (SpotLight에 집중)
  }
  
  addProductSpotlight(position, color) {
    // 진열대 위에서 상품을 비추는 핀 조명 (블랙 & 화이트 모던 라운지 - 선명한 그림자)
    const spotlight = new THREE.SpotLight(color, 3.5, 15, Math.PI / 6, 0.2, 2);
    spotlight.position.set(position.x, position.y + 4, position.z); // 진열대 위에서 비춤
    
    // Target을 별도 Object3D로 생성하여 scene에 추가
    const target = new THREE.Object3D();
    target.position.set(position.x, position.y, position.z);
    this.scene.add(target);
    spotlight.target = target;
    
    spotlight.castShadow = true;
    spotlight.shadow.mapSize.width = 2048; // 그림자 품질 대폭 향상 (밝은 방에서 선명하게)
    spotlight.shadow.mapSize.height = 2048;
    spotlight.shadow.bias = -0.0001; // 그림자 깨짐 방지
    spotlight.shadow.radius = 4; // 그림자 가장자리 부드러움 (선명하게)
    this.scene.add(spotlight);
    this.spotLights.push(spotlight); // 배열에 추가 (나중에 제어 가능)
  }

  createPodium(type, position) {
    // 진열대 그룹
    const podiumGroup = new THREE.Group();
    
    // 밝은 진열대 (하얀 산호석/나무 데크 느낌)
    const podiumGeometry = new THREE.CylinderGeometry(1.2, 1.2, 0.4, 32);
    const podiumMaterial = new THREE.MeshStandardMaterial({
      color: 0xF5F5DC, // 베이지/화이트
      roughness: 0.6,
      metalness: 0.1
    });
    const podium = new THREE.Mesh(podiumGeometry, podiumMaterial);
    podium.position.y = 0.2;
    podium.castShadow = true;
    podium.receiveShadow = true;
    podiumGroup.add(podium);
    
    // 진열대 테두리 (강조)
    let accentColor = 0xffffff;
    if (type === 'event') {
      accentColor = 0xffd700; // 골드
    } else if (type === 'standard') {
      accentColor = 0xc0c0c0; // 실버
    } else if (type === 'premium') {
      accentColor = 0x00bfff; // 블루
    } else if (type === 'gold') {
      accentColor = 0xffd700; // 골드
    }
    
    const ringGeometry = new THREE.TorusGeometry(1.2, 0.05, 16, 100);
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: accentColor,
      emissive: accentColor,
      emissiveIntensity: 0.5
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0.4;
    podiumGroup.add(ring);
    
    // 진열대 위치 설정
    podiumGroup.position.copy(position);
    this.scene.add(podiumGroup);
    this.podiums.push(podiumGroup);
    
    return podiumGroup;
  }

  createMarbleTexture() {
    // 블랙 마블 텍스처 (검은색 바탕에 흰색/회색 줄무늬) - 미드나잇 럭셔리
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 2048;
    const ctx = canvas.getContext('2d');
    
    // 베이스 색상 (거의 검정)
    ctx.fillStyle = '#111111'; // 블랙 마블 베이스
    ctx.fillRect(0, 0, 2048, 2048);
    
    // 타일 격자 그리기 (흰색/회색 줄무늬)
    const tileSize = 128;
    ctx.strokeStyle = '#888888'; // 회색 줄무늬
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
    
    // 대리석 무늬 (흰색/회색 베인) - 블랙 마블 특유의 줄무늬
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'; // 흰색 베인
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
    ctx.strokeStyle = 'rgba(200, 200, 200, 0.15)';
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
    texture.minFilter = THREE.LinearMipmapLinearFilter; // Mipmap 필터링
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = true; // Mipmap 생성
    texture.anisotropy = 16; // 이방성 필터링 (깨짐 방지)
    texture.repeat.set(5, 5); // 반복 횟수 감소 (더 큰 타일)
    texture.needsUpdate = true; // 강제 업데이트
    
    console.log("✅ [Showroom] 대리석 타일 텍스처 생성 완료:", texture);
    return texture;
  }

  createWallTexture() {
    // 벽면 미세 텍스처 (딥 차콜) - 미드나잇 럭셔리
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');
    
    // 베이스 색상 (딥 차콜)
    ctx.fillStyle = '#222222';
    ctx.fillRect(0, 0, 1024, 1024);
    
    // 미세한 노이즈 패턴 (매트한 질감) - 어두운 톤
    const imageData = ctx.createImageData(1024, 1024);
    for (let i = 0; i < imageData.data.length; i += 4) {
      const noise = Math.random() * 6 - 3; // -3 ~ +3 (미세한 변화)
      imageData.data[i] = Math.min(255, Math.max(0, 34 + noise));     // R (0x22 = 34)
      imageData.data[i + 1] = Math.min(255, Math.max(0, 34 + noise)); // G
      imageData.data[i + 2] = Math.min(255, Math.max(0, 34 + noise));  // B
      imageData.data[i + 3] = 255; // A
    }
    ctx.putImageData(imageData, 0, 0);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = true;
    texture.anisotropy = 16;
    texture.repeat.set(2, 2); // 벽면 전체에 반복
    texture.needsUpdate = true;
    return texture;
  }

  createRoom() {
    // 프라이빗 보석함 (The Vault) - 초소형 럭셔리 룸
    const roomSize = { width: 30, height: 15, depth: 30 };
    
    // 충돌 범위 업데이트
    this.wallLimitX = roomSize.width / 2 - 1; // ±14 (벽 두께 고려)
    this.wallLimitZ = roomSize.depth / 2 - 1; // ±14
    
    // 바닥 텍스처 생성 (블랙 마블 유지)
    const floorTexture = this.createMarbleTexture();
    console.log("✅ [Showroom] 바닥 텍스처:", floorTexture);
    
    // 벽면 텍스처는 사용하지 않음 (순수 흰색)
    // const wallTexture = this.createWallTexture();
    
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
    
    const roomGeo = new THREE.BoxGeometry(roomSize.width, roomSize.height, roomSize.depth);
    this.room = new THREE.Mesh(roomGeo, materials);
    this.room.position.set(0, roomSize.height / 2, 0); // 방 중심
    this.room.receiveShadow = true;
    this.scene.add(this.room);
    
    // 몰딩 (Baseboard) - 벽 하단 띠
    this.addBaseboard(roomSize);
  }
  
  addBaseboard(roomSize) {
    // 다크 그레이 라인 몰딩 (블랙 & 화이트 모던 라운지)
    const baseboardMat = new THREE.MeshStandardMaterial({
      color: 0x222222, // 다크 그레이/블랙
      roughness: 0.7,
      metalness: 0.1,
      side: THREE.FrontSide,
      flatShading: false
    });
    
    const height = 1.5;
    const thickness = 0.1; // 두께 절반으로 줄임 (세련된 라인)
    const wallOffset = 0.02; // 벽면에서 살짝 떨어뜨림 (Z-fighting 방지, 더 가깝게)
    const cornerGap = 0.15; // 모서리 겹침 방지 (더 정확한 연결)
    
    // 앞벽 몰딩 (좌우 모서리 제외)
    const frontBaseboard = new THREE.BoxGeometry(roomSize.width - cornerGap * 2, height, thickness);
    const front = new THREE.Mesh(frontBaseboard, baseboardMat);
    front.position.set(0, height / 2, roomSize.depth / 2 - wallOffset);
    this.scene.add(front);
    
    // 뒷벽 몰딩 (좌우 모서리 제외)
    const back = new THREE.Mesh(frontBaseboard, baseboardMat);
    back.position.set(0, height / 2, -roomSize.depth / 2 + wallOffset);
    this.scene.add(back);
    
    // 좌측벽 몰딩 (앞뒤 벽과 겹치지 않게, 모서리 제외)
    const sideBaseboard = new THREE.BoxGeometry(thickness, height, roomSize.depth - cornerGap * 2);
    const left = new THREE.Mesh(sideBaseboard, baseboardMat);
    left.position.set(-roomSize.width / 2 + wallOffset, height / 2, 0);
    this.scene.add(left);
    
    // 우측벽 몰딩 (앞뒤 벽과 겹치지 않게, 모서리 제외)
    const right = new THREE.Mesh(sideBaseboard, baseboardMat);
    right.position.set(roomSize.width / 2 - wallOffset, height / 2, 0);
    this.scene.add(right);
    
    // 모서리 연결부 (4개 모서리)
    const cornerSize = cornerGap;
    const cornerGeo = new THREE.BoxGeometry(cornerSize, height, cornerSize);
    
    // 앞-좌 모서리
    const cornerFL = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerFL.position.set(-roomSize.width / 2 + cornerSize / 2, height / 2, roomSize.depth / 2 - wallOffset);
    this.scene.add(cornerFL);
    
    // 앞-우 모서리
    const cornerFR = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerFR.position.set(roomSize.width / 2 - cornerSize / 2, height / 2, roomSize.depth / 2 - wallOffset);
    this.scene.add(cornerFR);
    
    // 뒤-좌 모서리
    const cornerBL = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerBL.position.set(-roomSize.width / 2 + cornerSize / 2, height / 2, -roomSize.depth / 2 + wallOffset);
    this.scene.add(cornerBL);
    
    // 뒤-우 모서리
    const cornerBR = new THREE.Mesh(cornerGeo, baseboardMat);
    cornerBR.position.set(roomSize.width / 2 - cornerSize / 2, height / 2, -roomSize.depth / 2 + wallOffset);
    this.scene.add(cornerBR);
  }
  
  createLuxuryPedestal(position) {
    // 럭셔리 진열대 (블랙 마블 + 금색 링) - 바닥에 정확히 붙이기 (물리적으로 딱 붙음)
    const pedestalGroup = new THREE.Group();
    
    // [1] 메인 기둥 (블랙 마블)
    const pedestalHeight = 1.4; // 높이 1.4m
    const pedestalGeo = new THREE.CylinderGeometry(0.6, 0.6, pedestalHeight, 32);
    const pedestalMat = new THREE.MeshStandardMaterial({
      color: 0x111111, // 블랙 마블
      roughness: 0.1,
      metalness: 0.8
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    // 기둥의 하단이 그룹 내부에서 Y=0.001에 위치 (Z-fighting 방지를 위한 미세한 오프셋)
    const zFightingOffset = 0.001; // Z-fighting 방지를 위한 최소 오프셋 (거의 보이지 않음)
    pedestal.position.y = pedestalHeight / 2 + zFightingOffset; // 기둥 중심 = 높이의 절반 + 미세 오프셋
    pedestal.castShadow = true;
    pedestal.receiveShadow = false; // 바닥과 겹치지 않도록 그림자 수신 비활성화
    pedestalGroup.add(pedestal);
    
    // [2] 상단 금색 링 (Top Gold Rim)
    const topRimGeo = new THREE.TorusGeometry(0.6, 0.05, 16, 32);
    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xFFD700, // 골드
      roughness: 0.2,
      metalness: 0.9
    });
    const topRim = new THREE.Mesh(topRimGeo, goldMat);
    topRim.position.y = pedestalHeight + zFightingOffset; // 기둥 상단 (높이 1.4m + 미세 오프셋)
    topRim.rotation.x = Math.PI / 2;
    topRim.castShadow = true;
    pedestalGroup.add(topRim);
    
    // [3] 하단 금색 링 (Bottom Gold Rim) - 바닥에 정확히 닿도록 (겹치지 않게)
    const bottomRim = new THREE.Mesh(topRimGeo, goldMat);
    bottomRim.position.y = zFightingOffset + 0.02; // 기둥 하단에서 살짝 올려서 바닥과 겹치지 않게
    bottomRim.rotation.x = Math.PI / 2;
    bottomRim.castShadow = true;
    pedestalGroup.add(bottomRim);
    
    // 위치 설정 (바닥 Y=0에 정확히 닿도록 - 물리적으로 딱 붙음, 겹침 없음)
    // 그룹의 Y 위치를 0으로 설정하고, 기둥 내부에서 zFightingOffset만큼 올려서 Z-fighting 방지
    pedestalGroup.position.set(position.x, 0, position.z); // Y는 항상 0으로 고정 (바닥에 붙임)
    
    // 사용자를 향해 살짝 회전
    const lookAtTarget = new THREE.Vector3(0, 3.8, 12); // 카메라 높이에 맞춤
    pedestalGroup.lookAt(lookAtTarget);
    
    this.scene.add(pedestalGroup);
    return pedestalGroup;
  }

  createFurniture() {
    // 기존 가구 모두 삭제 - 진열대는 상품 배치 시 생성
    // 진열대 위치 정보 저장 (U자형 배치용)
    this.pedestalPositions = [
      { x: 0, y: 0, z: -6 },        // 중앙: Gold
      { x: -4, y: 0, z: -4.5 },     // 좌측 중간: Standard
      { x: 4, y: 0, z: -4.5 },      // 우측 중간: Premium
      { x: -7, y: 0, z: -1 },       // 좌측 끝: Event 1
      { x: 7, y: 0, z: -1 }         // 우측 끝: Event 2
    ];
  }

  createChandelier() {
    // 모던 링 스타일 샹들리에 (블랙 & 화이트 모던 라운지)
    const chandelierGroup = new THREE.Group();
    
    // 발광 재질 (스스로 강력하게 빛남)
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xFFFFFF,
      emissive: 0xFFFFFF,
      emissiveIntensity: 2.0
    });
    
    // 고리 3개 (크기가 다른 Torus)
    const ring1 = new THREE.Mesh(
      new THREE.TorusGeometry(3.0, 0.15, 16, 100),
      ringMat
    );
    ring1.position.y = 0;
    ring1.rotation.x = Math.PI / 2; // 수평으로 배치
    chandelierGroup.add(ring1);
    
    const ring2 = new THREE.Mesh(
      new THREE.TorusGeometry(2.0, 0.12, 16, 100),
      ringMat
    );
    ring2.position.y = -0.3; // Y축으로 살짝 엇갈림
    ring2.rotation.x = Math.PI / 2;
    ring2.rotation.z = Math.PI / 6; // 각도 차이
    chandelierGroup.add(ring2);
    
    const ring3 = new THREE.Mesh(
      new THREE.TorusGeometry(1.0, 0.1, 16, 100),
      ringMat
    );
    ring3.position.y = -0.6; // Y축으로 더 엇갈림
    ring3.rotation.x = Math.PI / 2;
    ring3.rotation.z = -Math.PI / 6; // 반대 각도
    chandelierGroup.add(ring3);
    
    // 천장 중앙에 매달기 (방 높이 15, 천장 Y = 15)
    chandelierGroup.position.set(0, 14.5, 0); // 천장에서 약 0.5 아래에 매달림
    
    // 실제 광원 (PointLight) - 방 전체를 밝히는 역할
    const chandelierLight = new THREE.PointLight(0xFFFFFF, 2.0, 30);
    chandelierLight.position.set(0, 14.5, 0);
    chandelierLight.castShadow = true;
    chandelierLight.shadow.mapSize.set(1024, 1024);
    this.scene.add(chandelierLight);
    
    this.scene.add(chandelierGroup);
    
    // 애니메이션을 위한 참조 저장
    this.chandelierRings = { ring1, ring2, ring3 };
    
    console.log("✅ [Showroom] 샹들리에 설치 완료");
  }

  layoutProducts() {
    const count = this.products.length;
    console.log(`💎 [Showroom] 프라이빗 보석함 배치 시작: ${count}개`);
    
    if (count === 0) {
      console.warn("⚠️ [Showroom] 상품이 없습니다.");
      return;
    }

    // 상품 분류
    const eventProducts = this.products.filter(p => p.type === 'event' || p.type === 'event_period');
    const regularProducts = this.products.filter(p => p.type !== 'event' && p.type !== 'event_period');
    const standard = regularProducts.find(p => p.name.toLowerCase().includes('standard'));
    const gold = regularProducts.find(p => p.name.toLowerCase().includes('gold'));
    const premium = regularProducts.find(p => p.name.toLowerCase().includes('premium'));

    console.log(`   무료 상품: ${eventProducts.length}개, 유료 상품: ${regularProducts.length}개`);

    // U자형 배치 (반원형) - 사용자(0, 3.8, 12)를 바라보는 형태
    // 진열대가 바닥에 정확히 붙음 (물리법칙 준수)
    // 진열대 높이 1.4m (상단), 바닥면 Y=0.0 (물리법칙)
    const pedestalTop = 1.4; // 진열대 상단 높이 (바닥에서 1.4m)
    
    // ⚠️ 중요: ProductFactory 내부에서 이미 각 상품의 중심을 올리므로
    // 여기서는 진열대 상단(1.4m)만 전달합니다. (이중 가산 방지!)
    // - Standard Coin: ProductFactory 내부에서 +0.125m 올림 처리됨
    // - Premium Cube: ProductFactory 내부에서 +0.8m 올림 처리됨
    // - Gold Crown: ProductFactory 내부에서 +0.7m 올림 처리됨
    // - GiftBox: ProductFactory 내부에서 +0.945m 올림 처리됨
    const standardCoinHeight = pedestalTop; // 1.4m (내부 오프셋 자동 처리)
    const premiumCubeHeight = pedestalTop; // 1.4m (내부 오프셋 자동 처리)
    const goldCrownHeight = pedestalTop; // 1.4m (내부 오프셋 자동 처리)
    const giftBoxHeight = pedestalTop; // 1.4m (내부 오프셋 자동 처리)

    // [1] 중앙 - Gold 상품 (왕관)
    if (gold && this.pedestalPositions[0]) {
      const pedestalPos = this.pedestalPositions[0];
      this.builder.createPedestal(pedestalPos);
      const productPos = new THREE.Vector3(pedestalPos.x, goldCrownHeight, pedestalPos.z);
      console.log(`   [중앙 진열대] "Gold" → (${productPos.x}, ${productPos.y}, ${productPos.z})`);
      const productGroup = this.factory.createRegularProduct(gold, productPos);
      if (productGroup) {
        this.meshes.push(productGroup);
        this.addProductSpotlight(productPos, 0xffd700); // 골드 조명
      }
    }

    // [2] 좌측 중간 - Standard 상품 (코인)
    if (standard && this.pedestalPositions[1]) {
      const pedestalPos = this.pedestalPositions[1];
      this.builder.createPedestal(pedestalPos);
      const productPos = new THREE.Vector3(pedestalPos.x, standardCoinHeight, pedestalPos.z);
      console.log(`   [좌측 중간 진열대] "Standard" → (${productPos.x}, ${productPos.y}, ${productPos.z})`);
      const productGroup = this.factory.createRegularProduct(standard, productPos);
      if (productGroup) {
        this.meshes.push(productGroup);
        this.addProductSpotlight(productPos, 0xc0c0c0); // 실버 조명
      }
    }

    // [3] 우측 중간 - Premium 상품 (큐브)
    if (premium && this.pedestalPositions[2]) {
      const pedestalPos = this.pedestalPositions[2];
      this.builder.createPedestal(pedestalPos);
      const productPos = new THREE.Vector3(pedestalPos.x, premiumCubeHeight, pedestalPos.z);
      console.log(`   [우측 중간 진열대] "Premium" → (${productPos.x}, ${productPos.y}, ${productPos.z})`);
      const productGroup = this.factory.createRegularProduct(premium, productPos);
      if (productGroup) {
        this.meshes.push(productGroup);
        this.addProductSpotlight(productPos, 0x00bfff); // 블루 조명
      }
    }

    // [4] 좌측 끝 - Event 상품 1 (선물 상자)
    if (eventProducts[0] && this.pedestalPositions[3]) {
      const pedestalPos = this.pedestalPositions[3];
      this.builder.createPedestal(pedestalPos);
      const productPos = new THREE.Vector3(pedestalPos.x, giftBoxHeight, pedestalPos.z);
      console.log(`   [좌측 끝 진열대] "${eventProducts[0].name}" → (${productPos.x}, ${productPos.y}, ${productPos.z})`);
      const productGroup = this.factory.createEventProduct(eventProducts[0], productPos);
      if (productGroup) {
        this.meshes.push(productGroup);
        this.addProductSpotlight(productPos, 0xffd700); // 골드 조명
      }
    }
    // [5] 우측 끝 - Event 상품 2 (선물 상자)
    if (eventProducts[1] && this.pedestalPositions[4]) {
      const pedestalPos = this.pedestalPositions[4];
      this.builder.createPedestal(pedestalPos);
      const productPos = new THREE.Vector3(pedestalPos.x, giftBoxHeight, pedestalPos.z);
      console.log(`   [우측 끝 진열대] "${eventProducts[1].name}" → (${productPos.x}, ${productPos.y}, ${productPos.z})`);
      const productGroup = this.factory.createEventProduct(eventProducts[1], productPos);
      if (productGroup) {
        this.meshes.push(productGroup);
        this.addProductSpotlight(productPos, 0xffd700); // 골드 조명
      }
    }

    console.log(`✅ [Showroom] 총 ${this.meshes.length}개 상품 배치 완료`);
  }

  createEventProduct(product, position) {
    if (typeof GiftBox3D === "undefined") {
      console.error("❌ GiftBox3D 클래스를 찾을 수 없습니다!");
      return;
    }

    console.log(`      → 이벤트 상품 생성: "${product.name}"`);
    const giftBox = new GiftBox3D(null, {
      boxColor: 0x7b1113,
      ribbonColor: 0xffd700
    });
    const group = giftBox.createModel();
    group.position.copy(position);
    group.userData = group.userData || {};
    group.userData.productData = product;
    group.scale.set(0.9, 0.9, 0.9);
    
    // 사용자를 향해 회전
    const lookAtTarget = new THREE.Vector3(0, 3.8, 12); // 카메라 높이에 맞춤
    group.lookAt(lookAtTarget);
    
    this.scene.add(group);
    this.meshes.push(group);
    // 스포트라이트 추가 (상품 강조)
    this.addProductSpotlight(position, 0xffd700); // 골드 조명
    
    console.log(`      ✅ 선물 상자 추가됨: 위치 (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
  }

  createRegularProduct(product, position, index) {
    console.log(`      → 일반 상품 생성: "${product.name}"`);
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
      console.error(`      ❌ 그룹 생성 실패!`);
      return;
    }

    group.userData.productData = product;
    
    // 사용자를 향해 회전
    const lookAtTarget = new THREE.Vector3(0, 3.8, 12); // 카메라 높이에 맞춤
    group.lookAt(lookAtTarget);
    
    this.scene.add(group);
    this.meshes.push(group);
    
    // 스포트라이트 추가 (상품별 색상)
    let lightColor = 0xffffff;
    if (normalized === "standard") lightColor = 0xc0c0c0; // 실버
    else if (normalized === "premium") lightColor = 0x00bfff; // 블루
    else if (normalized === "gold") lightColor = 0xffd700; // 골드
    this.addProductSpotlight(position, lightColor);
    
    console.log(`      ✅ 씬에 추가됨: 위치 (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
  }

  createStandardCoin(product, position) {
    // 은색 코인 + 옆면 톱니바퀴 디테일
    const group = new THREE.Group();
    const coinMat = new THREE.MeshStandardMaterial({
      color: 0xc0c0c0,
      metalness: 1.0,
      roughness: 0.2
    });
    const coin = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 0.25, 64), coinMat);
    coin.rotation.x = Math.PI / 2;
    coin.castShadow = true;
    coin.receiveShadow = true;
    group.add(coin);

    // 옆면 톱니바퀴 디테일 (톱니 모양)
    const toothMat = new THREE.MeshStandardMaterial({
      color: 0x888888, // 어두운 회색 (대비)
      metalness: 0.8,
      roughness: 0.3
    });
    const toothCount = 24; // 톱니 개수
    const radius = 1.2;
    const toothHeight = 0.15;
    const toothWidth = 0.08;
    
    for (let i = 0; i < toothCount; i++) {
      const angle = (i / toothCount) * Math.PI * 2;
      const tooth = new THREE.Mesh(
        new THREE.BoxGeometry(toothWidth, toothHeight, toothWidth),
        toothMat
      );
      // 톱니를 코인 옆면에 배치
      tooth.position.set(
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius
      );
      // 톱니가 바깥쪽을 향하도록 회전
      tooth.rotation.y = angle + Math.PI / 2;
      tooth.castShadow = true;
      group.add(tooth);
    }

    const rimMat = new THREE.MeshStandardMaterial({
      color: 0xfffff0,
      metalness: 1,
      roughness: 0.1
    });
    const rim = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.08, 16, 100), rimMat);
    rim.rotation.x = Math.PI / 2;
    group.add(rim);

    const label = this.createPriceLabel(product);
    label.position.set(0, 0.9, 0);
    group.add(label);

    group.position.copy(position);
    group.userData.productData = product;
    this.standardCoins.push(group);
    return group;
  }

  createPremiumCube(product, position) {
    // 테크 큐브: 네온 시안 와이어프레임 + 반대 방향 회전 내부 큐브
    const group = new THREE.Group();
    const outerSize = 1.6;
    
    // 외부 와이어프레임 (네온 시안 - 두께 강화)
    const lines = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(outerSize, outerSize, outerSize)),
      new THREE.LineBasicMaterial({ 
        color: 0x00FFFF, // 네온 시안 (Cyan)
        linewidth: 3 // 두께 강화 (WebGL에서는 실제로는 작동하지 않지만 의도 표시)
      })
    );
    // 두께를 시각적으로 강화하기 위해 여러 레이어 추가
    const lines2 = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(outerSize * 0.98, outerSize * 0.98, outerSize * 0.98)),
      new THREE.LineBasicMaterial({ color: 0x00FFFF, transparent: true, opacity: 0.5 })
    );
    group.add(lines);
    group.add(lines2);

    // 내부 큐브 (반대 방향으로 빠르게 회전)
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x00FFFF, // 네온 시안
      transmission: 0.8,
      transparent: true,
      roughness: 0.1,
      metalness: 0.8,
      emissive: 0x004444, // 약한 발광
      emissiveIntensity: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05
    });
    const inner = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), coreMat);
    inner.position.set(0, -0.1, 0);
    inner.castShadow = true;
    group.add(inner);

    const label = this.createPriceLabel(product);
    label.position.set(0, 1.6, 0);
    group.add(label);

    group.position.copy(position);
    // 반대 방향 회전을 위한 속도 저장
    this.premiumCubes.push({ 
      group, 
      inner, // 내부 큐브 참조
      outerRotation: 0, // 외부 회전 속도
      innerRotation: 0, // 내부 회전 속도 (반대 방향, 더 빠름)
      offset: Math.random() * Math.PI 
    });
    group.userData.productData = product;
    return group;
  }

  createGoldCrown(product, position) {
    // 자이로스코프: 서로 교차하여 회전하는 3개의 링 + 중앙 에너지 코어
    const group = new THREE.Group();
    
    // 골드 재질 (순금, 자체 발광)
    const goldMat = new THREE.MeshPhysicalMaterial({
      color: 0xFFD700, // 순금
      metalness: 1.0,
      roughness: 0.1,
      emissive: 0x332200, // 자체 발광 (어두운 골드)
      emissiveIntensity: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05
    });
    
    // [1] 3개의 교차하는 Torus 링
    const ring1 = new THREE.Mesh(
      new THREE.TorusGeometry(0.7, 0.12, 32, 100),
      goldMat
    );
    ring1.rotation.x = Math.PI / 2; // 수평
    ring1.castShadow = true;
    group.add(ring1);
    
    const ring2 = new THREE.Mesh(
      new THREE.TorusGeometry(0.7, 0.12, 32, 100),
      goldMat
    );
    ring2.rotation.y = Math.PI / 2; // 수직 (Y축)
    ring2.rotation.z = Math.PI / 4; // 45도 기울임
    ring2.castShadow = true;
    group.add(ring2);
    
    const ring3 = new THREE.Mesh(
      new THREE.TorusGeometry(0.7, 0.12, 32, 100),
      goldMat
    );
    ring3.rotation.x = Math.PI / 4; // 45도 기울임
    ring3.rotation.z = Math.PI / 2; // 수직 (Z축)
    ring3.castShadow = true;
    group.add(ring3);
    
    // [2] 중앙 에너지 코어 (빛나는 구체)
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0xFFD700,
      metalness: 0.8,
      roughness: 0.1,
      emissive: 0xFFAA00, // 밝은 골드 발광
      emissiveIntensity: 0.8,
      transparent: true,
      opacity: 0.9
    });
    const core = new THREE.Mesh(
      new THREE.SphereGeometry(0.25, 32, 32),
      coreMat
    );
    core.castShadow = true;
    group.add(core);
    
    // 파티클 효과 (에너지 코어 주변)
    const particleGeo = new THREE.BufferGeometry();
    const positions = [];
    for (let i = 0; i < 50; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const radius = 0.3 + Math.random() * 0.3;
      positions.push(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
      );
    }
    particleGeo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
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

    const label = this.createPriceLabel(product);
    label.position.set(0, 2.2, 0);
    group.add(label);

    group.position.copy(position);
    this.goldCrowns.push({ group, ring1, ring2, ring3, core, particles });
    group.userData.productData = product;
    return group;
  }

  createFallbackProduct(product, position) {
    const group = new THREE.Group();
    const geometry = new THREE.BoxGeometry(0.9, 0.9, 0.9);
    const material = new THREE.MeshStandardMaterial({ color: 0x808080, roughness: 0.4 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    group.add(mesh);
    group.position.copy(position); // position은 이미 올바른 높이로 설정됨

    const label = this.createPriceLabel(product);
    label.position.set(position.x, 1.5, position.z);
    group.add(label);

    group.userData.productData = product;
    return group;
  }

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
    const priceLabel =
      product.price > 0
        ? `${new Intl.NumberFormat("ko-KR").format(product.price)}원`
        : "무료";
    ctx.fillText(priceLabel, canvas.width / 2, canvas.height / 2 + 8);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    const mat = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthTest: false
    });
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1), mat);
    plane.renderOrder = 999;
    return plane;
  }

  setupEvents() {
    this.renderer.domElement.addEventListener("click", (event) =>
      this.onClick(event)
    );
    
    // FPS 마우스 컨트롤
    this.renderer.domElement.addEventListener('mousedown', (e) => {
      this.isMouseDown = true;
    });
    
    document.addEventListener('mouseup', () => {
      this.isMouseDown = false;
    });
    
    this.renderer.domElement.addEventListener('mousemove', (e) => {
      if (!this.isMouseDown) return;
      
      const sensitivity = 0.002; // 마우스 감도
      this.yaw -= e.movementX * sensitivity; // 좌우 회전
      this.pitch -= e.movementY * sensitivity; // 상하 회전
      
      // Pitch 제한 (천장/바닥만 보게, 목이 안 꺾이게)
      const maxPitch = Math.PI / 2 - 0.1; // 거의 90도
      this.pitch = Math.max(-maxPitch, Math.min(maxPitch, this.pitch));
    });
    
    // WASD 키보드 이벤트
    document.addEventListener('keydown', (event) => {
      switch(event.code) {
        case 'KeyW':
        case 'ArrowUp':
          this.moveForward = true;
          break;
        case 'KeyS':
        case 'ArrowDown':
          this.moveBackward = true;
          break;
        case 'KeyA':
        case 'ArrowLeft':
          this.moveLeft = true;
          break;
        case 'KeyD':
        case 'ArrowRight':
          this.moveRight = true;
          break;
        case 'ShiftLeft':
        case 'ShiftRight':
          // ⚠️ 물리 법칙: 앉기/일어서기 토글 (인체 운동학)
          if (!event.repeat) { // 키를 누르고 있어도 한 번만 실행
            this.isSitting = !this.isSitting;
            console.log(`🪑 ${this.isSitting ? '앉기' : '일어서기'} 시작`);
          }
          break;
      }
    });
    
    document.addEventListener('keyup', (event) => {
      switch(event.code) {
        case 'KeyW':
        case 'ArrowUp':
          this.moveForward = false;
          break;
        case 'KeyS':
        case 'ArrowDown':
          this.moveBackward = false;
          break;
        case 'KeyA':
        case 'ArrowLeft':
          this.moveLeft = false;
          break;
        case 'KeyD':
        case 'ArrowRight':
          this.moveRight = false;
          break;
      }
    });
  }

  onClick(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const intersects = this.raycaster.intersectObjects(this.meshes, true);
    if (intersects.length === 0) {
      return;
    }
    const target = intersects[0].object;
    const productData =
      (target.userData && target.userData.productData) ||
      (target.parent && target.parent.userData && target.parent.userData.productData);
    if (!productData || typeof window.openCheckoutModal !== "function") {
      return;
    }
    window.openCheckoutModal(productData);
  }

  onResize() {
    if (!this.container || !this.camera || !this.renderer) {
      console.error("[Showroom] ❌ onResize: 필수 객체 없음");
      return;
    }
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    console.log(`[Showroom] 📐 Resize: ${width}x${height}`);
    
    if (width <= 0 || height <= 0) {
      console.error(`[Showroom] ❌ 컨테이너 크기가 0입니다! (${width}x${height})`);
      return;
    }
    this.renderer.setSize(width, height);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    const elapsed = this.clock.getElapsedTime();

    // [1] FPS 카메라 회전 적용
    this.camera.rotation.y = this.yaw;
    this.camera.rotation.x = this.pitch;
    
    // [2] 이동 방향 계산 (카메라가 보는 방향 기준)
    const forward = new THREE.Vector3();
    forward.x = -Math.sin(this.yaw);
    forward.z = -Math.cos(this.yaw);
    forward.normalize();
    
    const right = new THREE.Vector3();
    right.x = Math.cos(this.yaw);
    right.z = -Math.sin(this.yaw);
    right.normalize();
    
    // [3] WASD 이동 (부드러운 velocity 기반 이동)
    const acceleration = new THREE.Vector3(0, 0, 0);
    
    if (this.moveForward) {
      acceleration.addScaledVector(forward, this.moveSpeed);
    }
    if (this.moveBackward) {
      acceleration.addScaledVector(forward, -this.moveSpeed);
    }
    if (this.moveLeft) {
      acceleration.addScaledVector(right, -this.moveSpeed);
    }
    if (this.moveRight) {
      acceleration.addScaledVector(right, this.moveSpeed);
    }
    
    // Velocity 업데이트 (부드러운 가속/감속)
    this.velocity.add(acceleration);
    this.velocity.multiplyScalar(this.velocityDamping); // 자연스러운 감속
    
    // 최대 속도 제한 (빠른 이동 방지)
    const currentSpeed = this.velocity.length();
    if (currentSpeed > this.maxVelocity) {
      this.velocity.normalize().multiplyScalar(this.maxVelocity);
    }
    
    // 카메라 위치 업데이트
    this.camera.position.add(this.velocity);
    
    // [4] 벽 충돌 검사 (연동 모듈에서 가져온 값 사용)
    if (this.wallLimitX && this.wallLimitZ) {
      this.camera.position.x = Math.max(-this.wallLimitX, Math.min(this.wallLimitX, this.camera.position.x));
      this.camera.position.z = Math.max(-this.wallLimitZ, Math.min(this.wallLimitZ, this.camera.position.z));
    } else {
      // Fallback (기존 값)
      const wallLimit = 13;
      this.camera.position.x = Math.max(-wallLimit, Math.min(wallLimit, this.camera.position.x));
      this.camera.position.z = Math.max(-wallLimit, Math.min(wallLimit, this.camera.position.z));
    }
    
    // [5] 앉기/일어서기 부드러운 전환 (인체 운동학 - Kinematics)
    const targetEyeLevel = this.isSitting ? this.sittingEyeLevel : this.standingEyeLevel;
    const eyeLevelDiff = targetEyeLevel - this.eyeLevel;
    
    // 부드러운 보간 (Smooth Interpolation) - 이질감 없는 자연스러운 움직임
    if (Math.abs(eyeLevelDiff) > 0.001) {
      this.eyeLevel += eyeLevelDiff * this.transitionSpeed;
    } else {
      this.eyeLevel = targetEyeLevel; // 목표 도달 시 정확한 값으로 설정
    }
    
    // [6] 눈높이 적용 (날아다니기 금지)
    this.camera.position.y = this.eyeLevel;

    // 연동 모듈 애니메이션 업데이트
    if (this.builder) {
      this.builder.updateChandelierAnimation();
    }
    if (this.factory) {
      this.factory.updateProductAnimations();
    }

    // 상품 애니메이션 (기존 로직 유지 - 호환성)
    this.standardCoins.forEach((group) => {
      group.rotation.y += 0.01;
    });

    // Premium 큐브: 외부 와이어프레임과 내부 큐브 반대 방향 회전
    this.premiumCubes.forEach(({ group, inner, offset }) => {
      const scale = 1 + Math.sin(elapsed * 2 + offset) * 0.05;
      group.scale.setScalar(scale);
      // 외부 그룹 회전 (느리게)
      group.rotation.y += 0.005;
      // 내부 큐브 반대 방향 빠른 회전
      if (inner) {
        inner.rotation.x -= 0.03; // 반대 방향, 빠르게
        inner.rotation.y -= 0.03;
        inner.rotation.z -= 0.03;
      }
    });

    // Gold 자이로스코프: 3개의 링이 각각 다른 방향으로 회전
    this.goldCrowns.forEach(({ group, ring1, ring2, ring3, core, particles }) => {
      // 전체 그룹 회전 (느리게)
      group.rotation.y += 0.002;
      
      // 각 링이 독립적으로 회전
      if (ring1) {
        ring1.rotation.y += 0.01; // 수평 링
        ring1.rotation.z += 0.005;
      }
      if (ring2) {
        ring2.rotation.x += 0.008; // 수직 링 1
        ring2.rotation.z += 0.01;
      }
      if (ring3) {
        ring3.rotation.x += 0.012; // 수직 링 2 (다른 속도)
        ring3.rotation.y += 0.006;
      }
      
      // 에너지 코어 회전
      if (core) {
        core.rotation.x += 0.02;
        core.rotation.y += 0.02;
      }
      
      // 파티클 회전
      if (particles) {
        particles.rotation.y += 0.02;
      }
    });

    // 샹들리에 고리 회전 (각각 다른 각도로 천천히)
    if (this.chandelierRings) {
      if (this.chandelierRings.ring1) {
        this.chandelierRings.ring1.rotation.y += 0.003; // 천천히 회전
        this.chandelierRings.ring1.rotation.z += 0.001;
      }
      if (this.chandelierRings.ring2) {
        this.chandelierRings.ring2.rotation.y += 0.004; // 다른 속도
        this.chandelierRings.ring2.rotation.x += 0.002;
      }
      if (this.chandelierRings.ring3) {
        this.chandelierRings.ring3.rotation.y += 0.005; // 더 빠른 속도
        this.chandelierRings.ring3.rotation.x += 0.001;
      }
    }

    // 렌더링
    this.renderer.render(this.scene, this.camera);
  }
}

window.Showroom = Showroom;

