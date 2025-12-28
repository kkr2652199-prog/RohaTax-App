/**
 * GiftBox3D - 재사용 가능한 3D 선물 상자 클래스
 * 
 * @class GiftBox3D
 * @description 상점 페이지에서 여러 상품에 재사용 가능한 3D 선물 상자 컴포넌트
 * 
 * @example
 * const giftBox = new GiftBox3D('canvas-container', {
 *   boxColor: 0x7b1113,
 *   ribbonColor: 0xFFD700,
 *   texts: {
 *     title: "토큰 이벤트",
 *     subTitle: "Welcome Event",
 *     mainBenefit: "신규 가입 혜택 (60토큰)"
 *   }
 * });
 * giftBox.init();
 */
class GiftBox3D {
  /**
   * ✅ WebGL 텍스처 유닛 최적화: Static Material 공유
   * 모든 GiftBox3D 인스턴스가 동일한 Material을 공유하여 텍스처 유닛 절약
   */
  static sharedBoxMat = {};          // 상자 Material (색상별 공유)
  static sharedLinerMat = null;      // 내부 라이너 Material (골드)
  static sharedRibbonMat = {};       // 리본 Material (색상별 공유)
  static sharedConfettiMats = {};    // 컨페티 Material (색상별 공유)

  /**
   * @param {string} containerId - 3D 캔버스가 들어갈 HTML 요소의 ID
   * @param {Object} options - 설정 객체
   * @param {number} [options.boxColor=0x5D0016] - 상자 색상 (기본값: Deep Velvet Wine)
   * @param {number} [options.ribbonColor=0xD4AF37] - 리본 색상 (기본값: Rich Gold)
   * @param {Object} [options.texts] - 텍스트 설정 객체
   * @param {string} [options.texts.icon="🎉"] - 아이콘 이모지
   * @param {string} [options.texts.title="토큰 이벤트"] - 메인 타이틀
   * @param {string} [options.texts.subTitle="Welcome Event"] - 서브 타이틀
   * @param {string} [options.texts.mainBenefit="신규 가입 혜택 (60토큰)"] - 핵심 혜택
   * @param {string} [options.texts.description1="60개의 무료 토큰이"] - 설명 1
   * @param {string} [options.texts.description2="즉시 지급됩니다."] - 설명 2
   * @param {string} [options.texts.smallText="금액 부담 없이 즉시 사용\n관리자 승인 없이 자동 적용"] - 작은 설명
   */
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = null;
    this.canvas = null;
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.giftRoot = null;
    this.lidGroup = null;
    this.confetti = [];
    this.confettiGroup = null;
    this.isOpen = false;
    this.animationId = null;
    this.clock = new THREE.Clock();
    
    // 🚀 CPU 최적화: Page Visibility API로 백그라운드에서 애니메이션 일시정지
    this.isVisible = !document.hidden;

    // 설정 객체 (기본값 포함)
    this.config = {
      boxColor: options.boxColor || 0x5D0016, // Deep Velvet Wine
      boxColorHighlight: options.boxColorHighlight || 0x881326, // Ruby Shine
      ribbonColor: options.ribbonColor || 0xD4AF37, // Rich Gold
      ribbonColorShimmer: options.ribbonColorShimmer || 0xFADD85, // Shimmer Gold
      texts: {
        icon: options.texts?.icon || "🎉",
        title: options.texts?.title || "토큰 이벤트",
        subTitle: options.texts?.subTitle || "Welcome Event",
        mainBenefit: options.texts?.mainBenefit || "신규 가입 혜택 (60토큰)",
        description1: options.texts?.description1 || "60개의 무료 토큰이",
        description2: options.texts?.description2 || "즉시 지급됩니다.",
        smallText: options.texts?.smallText || "금액 부담 없이 즉시 사용\n관리자 승인 없이 자동 적용"
      }
    };

    // Dimensions (고정값)
    // 골드무제한 상품 크기 기준: 가로폭 1.2, 세로폭 1.2, 높이 1.2
    this.dimensions = {
      boxWidth: 1.2, // 골드무제한과 동일한 크기 (1.4 → 1.2)
      boxDepth: 1.2, // 골드무제한과 동일한 크기 (1.4 → 1.2)
      boxHeight: 0.9, // 골드무제한과 동일한 높이 (1.1 → 0.9, 총 높이 1.2)
      wallThickness: 0.15,
      ribbonWidth: 0.26,
      ribbonThick: 0.05,
      lidHeight: 0.3, // 총 높이 = 0.9 + 0.3 = 1.2
      lidOverhang: 0.1,
      boxRadius: 0.1,
      bevelSize: 0.03
    };

