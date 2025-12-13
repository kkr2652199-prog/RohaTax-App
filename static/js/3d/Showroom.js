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

    // window.SHOWROOM_DATA 우선 사용, 없으면 window.PRODUCT_DATA 사용 (하위 호환성)
    if (window.SHOWROOM_DATA) {
      console.log("✅ [Showroom] window.SHOWROOM_DATA 사용");
    } else if (window.PRODUCT_DATA && Array.isArray(window.PRODUCT_DATA)) {
      console.warn("⚠️ [Showroom] window.SHOWROOM_DATA가 없습니다. window.PRODUCT_DATA를 사용합니다.");
    } else {
      console.error(
        "[Showroom] window.SHOWROOM_DATA 또는 window.PRODUCT_DATA가 없습니다. 쇼룸이 렌더링되지 않습니다."
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
      powerPreference: "high-performance", // 고성능 모드
      // 🚀 성능 최적화: 렌더링 최적화 설정
      logarithmicDepthBuffer: false, // 로그 깊이 버퍼 비활성화 (성능 향상)
      precision: "highp" // 높은 정밀도 (필요시)
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // 🚀 2배율 제한으로 성능 향상
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap; // 🚀 PCFSoftShadowMap: 품질과 성능의 균형
    this.renderer.outputEncoding = THREE.sRGBEncoding; // 색상 인코딩 개선
    // 🚀 성능 최적화: 자동 정리 활성화 (메모리 관리)
    this.renderer.autoClear = true;
    this.renderer.sortObjects = true; // 객체 정렬 활성화 (투명도 처리 최적화)
    
    console.log(`[Showroom] 🎨 Renderer 생성: ${this.canvas.width}x${this.canvas.height}`);
    
    // ✅ CSS2DRenderer 초기화 (고해상도 HTML 라벨링용)
    try {
      const CSS2DRenderer = window.CSS2DRenderer || (typeof THREE !== 'undefined' && THREE.CSS2DRenderer);
      if (CSS2DRenderer) {
        this.css2dRenderer = new CSS2DRenderer();
        this.css2dRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.css2dRenderer.domElement.style.position = 'absolute';
        this.css2dRenderer.domElement.style.top = '0';
        this.css2dRenderer.domElement.style.left = '0';
        this.css2dRenderer.domElement.style.pointerEvents = 'none';
        this.css2dRenderer.domElement.style.zIndex = '1000';
        this.container.appendChild(this.css2dRenderer.domElement);
        console.log('✅ [Showroom] CSS2DRenderer 초기화 완료');
      } else {
        console.warn('⚠️ [Showroom] CSS2DRenderer를 사용할 수 없습니다.');
        this.css2dRenderer = null;
      }
    } catch (error) {
      console.error('❌ [Showroom] CSS2DRenderer 초기화 실패:', error);
      this.css2dRenderer = null;
    }
    
    // ✅ CSS3DRenderer 초기화 (3D 홀로그램 콘솔용)
    try {
      const CSS3DRenderer = window.CSS3DRenderer || (typeof THREE !== 'undefined' && THREE.CSS3DRenderer);
      if (CSS3DRenderer) {
        this.css3dRenderer = new CSS3DRenderer();
        this.css3dRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.css3dRenderer.domElement.style.position = 'absolute';
        this.css3dRenderer.domElement.style.top = '0';
        this.css3dRenderer.domElement.style.left = '0';
        this.css3dRenderer.domElement.style.pointerEvents = 'none';
        this.css3dRenderer.domElement.style.zIndex = '999';
        this.container.appendChild(this.css3dRenderer.domElement);
        console.log('✅ [Showroom] CSS3DRenderer 초기화 완료');
      } else {
        console.warn('⚠️ [Showroom] CSS3DRenderer를 사용할 수 없습니다.');
        this.css3dRenderer = null;
      }
    } catch (error) {
      console.error('❌ [Showroom] CSS3DRenderer 초기화 실패:', error);
      this.css3dRenderer = null;
    }

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
    
    // 🚀 성능 최적화: Frustum Culling 및 애니메이션 최적화
    this.frustum = new THREE.Frustum();
    this.cameraMatrix = new THREE.Matrix4();
    this.lastFrameTime = 0;
    this.frameCount = 0;
    this.fps = 60; // 목표 FPS
    this.animationUpdateInterval = 1; // 애니메이션 업데이트 간격 (프레임 단위)
    this.visibleObjects = new Set(); // 카메라에 보이는 객체 캐시
    this.frustumCullingEnabled = false; // Frustum Culling 비활성화 (안전장치 - 문제 발생 시 자동 비활성화)
    
    // 🚀 성능 최적화: 재사용 가능한 Vector3 객체 (매 프레임 생성 방지)
    this._tempForward = new THREE.Vector3();
    this._tempRight = new THREE.Vector3();
    this._tempAcceleration = new THREE.Vector3();

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
    
    // 샹들리에 삭제 (Commander 지시)
    // this.builder.createChandelier();

    // 진열대 위치 정의 (U자형 배치용)
    this.pedestalPositions = [
      new THREE.Vector3(0, 0, -6),        // 중앙: Gold
      new THREE.Vector3(-4, 0, -4.5),     // 좌측 중간: Standard
      new THREE.Vector3(4, 0, -4.5),      // 우측 중간: Premium
      new THREE.Vector3(-7, 0, -1),       // 좌측 끝: Event 1
      new THREE.Vector3(7, 0, -1)         // 우측 끝: Event 2
    ];

    // window.SHOWROOM_DATA에서 상품 데이터 추출
    if (window.SHOWROOM_DATA) {
      // regular_products와 event_products를 합쳐서 전체 상품 리스트 생성
      this.products = [
        ...(window.SHOWROOM_DATA.regular_products || []),
        ...(window.SHOWROOM_DATA.event_products || [])
      ];
      this.showroomData = window.SHOWROOM_DATA; // 전체 데이터 저장 (할인율 등)
      console.log(`✅ [Showroom] 상품 데이터 로드: 일반 ${window.SHOWROOM_DATA.regular_products?.length || 0}개, 이벤트 ${window.SHOWROOM_DATA.event_products?.length || 0}개`);
    } else if (window.PRODUCT_DATA && Array.isArray(window.PRODUCT_DATA)) {
      // 하위 호환성: window.PRODUCT_DATA 사용
      this.products = window.PRODUCT_DATA;
      this.showroomData = null;
      console.log(`⚠️ [Showroom] window.PRODUCT_DATA 사용 (하위 호환성): ${this.products.length}개`);
    } else {
      this.products = [];
      this.showroomData = null;
      console.error("❌ [Showroom] 상품 데이터를 찾을 수 없습니다.");
    }
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
    
    // 테스트: 보석상 스타일 유리 진열대 추가
    // ⚠️ 주석 처리: WebGL 텍스처 유닛 초과로 인한 검정 화면 문제 해결
    // JewelryDisplay 5개 생성 시 MeshPhysicalMaterial의 envMapIntensity 등으로 텍스처 유닛 16개 초과
    // this.addTestJewelryDisplay();
    
    this.setupEvents();
    this.onResize();
    window.addEventListener("resize", () => this.onResize());
    this.animate();
  }

  addLights() {
    // ✅ 얼룩 없는 부드러운 공간감: HemisphereLight 도입 (반구 조명)
    // 하늘색(Sky): 약간 푸른빛, 낮 느낌
    // 바닥색(Ground): 어두운 바닥 반사광
    const hemisphereLight = new THREE.HemisphereLight(
      0xddeeff,  // 하늘색 (Sky) - 약간 푸른빛
      0x0f0e0d,  // 바닥색 (Ground) - 어두운 바닥 반사광
      0.6        // 강도 (기존 AmbientLight보다 입체감 있음)
    );
    this.scene.add(hemisphereLight);

    // ✅ 보조 전역 조명: AmbientLight 강도 대폭 감소 (HemisphereLight가 주 조명)
    const ambient = new THREE.AmbientLight(0xffffff, 0.1); // 0.2 → 0.1 (아주 낮춤)
    this.scene.add(ambient);

    // ✅ 천장 유령 조명 삭제: areaLight1-4, ceilingLight 제거됨 (가구 조명만 사용)
    // ✅ 벽면 PointLight 삭제됨: 얼룩 반사 제거 (HemisphereLight로 대체)
    // 가구 조명(상품 스포트라이트 등)은 addProductSpotlight에서 생성되므로 유지됨
  }
  
  addProductSpotlight(position, color) {
    // 진열대 위에서 상품을 비추는 핀 조명 (블랙 & 화이트 모던 라운지)
    // ✅ 핀포인트 조명: 강도 50% 축소 (25.0 -> 12.0), 조사 각도 축소 (30도 -> 20도)
    // 바닥 반사 최소화: 좁은 각도로 상품만 정확히 조명, 바닥에 과도한 반사 방지
    // ✅ 물리법칙 준수: 역제곱 감쇠 법칙 (decay: 2) 적용
    // ✅ 부드러운 빛 확산: penumbra 0.5 (가장자리 흐림, 바닥에 칼같은 자국 방지)
    const spotlight = new THREE.SpotLight(color, 12.0, 30, Math.PI / 9, 0.5, 2);
    spotlight.position.set(position.x, position.y + 4, position.z); // 진열대 위에서 비춤
    
    // Target을 별도 Object3D로 생성하여 scene에 추가
    const target = new THREE.Object3D();
    target.position.set(position.x, position.y, position.z);
    this.scene.add(target);
    spotlight.target = target;
    
    // ✅ 물리법칙 준수: 상품은 그림자가 있어야 함 (리얼리티 확보)
    spotlight.castShadow = true;
    // 그림자 품질 설정: 1024x1024 (512는 너무 거칠고 2048은 무거움. 타협점)
    spotlight.shadow.mapSize.width = 1024;
    spotlight.shadow.mapSize.height = 1024;
    spotlight.shadow.camera.near = 0.1;
    spotlight.shadow.camera.far = 50;
    spotlight.shadow.bias = -0.0001; // 그림자 아티팩트 방지
    
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
    const floorTexture = ShowroomBuilder.createMarbleTexture();
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

  // createChandelier() 메서드 삭제됨 (Commander 지시)

  layoutProducts() {
    // window.SHOWROOM_DATA에서 직접 상품 데이터 가져오기
    let eventProducts = [];
    let regularProducts = [];
    
    if (this.showroomData) {
      // window.SHOWROOM_DATA 사용
      eventProducts = this.showroomData.event_products || [];
      regularProducts = this.showroomData.regular_products || [];
      console.log(`💎 [Showroom] 프라이빗 보석함 배치 시작: 일반 ${regularProducts.length}개, 이벤트 ${eventProducts.length}개`);
    } else {
      // 하위 호환성: this.products에서 필터링
      eventProducts = this.products.filter(p => p.type === 'event' || p.type === 'event_period');
      regularProducts = this.products.filter(p => p.type !== 'event' && p.type !== 'event_period');
      console.log(`💎 [Showroom] 프라이빗 보석함 배치 시작: 일반 ${regularProducts.length}개, 이벤트 ${eventProducts.length}개`);
    }
    
    if (regularProducts.length === 0 && eventProducts.length === 0) {
      console.warn("⚠️ [Showroom] 상품이 없습니다.");
      return;
    }

    // 상품 찾기
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

    // [1] 중앙 - Gold 상품 (왕관) - 제거됨 (LuxeDisplay3D 5번째 다이로 이동)
    // [2] 좌측 중간 - Standard 상품 (코인) - 제거됨 (LuxeDisplay3D 3번째 다이로 이동)
    // [3] 우측 중간 - Premium 상품 (큐브) - 제거됨 (LuxeDisplay3D 4번째 다이로 이동)
    // 기존 진열대는 유지하되 상품은 배치하지 않음 (LuxeDisplay3D 진열대에 배치)

    // [4] 좌측 끝 - Event 상품 1 (선물 상자) - 제거됨
    // 무료 상품은 이제 LuxeDisplay3D 진열대의 원형 다이 위에만 배치됩니다.
    // 기존 진열대는 유지하되 상품은 배치하지 않음
    
    // [5] 우측 끝 - Event 상품 2 (선물 상자) - 제거됨
    // 무료 상품은 이제 LuxeDisplay3D 진열대의 원형 다이 위에만 배치됩니다.
    // 기존 진열대는 유지하되 상품은 배치하지 않음

    // [6] 정면 벽 - TV 전시 (정면 벽에 붙여서 배치) - 대폭 확대된 TV
    // 정면 벽 위치: z = 15.5, TV를 벽에 붙이기 위해 z = 15.0에 배치
    // TV 높이: 3.15m (대폭 확대), 중심 기준이므로 Y = 7.075 정도 (바닥 방향으로 조금 내림)
    if (typeof window.TV3D !== 'undefined') {
      const tvPosition = new THREE.Vector3(0, 6.575, 15.0); // 정면 벽 중앙에 배치 (천장 방향으로 조금 더 올림, 6.075 → 6.575)
      console.log(`   [정면 벽] "TV" → (${tvPosition.x}, ${tvPosition.y}, ${tvPosition.z})`);
      
      // TV 생성 (재생 상태로 설정)
      const tvGroup = window.TV3D.createModel(null, tvPosition, true);
      if (tvGroup) {
        // TV를 사운드바 기준으로 180도 회전 (Y축 회전)
        tvGroup.rotation.y = Math.PI; // 180도 회전
        this.meshes.push(tvGroup);
        this.scene.add(tvGroup);
        // TV 조명 추가 (부드러운 조명)
        this.addProductSpotlight(tvPosition, 0xffffff); // 화이트 조명
        console.log(`   ✅ [정면 벽] TV 전시 완료 (180도 회전)`);
      }
    } else {
      console.warn(`   ⚠️ [정면 벽] TV3D 클래스를 찾을 수 없습니다.`);
    }

    // [7] 뒷벽 - LuxeDisplay3D 진열대 전시 (TV 반대편 벽)
    // TV 위치: z=15.0 (정면 벽)
    // 쇼룸 깊이: 30 (z=-15 ~ z=15)
    // 뒷벽: z=-15
    // 진열대 폭: 21, 폭의 반: 10.5
    // 진열대 z 위치: 벽쪽으로 조금 이동 (-4.5 → -6.5)
    if (typeof window.LuxeDisplay3D !== 'undefined' && typeof window.ProductFactory !== 'undefined') {
      const showcaseWidth = 21;
      const showcaseHalfWidth = showcaseWidth / 2; // 10.5
      const backWallZ = -15; // 뒷벽 위치
      const luxeDisplayPosition = new THREE.Vector3(0, 0, backWallZ + showcaseHalfWidth - 6); // z = -10.5 (벽쪽으로 6만큼 이동)
      console.log(`   [뒷벽] "LuxeDisplay3D" → (${luxeDisplayPosition.x}, ${luxeDisplayPosition.y}, ${luxeDisplayPosition.z})`);
      
      // ⚠️ 중요: this.factory를 사용하여 상품이 애니메이션 배열에 추가되도록 함
      const productData = { name: 'LuxeDisplay3D', price: 0 };
      const luxeDisplayGroup = this.factory.createLuxeDisplay3D(productData, luxeDisplayPosition);
      
      if (luxeDisplayGroup) {
        this.meshes.push(luxeDisplayGroup);
        console.log(`   ✅ [뒷벽] LuxeDisplay3D 진열대 전시 완료`);
        
        // 무료 상품 2종을 진열대 원형 다이 위에 올리기
        // LuxeDisplay3D의 원형 다이 위치 계산 (로컬 좌표계 기준)
        const showcaseHeight = 1.4; // 진열대 높이
        const innerWidth = showcaseWidth - 3; // 18
        const spacing = innerWidth / (5 - 1); // 4.5 (5개 원형 다이 간격)
        const jewelryBoxHeight = 0.25; // 원형 다이 높이
        // 원형 다이 중심 높이: showcaseHeight/2(0.7) + showcaseHeight/2(0.7) + jewelryBoxHeight/2(0.125) = 1.525
        const jewelryBoxCenterY = showcaseHeight / 2 + showcaseHeight / 2 + jewelryBoxHeight / 2; // 1.525
        // 원형 다이 윗면 높이: 중심 + 높이/2 = 1.525 + 0.125 = 1.65 (물리 법칙: 상자 밑면이 여기에 붙음)
        const jewelryBoxTopY = jewelryBoxCenterY + jewelryBoxHeight / 2; // 1.65
        
        // 무료 상품 2종을 첫 번째와 두 번째 원형 다이 위에 올리기
        // GiftBox 높이 계산 (boxHeight 0.9 + lidHeight 0.3 = 1.2, 스케일 0.9 적용)
        const giftBoxHeight = 1.2 * 0.9; // 1.08m
        const giftBoxHalfHeight = giftBoxHeight / 2; // 0.54m
        
        if (eventProducts.length >= 2) {
          // 첫 번째 원형 다이 위치 (인덱스 0)
          const firstBoxX = -innerWidth / 2 + (0 * spacing); // -9
          // 물리 법칙: 상자 밑면이 원형 다이 윗면에 1:1로 붙어야 함
          // createEventProduct에서 wrapperGroup.position.y가 상자의 바닥면이 되도록 설정됨
          // (giftBoxGroup.position.y = 0이므로 상자 중심이 wrapperGroup 중심과 같고,
          //  상자 바닥면 = position.y - giftBoxHalfHeight가 되지만,
          //  주석에 "GiftBox의 바닥면이 그룹의 position.y에 오도록"이라고 되어 있으므로
          //  실제로는 position.y가 상자 바닥면이 되어야 함)
          const firstBoxPosition = new THREE.Vector3(
            luxeDisplayPosition.x + firstBoxX,
            luxeDisplayPosition.y + jewelryBoxTopY, // 원형 다이 윗면 높이 = 상자 바닥면 높이 (1:1 붙음)
            luxeDisplayPosition.z
          );
          
          // 두 번째 원형 다이 위치 (인덱스 1)
          const secondBoxX = -innerWidth / 2 + (1 * spacing); // -4.5
          // 물리 법칙: 상자 밑면이 원형 다이 윗면에 1:1로 붙어야 함
          // createEventProduct에서 wrapperGroup.position.y가 상자의 바닥면이 되도록 설정됨
          const secondBoxPosition = new THREE.Vector3(
            luxeDisplayPosition.x + secondBoxX,
            luxeDisplayPosition.y + jewelryBoxTopY, // 원형 다이 윗면 높이 = 상자 바닥면 높이 (1:1 붙음)
            luxeDisplayPosition.z
          );
          
          console.log(`   [뒷벽] 무료 상품 1 "${eventProducts[0].name}" → (${firstBoxPosition.x.toFixed(2)}, ${firstBoxPosition.y.toFixed(2)}, ${firstBoxPosition.z.toFixed(2)})`);
          const firstEventProduct = this.factory.createEventProduct(eventProducts[0], firstBoxPosition);
          if (firstEventProduct) {
            this.meshes.push(firstEventProduct);
            console.log(`   ✅ [뒷벽] 무료 상품 1 전시 완료`);
          }
          
          console.log(`   [뒷벽] 무료 상품 2 "${eventProducts[1].name}" → (${secondBoxPosition.x.toFixed(2)}, ${secondBoxPosition.y.toFixed(2)}, ${secondBoxPosition.z.toFixed(2)})`);
          const secondEventProduct = this.factory.createEventProduct(eventProducts[1], secondBoxPosition);
          if (secondEventProduct) {
            this.meshes.push(secondEventProduct);
            console.log(`   ✅ [뒷벽] 무료 상품 2 전시 완료`);
          }
          
          // [3] 3번째 원형 다이 - 토큰 상품 (Standard Coin)
          if (standard) {
            const thirdBoxX = -innerWidth / 2 + (2 * spacing); // 0 (3번째 다이)
            // Standard Coin: coin.position.y = 0.6이므로, 그룹의 position.y = jewelryBoxTopY + 0.6
            // 상품의 바닥면이 원형 다이 윗면에 붙도록: position.y = jewelryBoxTopY + 0.6
            const thirdBoxPosition = new THREE.Vector3(
              luxeDisplayPosition.x + thirdBoxX,
              luxeDisplayPosition.y + jewelryBoxTopY + 0.6, // 원형 다이 윗면 + 코인 반지름
              luxeDisplayPosition.z
            );
            console.log(`   [뒷벽] 토큰 상품 "${standard.name}" → (${thirdBoxPosition.x.toFixed(2)}, ${thirdBoxPosition.y.toFixed(2)}, ${thirdBoxPosition.z.toFixed(2)})`);
            const standardProduct = this.factory.createRegularProduct(standard, thirdBoxPosition);
            if (standardProduct) {
              this.meshes.push(standardProduct);
              this.scene.add(standardProduct);
              this.addProductSpotlight(thirdBoxPosition, 0xc0c0c0); // 실버 조명
              console.log(`   ✅ [뒷벽] 토큰 상품 전시 완료`);
            }
          }
          
          // [4] 4번째 원형 다이 - 프리미엄 상품 (Premium Cube)
          if (premium) {
            const fourthBoxX = -innerWidth / 2 + (3 * spacing); // 4.5 (4번째 다이)
            // Premium Cube: lines.position.y = 0.6이므로, 그룹의 position.y = jewelryBoxTopY + 0.6
            // 상품의 바닥면이 원형 다이 윗면에 붙도록: position.y = jewelryBoxTopY + 0.6
            const fourthBoxPosition = new THREE.Vector3(
              luxeDisplayPosition.x + fourthBoxX,
              luxeDisplayPosition.y + jewelryBoxTopY + 0.6, // 원형 다이 윗면 + 큐브 반 높이
              luxeDisplayPosition.z
            );
            console.log(`   [뒷벽] 프리미엄 상품 "${premium.name}" → (${fourthBoxPosition.x.toFixed(2)}, ${fourthBoxPosition.y.toFixed(2)}, ${fourthBoxPosition.z.toFixed(2)})`);
            const premiumProduct = this.factory.createRegularProduct(premium, fourthBoxPosition);
            if (premiumProduct) {
              this.meshes.push(premiumProduct);
              this.scene.add(premiumProduct);
              this.addProductSpotlight(fourthBoxPosition, 0x00bfff); // 블루 조명
              console.log(`   ✅ [뒷벽] 프리미엄 상품 전시 완료`);
            }
          }
          
          // [5] 5번째 원형 다이 - 골드 상품 (Gold Crown)
          if (gold) {
            const fifthBoxX = -innerWidth / 2 + (4 * spacing); // 9 (5번째 다이)
            // Gold Crown: ring.position.y = 0.6이므로, 그룹의 position.y = jewelryBoxTopY + 0.6
            // 상품의 바닥면이 원형 다이 윗면에 붙도록: position.y = jewelryBoxTopY + 0.6
            const fifthBoxPosition = new THREE.Vector3(
              luxeDisplayPosition.x + fifthBoxX,
              luxeDisplayPosition.y + jewelryBoxTopY + 0.6, // 원형 다이 윗면 + 링 반지름
              luxeDisplayPosition.z
            );
            console.log(`   [뒷벽] 골드 상품 "${gold.name}" → (${fifthBoxPosition.x.toFixed(2)}, ${fifthBoxPosition.y.toFixed(2)}, ${fifthBoxPosition.z.toFixed(2)})`);
            const goldProduct = this.factory.createRegularProduct(gold, fifthBoxPosition);
            if (goldProduct) {
              this.meshes.push(goldProduct);
              this.scene.add(goldProduct);
              this.addProductSpotlight(fifthBoxPosition, 0xffd700); // 골드 조명
              console.log(`   ✅ [뒷벽] 골드 상품 전시 완료`);
            }
          }
        } else {
          console.warn(`   ⚠️ [뒷벽] 무료 상품이 2개 미만입니다. (현재: ${eventProducts.length}개)`);
        }
      } else {
        console.warn(`   ⚠️ [뒷벽] LuxeDisplay3D 생성 실패`);
      }
    } else {
      console.warn(`   ⚠️ [뒷벽] LuxeDisplay3D 또는 ProductFactory 클래스를 찾을 수 없습니다.`);
    }

    console.log(`✅ [Showroom] 총 ${this.meshes.length}개 상품 배치 완료`);
  }

  /**
   * 테스트: 보석상 스타일 유리 진열대 추가
   */
  /**
   * 쇼룸에 진열대 배치 (배치만 담당 - 디자인은 JewelryDisplay.js에서)
   * 
   * 💡 아키텍처 원칙:
   * - 쇼룸은 "진열만 하는 공간" (가구 생성/디자인 X)
   * - 가구 디자인은 별도 테스트 파일(/test/jewelry-display)에서 작업
   * - 워크플로우: 테스트 파일에서 디자인 → 확인 → 완성되면 쇼룸에 배치만 추가
   */
  addTestJewelryDisplay() {
    console.log("💎 [Showroom] 진열대 배치 시작 (배치만 담당)...");
    
    if (typeof window.JewelryDisplay === "undefined") {
      console.error("❌ [Showroom] JewelryDisplay 클래스를 찾을 수 없습니다!");
      console.error("   - JewelryDisplay.js 파일이 로드되었는지 확인하세요.");
      console.error("   - 디자인 테스트: /test/jewelry-display 페이지에서 확인하세요.");
      return;
    }

    if (typeof THREE === "undefined") {
      console.error("❌ [Showroom] THREE.js가 로드되지 않았습니다!");
      return;
    }

    // 진열대 크기 (JewelryDisplay.js에서 정의된 디자인 사용)
    const displaySize = { width: 2.5, height: 1.8, depth: 2 };
    
    // 방 크기 고려한 간격 계산 (벽 안쪽에 안전하게 배치)
    const safeLimit = 14.0; // 안전한 최대 위치 (벽 안쪽 1m 여유)
    const displayHalfWidth = displaySize.width / 2; // 1.25m
    const maxPosition = safeLimit - displayHalfWidth; // 14.0 - 1.25 = 12.75
    
    // 5개를 일정한 간격으로 배치: 중앙 기준 좌우 대칭
    const spacing = (maxPosition * 2) / 4; // 약 6.375m
    
    // 5개 진열대 배치 (배치만 담당)
    const positions = [
      { x: -spacing * 2, y: 0, z: 5, name: "좌측 끝" },
      { x: -spacing, y: 0, z: 5, name: "좌측 중간" },
      { x: 0, y: 0, z: 5, name: "중앙" },
      { x: spacing, y: 0, z: 5, name: "우측 중간" },
      { x: spacing * 2, y: 0, z: 5, name: "우측 끝" }
    ];
    
    positions.forEach((pos, index) => {
      try {
        const display = new window.JewelryDisplay(
          this.scene,
          { x: pos.x, y: pos.y, z: pos.z },
          displaySize
        );
        display.create();
        console.log(`   ✅ 진열대 ${index + 1} (${pos.name}) 배치 완료: x=${pos.x.toFixed(2)}`);
      } catch (error) {
        console.error(`   ❌ 진열대 ${index + 1} (${pos.name}) 배치 실패:`, error);
      }
    });

    console.log("✅ [Showroom] 진열대 배치 완료 (총 5개)");
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
    
    // ✅ 메뉴판 클릭 감지 (우선 처리)
    const menuIntersects = this.raycaster.intersectObjects(this.scene.children, true);
    for (const intersect of menuIntersects) {
      if (intersect.object.userData && intersect.object.userData.isMenu) {
        const menuMesh = intersect.object;
        const productData = menuMesh.userData.productData;
        
        if (!productData) {
          console.warn("⚠️ [Showroom] 메뉴판에 상품 데이터가 없습니다.");
          continue;
        }
        
        // ✅ 앞면(Material Index 4)만 클릭 허용 (BoxGeometry: 인덱스 4=앞면)
        if (intersect.face && intersect.face.materialIndex !== 4) {
          console.log('ℹ️ [Showroom] 메뉴판 뒷면/옆면 클릭됨 (무시, materialIndex:', intersect.face.materialIndex, ')');
          continue; // 앞면이 아니면 무시
        }
        
        // ✅ 버튼 영역 UV 좌표 확인
        const uv = intersect.uv;
        
        // 디버깅: UV 좌표 출력
        console.log('🔍 [Showroom] 클릭된 UV 좌표:', {
          x: uv.x,
          y: uv.y,
          productName: productData.name || 'Unknown'
        });
        
        // 버튼은 Canvas 하단에 그려졌으므로, UV y 좌표가 0에 가까울수록 하단
        // 4K 해상도(1024x700) 기준, 버튼은 하단 100px 영역 (700-100 ~ 700)
        // UV 좌표계에서 y=0이 하단이므로, y < (100/700) = 0.143
        const isButtonClick = uv.y < 0.15; // 하단 15% 영역 (버튼 영역)
        
        if (isButtonClick) {
          console.log('✅ [Showroom] 메뉴판 버튼 클릭됨:', productData.name || 'Unknown');
          
          // 가상 버튼 생성 및 openCheckoutModal 호출
          this._handleMenuButtonClick(productData);
          return; // 메뉴판 클릭 처리 완료
        } else {
          console.log('ℹ️ [Showroom] 메뉴판 클릭됨 (버튼 영역 아님, UV y:', uv.y, ')');
          return; // 메뉴판이지만 버튼이 아니면 무시
        }
      }
    }
    
    // ✅ 기존 상품 클릭 처리 (메뉴판이 아닌 경우)
    const intersects = this.raycaster.intersectObjects(this.meshes, true);
    if (intersects.length === 0) {
      return;
    }
    
    // 클릭된 객체에서 productData 찾기 (재귀적으로 부모 그룹까지 탐색)
    let target = intersects[0].object;
    let productData = null;
    
    while (target && !productData) {
      if (target.userData && target.userData.productData) {
        productData = target.userData.productData;
        break;
      }
      target = target.parent;
    }
    
    if (!productData) {
      console.log("⚠️ [Showroom] 클릭된 객체에 상품 데이터가 없습니다.");
      return;
    }
    
    if (typeof window.openCheckoutModal !== "function") {
      console.error("❌ [Showroom] window.openCheckoutModal 함수를 찾을 수 없습니다.");
      return;
    }
    
    // 🔍 디버깅: productData 전체 구조 확인
    console.log(`🔍 [Showroom] 상품 데이터 전체:`, productData);
    
    // ⚠️ 치명적: product_id 필수 오류 방지 - ID 강제 주입
    if (!productData.id && productData.id !== 0) {
      console.error("❌ [Showroom] productData.id가 없습니다! productData:", productData);
      // product_id도 확인 (혹시 다른 필드명을 사용하는 경우)
      if (productData.product_id !== undefined) {
        console.warn("⚠️ [Showroom] product_id 필드를 id로 매핑합니다.");
        productData.id = productData.product_id;
      } else {
        console.error("❌ [Showroom] product_id도 없습니다. 결제 모달을 열 수 없습니다.");
        return;
      }
    }
    
    // 이벤트 상품 여부 확인 (shop.js와 동일한 로직)
    // ⚠️ 중요: productData.type이 null/undefined일 경우를 대비하여 빈 문자열로 처리
    const productTypeRaw = (productData.type || '').trim();
    const productType = productTypeRaw.toLowerCase();
    const isEventType = productType === 'event' || productType === 'event_period';
    
    // 디버깅: productData.type 값 확인
    console.log(`🔍 [Showroom] 상품 타입 확인:`, {
      name: productData.name,
      id: productData.id,
      type: productData.type,
      rawType: productTypeRaw,
      normalizedType: productType,
      isEventType: isEventType
    });
    
    // 가상 버튼 생성 (shop.js의 openCheckoutModal이 버튼 엘리먼트를 기대함)
    const virtualButton = document.createElement('button');
    
    // ⚠️ 치명적 수정 1: data-id 강제 주입 (product_id 필수 오류 방지)
    virtualButton.setAttribute('data-id', String(productData.id));
    console.log(`✅ [Showroom] data-id 설정: ${productData.id}`);
    
    virtualButton.setAttribute('data-name', productData.name || '');
    
    // ⚠️ 치명적 수정 2: 이벤트 상품은 data-price를 무조건 문자열 "0"으로 설정
    if (isEventType) {
      virtualButton.setAttribute('data-price', '0'); // 이벤트 상품은 무조건 0원 (문자열)
      console.log(`🎁 [Showroom] 이벤트 상품 클릭: ${productData.name} (가격: 0원, 타입: ${productTypeRaw})`);
    } else {
      virtualButton.setAttribute('data-price', String(productData.price || 0)); // 유료 상품은 실제 가격 (문자열로 변환)
      console.log(`🛒 [Showroom] 유료 상품 클릭: ${productData.name} (${productData.price?.toLocaleString()}원, 타입: ${productTypeRaw})`);
    }
    
    // ⚠️ 치명적 수정 3: data-type 강제 주입 (shop.js가 인식할 수 있는 값으로 매핑)
    // shop.js는 currentProduct.type === 'event' || currentProduct.type === 'event_period'를 확인
    // 원본 값을 그대로 전달하되, 공백만 제거하고 대소문자는 유지
    if (isEventType) {
      // 이벤트 타입인 경우, 원본 값을 그대로 전달 (공백만 제거)
      // 'event' 또는 'event_period' 둘 다 shop.js가 인식하므로 원본 유지
      virtualButton.setAttribute('data-type', productTypeRaw || (productType === 'event_period' ? 'event_period' : 'event'));
    } else {
      // 일반 상품인 경우, 원본 값을 그대로 전달 (공백만 제거)
      virtualButton.setAttribute('data-type', productTypeRaw || '');
    }
    
    virtualButton.setAttribute('data-token', String(productData.token_amount || 0));
    virtualButton.setAttribute('data-duration', String(productData.duration_days || 0));
    
    // 🔍 최종 확인: 가상 버튼의 모든 속성 로그
    console.log(`✅ [Showroom] 가상 버튼 속성:`, {
      'data-id': virtualButton.getAttribute('data-id'),
      'data-name': virtualButton.getAttribute('data-name'),
      'data-price': virtualButton.getAttribute('data-price'),
      'data-type': virtualButton.getAttribute('data-type'),
      'data-token': virtualButton.getAttribute('data-token'),
      'data-duration': virtualButton.getAttribute('data-duration')
    });
    
    // shop.js의 openCheckoutModal 호출
    window.openCheckoutModal(virtualButton);
  }
  
  /**
   * 메뉴판 버튼 클릭 처리 (내부 메서드)
   * @param {Object} productData - 상품 데이터
   */
  _handleMenuButtonClick(productData) {
    if (typeof window.openCheckoutModal !== "function") {
      console.error("❌ [Showroom] window.openCheckoutModal 함수를 찾을 수 없습니다.");
      return;
    }
    
    // 이벤트 상품 여부 확인
    const productTypeRaw = (productData.type || '').trim();
    const productType = productTypeRaw.toLowerCase();
    const isEventType = productType === 'event' || productType === 'event_period';
    
    // 가상 버튼 생성 (shop.js의 openCheckoutModal이 버튼 엘리먼트를 기대함)
    const virtualButton = document.createElement('button');
    
    // 필수 데이터 속성 주입
    virtualButton.setAttribute('data-id', String(productData.id || productData.product_id || ''));
    virtualButton.setAttribute('data-name', productData.name || '');
    
    // 가격 설정 (이벤트 상품은 "0")
    if (isEventType) {
      virtualButton.setAttribute('data-price', '0');
    } else {
      virtualButton.setAttribute('data-price', String(productData.price || 0));
    }
    
    // 타입 설정
    if (isEventType) {
      virtualButton.setAttribute('data-type', productTypeRaw || (productType === 'event_period' ? 'event_period' : 'event'));
    } else {
      virtualButton.setAttribute('data-type', productTypeRaw || '');
    }
    
    virtualButton.setAttribute('data-token', String(productData.token_amount || 0));
    virtualButton.setAttribute('data-duration', String(productData.duration_days || 0));
    
    console.log('✅ [Showroom] 메뉴판 버튼 클릭 처리:', {
      id: virtualButton.getAttribute('data-id'),
      name: virtualButton.getAttribute('data-name'),
      price: virtualButton.getAttribute('data-price'),
      type: virtualButton.getAttribute('data-type')
    });
    
    // shop.js의 openCheckoutModal 호출
    window.openCheckoutModal(virtualButton);
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
    
    // ✅ CSS2DRenderer 리사이즈
    if (this.css2dRenderer) {
      this.css2dRenderer.setSize(width, height);
    }
    
    // ✅ CSS3DRenderer 리사이즈
    if (this.css3dRenderer) {
      this.css3dRenderer.setSize(width, height);
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    const currentTime = performance.now();
    const deltaTime = currentTime - this.lastFrameTime;
    this.lastFrameTime = currentTime;
    
    // 🚀 성능 최적화: FPS 계산 및 자동 조절
    this.frameCount++;
    if (this.frameCount % 60 === 0) {
      const actualFps = 1000 / (deltaTime || 16.67);
      this.fps = actualFps;
      
      // 프레임 드롭 시 애니메이션 업데이트 빈도 자동 조절
      if (actualFps < 30) {
        this.animationUpdateInterval = Math.min(3, this.animationUpdateInterval + 1);
      } else if (actualFps > 55 && this.animationUpdateInterval > 1) {
        this.animationUpdateInterval = Math.max(1, this.animationUpdateInterval - 1);
      }
    }
    
    const elapsed = this.clock.getElapsedTime();
    const shouldUpdateAnimations = this.frameCount % this.animationUpdateInterval === 0;

    // [1] FPS 카메라 회전 적용
    this.camera.rotation.y = this.yaw;
    this.camera.rotation.x = this.pitch;
    
    // [2] 이동 방향 계산 (카메라가 보는 방향 기준) - 🚀 재사용 가능한 객체 사용
    this._tempForward.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw)).normalize();
    this._tempRight.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw)).normalize();
    
    // [3] WASD 이동 (부드러운 velocity 기반 이동) - 🚀 재사용 가능한 객체 사용
    this._tempAcceleration.set(0, 0, 0);
    
    if (this.moveForward) {
      this._tempAcceleration.addScaledVector(this._tempForward, this.moveSpeed);
    }
    if (this.moveBackward) {
      this._tempAcceleration.addScaledVector(this._tempForward, -this.moveSpeed);
    }
    if (this.moveLeft) {
      this._tempAcceleration.addScaledVector(this._tempRight, -this.moveSpeed);
    }
    if (this.moveRight) {
      this._tempAcceleration.addScaledVector(this._tempRight, this.moveSpeed);
    }
    
    // Velocity 업데이트 (부드러운 가속/감속)
    this.velocity.add(this._tempAcceleration);
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
    
    // 카메라 행렬 업데이트 (Frustum Culling을 위해 필수)
    this.camera.updateMatrixWorld();

    // 🚀 성능 최적화: Frustum Culling - 카메라에 보이는 객체만 업데이트
    // ⚠️ 안전장치: Frustum Culling이 실패할 경우를 대비해 try-catch 추가
    try {
      this.cameraMatrix.multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse);
      this.frustum.setFromProjectionMatrix(this.cameraMatrix);
      this.visibleObjects.clear();
    } catch (error) {
      console.warn("[Showroom] Frustum Culling 계산 오류, 모든 객체 업데이트:", error);
      // Frustum Culling 실패 시 모든 객체를 보이는 것으로 간주
      this.visibleObjects.clear();
    }
    
    // 🚀 성능 최적화: 연동 모듈 애니메이션 업데이트 (프레임 드롭 시 빈도 조절)
    // 샹들리에 애니메이션 삭제 (Commander 지시)
    if (this.factory && shouldUpdateAnimations) {
      // 🚀 성능 최적화: Frustum Culling 적용 - 보이는 객체만 업데이트
      // ⚠️ 안전장치: Frustum Culling이 모든 객체를 필터링하는 경우를 방지
      let visibleCount = 0;
      
      // Standard Coin 회전 애니메이션
      if (this.factory.standardCoins) {
        this.factory.standardCoins.forEach((group) => {
          if (group && group.rotation) {
            // Frustum Culling: 카메라에 보이는 객체만 업데이트
            // ⚠️ 안전장치: Frustum Culling 비활성화 시 모든 객체 업데이트
            const isVisible = this.frustumCullingEnabled && this.frustum.intersectsObject ? this.frustum.intersectsObject(group) : true;
            if (isVisible) {
              group.rotation.y += 0.01;
              this.visibleObjects.add(group);
              visibleCount++;
            }
          }
        });
      }
      
      // Premium 큐브: 외부 와이어프레임과 내부 큐브 반대 방향 회전
      if (this.factory.premiumCubes) {
        this.factory.premiumCubes.forEach((cube) => {
          if (cube && cube.group) {
            // Frustum Culling: 카메라에 보이는 객체만 업데이트
            const isVisible = this.frustumCullingEnabled && this.frustum.intersectsObject ? this.frustum.intersectsObject(cube.group) : true;
            if (isVisible) {
              const scale = 1 + Math.sin(elapsed * 2 + (cube.offset || 0)) * 0.05;
              cube.group.scale.setScalar(scale);
              // 내부 큐브 반대 방향 빠른 회전
              if (cube.inner) {
                cube.inner.rotation.x -= 0.03; // 반대 방향, 빠르게
                cube.inner.rotation.y -= 0.03;
                cube.inner.rotation.z -= 0.03;
              }
              this.visibleObjects.add(cube.group);
              visibleCount++;
            }
          }
        });
      }
      
      // Gold 자이로스코프: 3개의 링이 각각 다른 방향으로 회전
      if (this.factory.goldCrowns) {
        this.factory.goldCrowns.forEach((crown) => {
          if (crown && crown.group) {
            // Frustum Culling: 카메라에 보이는 객체만 업데이트
            const isVisible = this.frustumCullingEnabled && this.frustum.intersectsObject ? this.frustum.intersectsObject(crown.group) : true;
            if (isVisible) {
              // 전체 그룹 회전 (느리게)
              crown.group.rotation.y += 0.002;
              
              // 각 링이 독립적으로 회전
              if (crown.ring1) {
                crown.ring1.rotation.y += 0.01; // 수평 링
                crown.ring1.rotation.z += 0.005;
              }
              if (crown.ring2) {
                crown.ring2.rotation.x += 0.008; // 수직 링 1
                crown.ring2.rotation.z += 0.01;
              }
              if (crown.ring3) {
                crown.ring3.rotation.x += 0.012; // 수직 링 2 (다른 속도)
                crown.ring3.rotation.y += 0.006;
              }
              
              // 에너지 코어 회전
              if (crown.core) {
                crown.core.rotation.x += 0.02;
                crown.core.rotation.y += 0.02;
              }
              
              // 파티클 회전
              if (crown.particles) {
                crown.particles.rotation.y += 0.02;
              }
              this.visibleObjects.add(crown.group);
              visibleCount++;
            }
          }
        });
      }
      
      // ⚠️ 안전장치: 모든 객체가 필터링된 경우 경고 및 Frustum Culling 비활성화
      if (visibleCount === 0 && (this.factory.standardCoins?.length > 0 || this.factory.premiumCubes?.length > 0 || this.factory.goldCrowns?.length > 0)) {
        console.warn("[Showroom] ⚠️ Frustum Culling이 모든 객체를 필터링했습니다. Frustum Culling을 일시적으로 비활성화합니다.");
        // 다음 프레임부터 Frustum Culling 비활성화
        this.frustumCullingEnabled = false;
      }
    }

    // 샹들리에 애니메이션 삭제됨 (Commander 지시)

    // [Arc Reactor 애니메이션] 중앙 조명 발광 코어 회전 및 빛의 기둥 펄스
    // 🚀 성능 최적화: 회전 애니메이션 제거 (프레임 드랍 해결)
    // ⚠️ 주석 처리: scene.traverse()가 매 프레임 실행되어 렌더링 부하 발생
    // if (shouldUpdateAnimations) {
    //   this.scene.traverse((obj) => {
    //     // 발광 코어 링 회전 (서로 반대 방향)
    //     if (obj.userData.isArcReactorCore && obj.userData.rotationSpeed) {
    //       // Frustum Culling: 카메라에 보이는 객체만 업데이트
    //       const isVisible = this.frustumCullingEnabled && this.frustum.intersectsObject ? this.frustum.intersectsObject(obj) : true;
    //       if (isVisible) {
    //         obj.rotation.z += obj.userData.rotationSpeed; // 천천히 회전
    //       }
    //     }
    //   });
    // }

    // 🚀 성능 최적화: 렌더링 (Three.js 내부적으로 Frustum Culling 자동 적용)
    this.renderer.render(this.scene, this.camera);
    
    // ✅ CSS2DRenderer 렌더링 (고해상도 HTML 라벨링)
    if (this.css2dRenderer) {
      this.css2dRenderer.render(this.scene, this.camera);
    }
    
    // ✅ CSS3DRenderer 렌더링 (3D 홀로그램 콘솔)
    if (this.css3dRenderer) {
      this.css3dRenderer.render(this.scene, this.camera);
    }
  }
}

window.Showroom = Showroom;