    // 메모리 관리용 배열
    this.geometries = [];
    this.materials = [];
    this.textures = [];
  }

  /**
   * 초기화 - 씬, 카메라, 조명 설정
   */
  init() {
    // 컨테이너 확인
    this.container = document.getElementById(this.containerId);
    if (!this.container) {
      console.error(`Container with id "${this.containerId}" not found`);
      return;
    }

    // Canvas 생성
    this.canvas = document.createElement('canvas');
    this.container.appendChild(this.canvas);

    // Renderer 설정
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true, // 투명 배경
      powerPreference: "high-performance"
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2.5));
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);

    // 색상 품질 향상 설정
    if (THREE.SRGBColorSpace !== undefined) {
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    } else {
      this.renderer.outputEncoding = THREE.sRGBEncoding;
    }

    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    this.renderer.useLegacyLights = false;

    // Scene 설정
    this.scene = new THREE.Scene();
    this.scene.background = null; // 투명 배경

    // Camera 설정 (압도적인 공간감 연출)
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 200); // FOV 45 -> 50 (시야각 확대)
    this.camera.position.set(3.5, 2.5, 4.5); // 가까이서 웅장하게 (기존: 5.5, 4.5, 6.5)

    // Controls 설정
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.enableZoom = false; // 마우스 휠로 페이지 스크롤 가능하도록
      this.controls.enablePan = false; // 화면 이동 방지
      this.controls.autoRotate = true; // 자동 회전 유지
      this.controls.autoRotateSpeed = 1.0; // 회전 속도
      this.controls.target.set(0, 1.2, 0);
      this.controls.maxPolarAngle = Math.PI * 0.49;
    }

    // 조명 설정
    this.setupLights();

    // 바닥 생성 (ShadowMaterial)
    this.createFloor();

    // Gift Root Group
    this.giftRoot = new THREE.Group();
    this.giftRoot.scale.set(1.5, 1.5, 1.5);
    this.scene.add(this.giftRoot);

    // Model 생성 (상자 + 뚜껑 + 꽃가루)
    const modelGroup = this.createModel();
    this.giftRoot.add(modelGroup);

    // lidGroup 참조 확보
    if (!this.lidGroup) {
      this.lidGroup = modelGroup.getObjectByName('lidGroup') || this.lidGroup;
    }

    // 반응형 처리
    this.setupResize();
    
    // 🚀 CPU 최적화: Page Visibility API로 백그라운드에서 애니메이션 일시정지
    // 초기 로드 시에는 항상 애니메이션 시작, 이후 visibilitychange에서만 제어
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        // 페이지가 숨겨지면 애니메이션 중지
        if (this.animationId) {
          cancelAnimationFrame(this.animationId);
          this.animationId = null;
        }
      } else {
        // 페이지가 다시 보이면 애니메이션 재개
        if (!this.animationId) {
          this.animate();
        }
      }
    });

    // 애니메이션 시작
    this.animate();
  }

  /**
   * 조명 설정
   */
  setupLights() {
    // Ambient Light
    const ambient = new THREE.AmbientLight(0xffffff, 0.65);
    this.scene.add(ambient);

    // Hemisphere Light
    const hemi = new THREE.HemisphereLight(
      new THREE.Color(0xfff4d6),
      new THREE.Color(0x2A0005),
      0.95
    );
    this.scene.add(hemi);

    // Main Directional Light
    const dir = new THREE.DirectionalLight(0xffffff, 2.5);
    dir.position.set(7, 12, 6.5);
    dir.castShadow = true;
    dir.shadow.mapSize.set(4096, 4096);
    dir.shadow.camera.near = 0.5;
    dir.shadow.camera.far = 20;
    dir.shadow.camera.left = -6;
    dir.shadow.camera.right = 6;
    dir.shadow.camera.top = 6;
    dir.shadow.camera.bottom = -6;
    dir.shadow.bias = -0.0001;
    dir.shadow.normalBias = 0.02;
    this.scene.add(dir);

    // Fill Light
    const fill = new THREE.DirectionalLight(new THREE.Color(0xfff6e4), 1.0);
    fill.position.set(-6, 4, -5);
    this.scene.add(fill);

    // Rim Light
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.8);
    rimLight.position.set(-5, 8, 8);
    this.scene.add(rimLight);

    // Spot Light
    const spotLight = new THREE.SpotLight(0xffffff, 1.2);
    spotLight.position.set(5, 10, 5);
    spotLight.angle = Math.PI / 6;
    spotLight.penumbra = 0.3;
    spotLight.castShadow = true;
    this.scene.add(spotLight);

    // Highlight Light (Ruby Shine)
    const highlightColor = new THREE.Color(this.config.boxColorHighlight);
    const highlightLight = new THREE.DirectionalLight(highlightColor, 0.45);
    highlightLight.position.set(5, 8, 4);
    this.scene.add(highlightLight);

    // Gold Reflection
    const goldReflection = new THREE.DirectionalLight(
      new THREE.Color(this.config.ribbonColorShimmer),
      0.3
    );
    goldReflection.position.set(-4, 6, 5);
    this.scene.add(goldReflection);
  }

  /**
   * 바닥 생성 (ShadowMaterial - 그림자만 표시)
   */
  createFloor() {
    const floorGeo = new THREE.PlaneGeometry(20, 20);
    this.geometries.push(floorGeo);
    const floorMat = new THREE.ShadowMaterial({ opacity: 0.3 });
    this.materials.push(floorMat);
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.2;
    floor.receiveShadow = true;
    this.scene.add(floor);
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 컨페티 Material 가져오기 (색상별 공유)
   */
  static getConfettiMaterial(color) {
    const colorKey = color.toString();
    if (!GiftBox3D.sharedConfettiMats[colorKey]) {
      GiftBox3D.sharedConfettiMats[colorKey] = new THREE.MeshStandardMaterial({
        color: color,
        metalness: 0.2,
        roughness: 0.4,
        side: THREE.DoubleSide
      });
    }
    return GiftBox3D.sharedConfettiMats[colorKey];
  }

  /**
   * Confetti 초기화
   */
  buildConfettiGroup() {
    const confettiCount = 45;
    const group = new THREE.Group();
    group.position.set(0, this.dimensions.boxHeight * 0.2, 0);
    const confettiGeo = new THREE.PlaneGeometry(0.08, 0.12);
    this.geometries.push(confettiGeo);
    const confettiColors = [0xf59e0b, 0x22d3ee, 0xec4899, 0xa3e635, 0xffedd5, 0xffffff, 0xffd700];
    this.confetti = [];

    for (let i = 0; i < confettiCount; i++) {
      const color = confettiColors[i % confettiColors.length];
      // ✅ Static Material 공유 사용 (색상별 공유)
      const mat = GiftBox3D.getConfettiMaterial(color);
      // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
      const m = new THREE.Mesh(confettiGeo, mat);
      m.castShadow = true;
      m.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      );
      group.add(m);
      this.confetti.push({
        mesh: m,
        vel: new THREE.Vector3(),
        angVel: new THREE.Vector3(),
        life: 0
      });
    }

    return group;
  }

  initConfetti() {
    if (!this.giftRoot) {
      return;
    }

    const group = this.buildConfettiGroup();
    this.confettiGroup = group;
    this.giftRoot.add(group);
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 상자 Material 가져오기 (색상별 공유)
   */
  static getBoxMaterial(boxColor) {
    const colorKey = boxColor instanceof THREE.Color ? boxColor.getHex() : boxColor;
    if (!GiftBox3D.sharedBoxMat) {
      GiftBox3D.sharedBoxMat = {};
    }
    if (!GiftBox3D.sharedBoxMat[colorKey]) {
      GiftBox3D.sharedBoxMat[colorKey] = new THREE.MeshStandardMaterial({
        color: boxColor,
        roughness: 0.5,
        metalness: 0.0
        // envMapIntensity 제거: 텍스처 유닛 절약
      });
    }
    return GiftBox3D.sharedBoxMat[colorKey];
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 라이너 Material 가져오기 (공유)
   */
  static getLinerMaterial() {
    if (!GiftBox3D.sharedLinerMat) {
      GiftBox3D.sharedLinerMat = new THREE.MeshStandardMaterial({
        color: 0xdab15a,
        metalness: 0.65,
        roughness: 0.2,
        side: THREE.DoubleSide
        // clearcoat 제거: MeshStandardMaterial로 변경하여 텍스처 유닛 절약
      });
    }
    return GiftBox3D.sharedLinerMat;
  }

  /**
   * ✅ WebGL 최적화: Static Material 공유
   * 리본 Material 가져오기 (색상별 공유)
   */
  static getRibbonMaterial(ribbonColor) {
    const colorKey = ribbonColor instanceof THREE.Color ? ribbonColor.getHex() : ribbonColor;
    if (!GiftBox3D.sharedRibbonMat) {
      GiftBox3D.sharedRibbonMat = {};
    }
    if (!GiftBox3D.sharedRibbonMat[colorKey]) {
      GiftBox3D.sharedRibbonMat[colorKey] = new THREE.MeshStandardMaterial({
        color: ribbonColor,
        metalness: 0.3,
        roughness: 0.15
        // envMapIntensity 제거: 텍스처 유닛 절약
      });
    }
    return GiftBox3D.sharedRibbonMat[colorKey];
  }

  /**
   * 상자 모델 생성
   */
  createBox() {
    const group = new THREE.Group();

    // Walls
    const boxGeometry = this.createBoxGeometry();
    const boxColor = new THREE.Color(this.config.boxColor);
    // ✅ Static Material 공유 사용
    const boxMaterial = GiftBox3D.getBoxMaterial(boxColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const walls = new THREE.Mesh(boxGeometry, boxMaterial);
    walls.rotation.x = -Math.PI / 2;
    walls.castShadow = true;
    walls.receiveShadow = true;
    group.add(walls);

    // Floor
    const floorShape = new THREE.Shape();
    const fw = (this.dimensions.boxWidth - this.dimensions.wallThickness * 2) / 2;
    const fh = (this.dimensions.boxDepth - this.dimensions.wallThickness * 2) / 2;
    const fr = Math.max(0.04, this.dimensions.boxRadius * 0.5);
    floorShape.moveTo(-fw + fr, -fh);
    floorShape.lineTo(fw - fr, -fh);
    floorShape.quadraticCurveTo(fw, -fh, fw, -fh + fr);
    floorShape.lineTo(fw, fh - fr);
    floorShape.quadraticCurveTo(fw, fh, fw - fr, fh);
    floorShape.lineTo(-fw + fr, fh);
    floorShape.quadraticCurveTo(-fw, fh, -fw, fh - fr);
    floorShape.lineTo(-fw, -fh + fr);
    floorShape.quadraticCurveTo(-fw, -fh, -fw + fr, -fh);

    const floorGeo = new THREE.ExtrudeGeometry(floorShape, {
      depth: this.dimensions.wallThickness,
      bevelEnabled: true,
      bevelSegments: 5,
      steps: 1,
      bevelSize: fr * 0.6,
      bevelThickness: fr * 0.6,
      curveSegments: 16
    });
    floorGeo.center();
    this.geometries.push(floorGeo);
    const floorColor = new THREE.Color(this.config.boxColor);
    // ✅ Static Material 공유 사용 (boxMaterial과 동일한 속성)
    const floorMat = GiftBox3D.getBoxMaterial(floorColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = this.dimensions.wallThickness / 2;
    floor.castShadow = true;
    floor.receiveShadow = true;
    group.add(floor);

    // Inner liner (gold tone)
    const linerGeo = new THREE.ExtrudeGeometry(floorShape, {
      depth: this.dimensions.wallThickness * 0.35,
      bevelEnabled: true,
      bevelSegments: 3,
      steps: 1,
      bevelSize: fr * 0.35,
      bevelThickness: fr * 0.35,
      curveSegments: 12
    });
    linerGeo.center();
    this.geometries.push(linerGeo);
    // ✅ Static Material 공유 사용
    const linerMat = GiftBox3D.getLinerMaterial();
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const liner = new THREE.Mesh(linerGeo, linerMat);
    liner.rotation.x = -Math.PI / 2;
    liner.position.y = this.dimensions.wallThickness * 0.9;
    liner.scale.set(0.96, 1, 0.96);
    liner.castShadow = false;
    liner.receiveShadow = true;
    group.add(liner);

    // Front text plate
    const frontTextTex = this.createTexts();
    const frontMat = new THREE.MeshStandardMaterial({
      map: frontTextTex,
      transparent: true,
      roughness: 0.2,
      metalness: 0.1
    });
    this.materials.push(frontMat);
    const frontPlate = new THREE.Mesh(
      new THREE.PlaneGeometry(
        this.dimensions.boxWidth * 0.98,
        this.dimensions.boxHeight * 0.88
      ),
      frontMat
    );
    frontPlate.position.set(0, this.dimensions.boxHeight * 0.48, this.dimensions.boxDepth / 2 + 0.035);
    group.add(frontPlate);

    return group;
  }

  createModel() {
    const group = new THREE.Group();
    const boxGroup = this.createBox();
    group.add(boxGroup);
    const lidGroup = this.createLid();
    lidGroup.name = 'lidGroup';
    this.lidGroup = lidGroup;
    group.add(lidGroup);
    const confetti = this.buildConfettiGroup();
    if (confetti) {
      group.add(confetti);
    }
    group.userData = {
      isProduct: true,
      productData: this.config
    };
    return group;
  }

  /**
   * 상자 지오메트리 생성
   */
  createBoxGeometry() {
    const shape = new THREE.Shape();
    const w = this.dimensions.boxWidth / 2;
    const h = this.dimensions.boxDepth / 2;
    const r = this.dimensions.boxRadius;

    // Outer rounded rect
    shape.moveTo(-w + r, -h);
    shape.lineTo(w - r, -h);
    shape.quadraticCurveTo(w, -h, w, -h + r);
    shape.lineTo(w, h - r);
    shape.quadraticCurveTo(w, h, w - r, h);
    shape.lineTo(-w + r, h);
    shape.quadraticCurveTo(-w, h, -w, h - r);
    shape.lineTo(-w, -h + r);
    shape.quadraticCurveTo(-w, -h, -w + r, -h);

    // Inner hole
    const hole = new THREE.Shape();
    const iw = w - this.dimensions.wallThickness;
    const ih = h - this.dimensions.wallThickness;
    const ir = Math.max(0.01, r - this.dimensions.wallThickness);

    hole.moveTo(-iw + ir, -ih);
    hole.quadraticCurveTo(-iw, -ih, -iw, -ih + ir);
    hole.lineTo(-iw, ih - ir);
    hole.quadraticCurveTo(-iw, ih, -iw + ir, ih);
    hole.lineTo(iw - ir, ih);
    hole.quadraticCurveTo(iw, ih, iw, ih - ir);
    hole.lineTo(iw, -ih + ir);
    hole.quadraticCurveTo(iw, -ih, iw - ir, -ih);
    hole.lineTo(-iw + ir, -ih);

    shape.holes.push(hole);

    const extrudeSettings = {
      depth: this.dimensions.boxHeight,
      bevelEnabled: true,
      bevelSegments: 5,
      steps: 1,
      bevelSize: this.dimensions.bevelSize,
      bevelThickness: this.dimensions.bevelSize,
      curveSegments: 12
    };
    const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    this.geometries.push(geometry);
    return geometry;
  }

  /**
   * 텍스트 생성 (Canvas Texture)
   */
  createTexts() {
    const size = 2048;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "rgba(0,0,0,0)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.textAlign = "center";
    const centerX = canvas.width / 2;

    // [15%] 아이콘
    ctx.font = "150px Arial";
    ctx.fillText(this.config.texts.icon, centerX, canvas.height * 0.15);

    // [25%] 메인 타이틀 (그림자 효과 포함)
    ctx.font = "bold 120px 'Noto Sans KR', sans-serif";
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
    ctx.fillText(this.config.texts.title, centerX + 4, canvas.height * 0.25 + 4);
    ctx.fillStyle = `#${this.config.ribbonColor.toString(16).padStart(6, '0')}`;
    ctx.fillText(this.config.texts.title, centerX, canvas.height * 0.25);

    // [32%] 서브 타이틀
    ctx.font = "300 60px 'Inter', sans-serif";
    ctx.fillStyle = "#E0E0E0";
    ctx.fillText(this.config.texts.subTitle, centerX, canvas.height * 0.32);

    // [50%] 핵심 혜택
    ctx.font = "bold 100px 'Noto Sans KR', sans-serif";
    ctx.fillStyle = "#FFFFFF";
    ctx.fillText(this.config.texts.mainBenefit, centerX, canvas.height * 0.50);

    // [65%] 설명 1
    ctx.font = "500 50px 'Noto Sans KR', sans-serif";
    ctx.fillStyle = "#CCCCCC";
    ctx.fillText(this.config.texts.description1, centerX, canvas.height * 0.65);

    // [70%] 설명 2
    ctx.fillText(this.config.texts.description2, centerX, canvas.height * 0.70);

    // [85%] 작은 설명
    ctx.font = "400 40px 'Noto Sans KR', sans-serif";
    ctx.fillStyle = "#AAAAAA";
    const lines = this.config.texts.smallText.split("\n");
    lines.forEach((line, i) => {
      ctx.fillText(line, centerX, canvas.height * 0.85 + i * 50);
    });

    const texture = new THREE.CanvasTexture(canvas);
    texture.anisotropy = 8;
    texture.needsUpdate = true;
    this.textures.push(texture);
    return texture;
  }

  /**
   * 뚜껑 생성
   */
  createLid() {
    const group = new THREE.Group();
    const hingePosition = new THREE.Vector3(
      0,
      this.dimensions.boxHeight,
      -this.dimensions.boxDepth / 2
    );
    group.position.copy(hingePosition);

    const lidBody = new THREE.Group();
    lidBody.position.set(0, this.dimensions.lidHeight / 2, this.dimensions.boxDepth / 2);
    group.add(lidBody);

    // Lid material
    const lidColor = new THREE.Color(this.config.boxColor);
    // ✅ Static Material 공유 사용 (boxMaterial과 동일한 속성)
    const lidMat = GiftBox3D.getBoxMaterial(lidColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음

    // Rounded lid via Shape + Extrude
    const lidShape = new THREE.Shape();
    const lw = (this.dimensions.boxWidth + this.dimensions.lidOverhang) / 2;
    const lh = (this.dimensions.boxDepth + this.dimensions.lidOverhang) / 2;
    const lr = this.dimensions.boxRadius;
    lidShape.moveTo(-lw + lr, -lh);
    lidShape.lineTo(lw - lr, -lh);
    lidShape.quadraticCurveTo(lw, -lh, lw, -lh + lr);
    lidShape.lineTo(lw, lh - lr);
    lidShape.quadraticCurveTo(lw, lh, lw - lr, lh);
    lidShape.lineTo(-lw + lr, lh);
    lidShape.quadraticCurveTo(-lw, lh, -lw, lh - lr);
    lidShape.lineTo(-lw, -lh + lr);
    lidShape.quadraticCurveTo(-lw, -lh, -lw + lr, -lh);

    const lidExtrude = new THREE.ExtrudeGeometry(lidShape, {
      depth: this.dimensions.lidHeight,
      bevelEnabled: true,
      bevelSegments: 6,
      steps: 1,
      bevelSize: this.dimensions.boxRadius * 0.6,
      bevelThickness: this.dimensions.boxRadius * 0.6,
      curveSegments: 16
    });
    lidExtrude.center();
    this.geometries.push(lidExtrude);
    const lidMesh = new THREE.Mesh(lidExtrude, lidMat);
    lidMesh.rotation.x = -Math.PI / 2;
    lidMesh.position.y = 0;
    lidMesh.castShadow = true;
    lidMesh.receiveShadow = true;
    lidBody.add(lidMesh);

    // Ribbon material
    const ribbonColor = new THREE.Color(this.config.ribbonColor);
    // ✅ Static Material 공유 사용
    const ribbonMatLid = GiftBox3D.getRibbonMaterial(ribbonColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const ribbonProtrusion = 0.05;

    // Cross ribbons on lid
    const lidRibbonTopX = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.boxWidth + this.dimensions.lidOverhang + ribbonProtrusion * 2,
        this.dimensions.ribbonThick,
        this.dimensions.ribbonWidth
      ),
      ribbonMatLid
    );
    lidRibbonTopX.position.set(0, this.dimensions.lidHeight / 2 + this.dimensions.ribbonThick / 2 + ribbonProtrusion, 0);
    lidRibbonTopX.castShadow = true;
    lidRibbonTopX.receiveShadow = true;
    lidBody.add(lidRibbonTopX);

    const lidRibbonTopZ = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonWidth,
        this.dimensions.ribbonThick,
        this.dimensions.boxDepth + this.dimensions.lidOverhang + ribbonProtrusion * 2
      ),
      ribbonMatLid
    );
    lidRibbonTopZ.position.set(0, this.dimensions.lidHeight / 2 + this.dimensions.ribbonThick / 2 + ribbonProtrusion, 0);
    lidRibbonTopZ.castShadow = true;
    lidRibbonTopZ.receiveShadow = true;
    lidBody.add(lidRibbonTopZ);

    const lidRibbonBottomX = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.boxWidth + this.dimensions.lidOverhang + ribbonProtrusion * 2,
        this.dimensions.ribbonThick,
        this.dimensions.ribbonWidth
      ),
      ribbonMatLid
    );
    lidRibbonBottomX.position.set(0, -this.dimensions.lidHeight / 2 - this.dimensions.ribbonThick / 2 - ribbonProtrusion, 0);
    lidRibbonBottomX.castShadow = true;
    lidRibbonBottomX.receiveShadow = true;
    lidBody.add(lidRibbonBottomX);

    const lidRibbonBottomZ = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonWidth,
        this.dimensions.ribbonThick,
        this.dimensions.boxDepth + this.dimensions.lidOverhang + ribbonProtrusion * 2
      ),
      ribbonMatLid
    );
    lidRibbonBottomZ.position.set(0, -this.dimensions.lidHeight / 2 - this.dimensions.ribbonThick / 2 - ribbonProtrusion, 0);
    lidRibbonBottomZ.castShadow = true;
    lidRibbonBottomZ.receiveShadow = true;
    lidBody.add(lidRibbonBottomZ);

    // Side ribbons
    const lidRibbonFront = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonWidth,
        this.dimensions.lidHeight + ribbonProtrusion * 2,
        this.dimensions.ribbonThick
      ),
      ribbonMatLid
    );
    lidRibbonFront.position.set(0, 0, (this.dimensions.boxDepth + this.dimensions.lidOverhang) / 2 + this.dimensions.ribbonThick / 2 + ribbonProtrusion);
    lidRibbonFront.castShadow = true;
    lidRibbonFront.receiveShadow = true;
    lidBody.add(lidRibbonFront);

    const lidRibbonBack = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonWidth,
        this.dimensions.lidHeight + ribbonProtrusion * 2,
        this.dimensions.ribbonThick
      ),
      ribbonMatLid
    );
    lidRibbonBack.position.set(0, 0, -(this.dimensions.boxDepth + this.dimensions.lidOverhang) / 2 - this.dimensions.ribbonThick / 2 - ribbonProtrusion);
    lidRibbonBack.castShadow = true;
    lidRibbonBack.receiveShadow = true;
    lidBody.add(lidRibbonBack);

    const lidRibbonLeft = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonThick,
        this.dimensions.lidHeight + ribbonProtrusion * 2,
        this.dimensions.ribbonWidth
      ),
      ribbonMatLid
    );
    lidRibbonLeft.position.set(-(this.dimensions.boxWidth + this.dimensions.lidOverhang) / 2 - this.dimensions.ribbonThick / 2 - ribbonProtrusion, 0, 0);
    lidRibbonLeft.castShadow = true;
    lidRibbonLeft.receiveShadow = true;
    lidBody.add(lidRibbonLeft);

    const lidRibbonRight = new THREE.Mesh(
      new THREE.BoxGeometry(
        this.dimensions.ribbonThick,
        this.dimensions.lidHeight + ribbonProtrusion * 2,
        this.dimensions.ribbonWidth
      ),
      ribbonMatLid
    );
    lidRibbonRight.position.set((this.dimensions.boxWidth + this.dimensions.lidOverhang) / 2 + this.dimensions.ribbonThick / 2 + ribbonProtrusion, 0, 0);
    lidRibbonRight.castShadow = true;
    lidRibbonRight.receiveShadow = true;
    lidBody.add(lidRibbonRight);

    // Bow
    const bowGroup = new THREE.Group();
    bowGroup.position.set(0, this.dimensions.lidHeight / 2 + 0.1, 0);

    const torusColor = new THREE.Color(this.config.ribbonColor);
    // ✅ Static Material 공유 사용 (ribbonMatLid와 동일한 속성)
    const torusMat = GiftBox3D.getRibbonMaterial(torusColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const loopA = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.12, 16, 32), torusMat);
    loopA.position.set(-0.35, 0.15, 0);
    loopA.rotation.z = 0.6;
    loopA.castShadow = true;
    bowGroup.add(loopA);

    const loopB = loopA.clone();
    loopB.position.set(0.35, 0.15, 0);
    loopB.rotation.z = -0.6;
    bowGroup.add(loopB);

    const knotColor = new THREE.Color(this.config.boxColor);
    // ✅ Static Material 공유 사용 (boxMaterial과 동일한 속성)
    const knotMat = GiftBox3D.getBoxMaterial(knotColor);
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const knot = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), knotMat);
    knot.position.set(0, 0.05, 0);
    knot.castShadow = true;
    bowGroup.add(knot);

    const tailColor = new THREE.Color(this.config.ribbonColor);
    // ✅ Static Material 공유 사용 (ribbonMatLid와 동일한 속성, side만 추가)
    const tailMat = GiftBox3D.getRibbonMaterial(tailColor);
    tailMat.side = THREE.DoubleSide; // tailMat만 양면 렌더링 필요
    // this.materials.push 제거: 공유 Material이므로 인스턴스별로 관리하지 않음
    const tailA = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.8, 0.02), tailMat);
    tailA.position.set(-0.4, 0, 0.4);
    tailA.rotation.set(0.5, 0.5, 0);
    tailA.castShadow = true;
    bowGroup.add(tailA);

    const tailB = tailA.clone();
    tailB.position.set(0.4, 0, -0.4);
    tailB.rotation.set(-0.5, -0.5, 0);
    bowGroup.add(tailB);

    lidBody.add(bowGroup);
    return group;
  }

  /**
   * Confetti 트리거
   */
  triggerConfetti() {
    const spread = 1.6;
    this.confetti.forEach((c) => {
      c.mesh.position.set(
        (Math.random() - 0.5) * spread,
        Math.random() * 0.8,
        (Math.random() - 0.5) * spread
      );
      c.vel.set(
        (Math.random() - 0.35) * 2.8,
        Math.random() * 5.8 + 3.6,
        (Math.random() - 0.35) * 2.8
      );
      c.angVel.set(
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8
      );
      c.life = 10.0;
      const s = 0.9 + Math.random() * 1.7;
      c.mesh.scale.set(s, s, s);
      c.mesh.visible = true;
    });
  }

  /**
   * Confetti 리셋
   */
  resetConfetti() {
    this.confetti.forEach((c) => {
      c.mesh.position.set(0, 0, 0);
      c.vel.set(0, 0, 0);
      c.angVel.set(0, 0, 0);
      c.life = 0;
      c.mesh.visible = false;
    });
  }

  /**
   * 상자 열기/닫기 토글
   */
  toggle() {
    if (!this.isOpen) {
      this.isOpen = true;
      this.triggerConfetti();
    } else {
      this.isOpen = false;
      this.resetConfetti();
    }
  }

  /**
   * 반응형 처리 설정
   */
  setupResize() {
    const resizeObserver = new ResizeObserver(() => {
      if (this.container && this.renderer && this.camera) {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // 컨테이너 크기가 0이거나 유효하지 않을 때 렌더러 크기 변경 방지
        if (width <= 0 || height <= 0 || !isFinite(width) || !isFinite(height)) {
          return;
        }
        
        this.renderer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
      }
    });
    resizeObserver.observe(this.container);
  }

  /**
   * 애니메이션 루프
   */
  animate() {
    // 🚀 CPU 최적화: visibilitychange 이벤트에서만 제어 (초기 로드는 항상 실행)
    this.animationId = requestAnimationFrame(() => this.animate());
    const delta = this.clock.getDelta();

    // Smooth hinge rotation
    const target = this.isOpen ? -Math.PI * 0.65 : 0;
    if (this.lidGroup) {
      const current = this.lidGroup.rotation.x;
      this.lidGroup.rotation.x = THREE.MathUtils.lerp(current, target, delta * 3);
    }

    // Confetti physics
    const gravity = new THREE.Vector3(0, -6, 0);
    const floorHeight = -0.2;
    this.confetti.forEach((c) => {
      if (c.life > 0 && c.mesh.visible) {
        c.vel.addScaledVector(gravity, delta);
        c.mesh.position.addScaledVector(c.vel, delta);
        c.mesh.rotation.x += c.angVel.x * delta;
        c.mesh.rotation.y += c.angVel.y * delta;
        c.mesh.rotation.z += c.angVel.z * delta;

        if (c.mesh.position.y <= floorHeight) {
          c.life = 0;
          c.mesh.visible = false;
          c.mesh.position.set(c.mesh.position.x, floorHeight, c.mesh.position.z);
        }
      }
    });

    if (this.controls) {
      this.controls.update();
    }
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * 메모리 해제 (페이지 이동 시 호출)
   */
  dispose() {
    // 애니메이션 중지
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }

    // Geometry 해제
    this.geometries.forEach(geo => {
      if (geo) geo.dispose();
    });
    this.geometries = [];

    // Material 해제
    this.materials.forEach(mat => {
      if (mat) {
        if (mat.map) mat.map.dispose();
        mat.dispose();
      }
    });
    this.materials = [];

    // Texture 해제
    this.textures.forEach(tex => {
      if (tex) tex.dispose();
    });
    this.textures = [];

    // Scene 정리
    if (this.scene) {
      this.scene.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach(mat => {
              if (mat.map) mat.map.dispose();
              mat.dispose();
            });
          } else {
            if (object.material.map) object.material.map.dispose();
            object.material.dispose();
          }
        }
      });
    }

    // Renderer 해제
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer = null;
    }

    // Canvas 제거
    if (this.canvas && this.container) {
      this.container.removeChild(this.canvas);
      this.canvas = null;
    }

    // 참조 정리
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.giftRoot = null;
    this.lidGroup = null;
    this.confetti = [];
    this.confettiGroup = null;
  }
}

// 전역 변수로 등록 (브라우저 호환성)
if (typeof window !== 'undefined') {
  window.GiftBox3D = GiftBox3D;
}

