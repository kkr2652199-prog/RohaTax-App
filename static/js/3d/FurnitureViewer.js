/**
 * FurnitureViewer - 가구 전용 3D 뷰어
 * 관리자 페이지에서 단일 가구를 시각화하는 경량 뷰어
 * 
 * @class FurnitureViewer
 * @description Showroom.js와 독립적으로 작동하는 가구 전용 뷰어
 * 
 * @example
 * const viewer = new FurnitureViewer('furniture-canvas');
 * viewer.displayProduct(productGroup);
 */
class FurnitureViewer {
  /**
   * @param {string} canvasId - 3D 캔버스가 들어갈 HTML 요소의 ID
   */
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.container = null;
    this.canvas = null;
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.currentProduct = null;
    this.animationId = null;
    this.factory = null; // ProductFactory 참조 (선택적)
    this.css3dRenderer = null; // CSS3DRenderer (HTML/CSS 렌더링용)
    
    // 🚀 CPU 최적화: Page Visibility API로 백그라운드에서 애니메이션 일시정지
    this.isVisible = !document.hidden;

    this.init();
  }
  
  /**
   * ProductFactory 참조 설정 (애니메이션용)
   */
  setFactory(factory) {
    this.factory = factory;
  }

  /**
   * 초기화 - Renderer, Scene, Camera, Light, Controls 설정
   */
  init() {
    // 컨테이너 확인
    this.container = document.getElementById(this.canvasId);
    if (!this.container) {
      console.error(`[FurnitureViewer] 컨테이너를 찾을 수 없습니다: ${this.canvasId}`);
      return;
    }

    // Canvas 생성
    this.canvas = document.createElement('canvas');
    this.canvas.style.display = 'block';
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    this.container.appendChild(this.canvas);

    // Renderer 설정
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true, // 투명 배경
      antialias: true,
      powerPreference: "high-performance"
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // 색상 인코딩 설정
    if (THREE.SRGBColorSpace !== undefined) {
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    } else {
      this.renderer.outputEncoding = THREE.sRGBEncoding;
    }

    // Scene 설정
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf5f5f5); // 연한 회색 배경 (가구가 잘 보이도록)

    // Camera 설정
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
    this.camera.position.set(0, 2, 5); // 기본 위치 (앞에서 위로 비춤)

    // 조명 설정
    this.setupLights();

    // OrbitControls 설정
    this.setupControls();
    
    // CSS3DRenderer 초기화 (HTML/CSS 렌더링용)
    this.initCSS3DRenderer();

    // 반응형 처리
    window.addEventListener('resize', () => this.resize());
    
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

    // 렌더링 루프 시작
    this.animate();

    console.log('✅ [FurnitureViewer] 초기화 완료');
  }
  
  /**
   * CSS3DRenderer 초기화 (HTML/CSS를 3D 객체로 렌더링)
   */
  initCSS3DRenderer() {
    try {
      const CSS3DRendererClass = window.CSS3DRenderer || (typeof CSS3DRenderer !== 'undefined' ? CSS3DRenderer : null);
      if (CSS3DRendererClass) {
        this.css3dRenderer = new CSS3DRendererClass();
        this.css3dRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.css3dRenderer.domElement.style.position = 'absolute';
        this.css3dRenderer.domElement.style.top = '0';
        this.css3dRenderer.domElement.style.left = '0';
        this.css3dRenderer.domElement.style.pointerEvents = 'none';
        this.css3dRenderer.domElement.style.zIndex = '999';
        this.container.appendChild(this.css3dRenderer.domElement);
        console.log('✅ [FurnitureViewer] CSS3DRenderer 초기화 완료');
      } else {
        console.warn('⚠️ [FurnitureViewer] CSS3DRenderer를 사용할 수 없습니다.');
        this.css3dRenderer = null;
      }
    } catch (error) {
      console.error('❌ [FurnitureViewer] CSS3DRenderer 초기화 실패:', error);
      this.css3dRenderer = null;
    }
  }

  /**
   * 조명 설정 - 가구가 잘 보이도록 AmbientLight와 DirectionalLight 배치
   */
  setupLights() {
    // Ambient Light (전체적인 밝기)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    // Directional Light 1 (앞에서 비춤)
    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(2, 3, 2);
    directionalLight1.castShadow = true;
    directionalLight1.shadow.mapSize.width = 2048;
    directionalLight1.shadow.mapSize.height = 2048;
    directionalLight1.shadow.camera.near = 0.5;
    directionalLight1.shadow.camera.far = 50;
    directionalLight1.shadow.camera.left = -5;
    directionalLight1.shadow.camera.right = 5;
    directionalLight1.shadow.camera.top = 5;
    directionalLight1.shadow.camera.bottom = -5;
    this.scene.add(directionalLight1);

    // Directional Light 2 (위에서 비춤)
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(0, 5, 0);
    this.scene.add(directionalLight2);

    // Point Light (보조 조명)
    const pointLight = new THREE.PointLight(0xffffff, 0.3, 20);
    pointLight.position.set(-3, 2, -3);
    this.scene.add(pointLight);
  }

  /**
   * OrbitControls 설정
   */
  setupControls() {
    if (typeof THREE.OrbitControls === 'undefined') {
      console.warn('[FurnitureViewer] OrbitControls를 찾을 수 없습니다. 스크립트가 로드되었는지 확인하세요.');
      return;
    }

    this.controls = new THREE.OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true; // 부드러운 회전
    this.controls.dampingFactor = 0.05;
    this.controls.enableZoom = true;
    this.controls.enablePan = false; // 팬 비활성화 (중앙 고정)
    this.controls.minDistance = 1;
    this.controls.maxDistance = 20;
    this.controls.target.set(0, 0, 0); // 항상 원점을 바라봄
  }

  /**
   * 가구 표시 - 기존 가구를 제거하고 새 가구를 Scene 정중앙에 배치
   * 
   * @param {THREE.Group} productGroup - 표시할 가구 객체
   */
  displayProduct(productGroup) {
    // 디버깅 코드 제거됨 (프로덕션 배포)
    if (!productGroup || !(productGroup instanceof THREE.Group)) {
      console.error('[FurnitureViewer] 유효하지 않은 가구 객체입니다.');
      return;
    }

    // 1. 기존 가구 제거
    if (this.currentProduct) {
      this.scene.remove(this.currentProduct);
      this.currentProduct = null;
    }

    // 2. 새 가구 추가 (Scene 정중앙)
    this.currentProduct = productGroup.clone(); // 원본 보호를 위해 클론
    this.currentProduct.position.set(0, 0, 0); // 정중앙 배치
    this.scene.add(this.currentProduct);

    // 3. 카메라 거리 자동 조정
    this.adjustCamera();

    console.log('✅ [FurnitureViewer] 가구 표시 완료');
  }

  /**
   * 카메라 거리 자동 조정 - 가구의 크기에 맞춰 카메라 위치 조정
   */
  adjustCamera() {
    if (!this.currentProduct) return;

    // 가구의 바운딩 박스 계산
    const box = new THREE.Box3().setFromObject(this.currentProduct);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    // 가구의 최대 크기 계산
    const maxSize = Math.max(size.x, size.y, size.z);
    
    // 디버깅: 바운딩 박스 정보 출력
    console.log(`[FurnitureViewer] adjustCamera - 크기: (${size.x.toFixed(2)}, ${size.y.toFixed(2)}, ${size.z.toFixed(2)}), 중심: (${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)}), maxSize: ${maxSize.toFixed(2)}`);
    
    // 샹들리에는 크기가 작을 수 있으므로 최소 거리 보장
    const minDistance = 5.0;
    const calculatedDistance = maxSize * 2.5;
    const distance = Math.max(calculatedDistance, minDistance);
    
    // 카메라 위치 설정 (가구를 앞에서 위로 비춤)
    this.camera.position.set(
      center.x + distance * 0.5,
      center.y + distance * 0.8,
      center.z + distance * 0.7
    );

    // 카메라가 가구 중심을 바라보도록 설정
    this.camera.lookAt(center);

    // OrbitControls 타겟 업데이트
    if (this.controls) {
      this.controls.target.copy(center);
      this.controls.update();
    }
    
    console.log(`[FurnitureViewer] 카메라 위치: (${this.camera.position.x.toFixed(2)}, ${this.camera.position.y.toFixed(2)}, ${this.camera.position.z.toFixed(2)}), 거리: ${distance.toFixed(2)}`);

    console.log(`[FurnitureViewer] 카메라 거리 조정: ${distance.toFixed(2)}m, 가구 크기: ${maxSize.toFixed(2)}m`);
  }

  /**
   * 렌더링 루프
   */
  animate() {
    // 🚀 CPU 최적화: visibilitychange 이벤트에서만 제어 (초기 로드는 항상 실행)
    this.animationId = requestAnimationFrame(() => this.animate());

    // OrbitControls 업데이트
    if (this.controls) {
      this.controls.update();
    }
    
    // ProductFactory 애니메이션 업데이트 (MagicFire 등)
    if (this.factory && typeof this.factory.updateProductAnimations === 'function') {
      this.factory.updateProductAnimations();
    }

    // 렌더링
    this.renderer.render(this.scene, this.camera);
    
    // CSS3DRenderer 렌더링 (HTML/CSS 객체)
    if (this.css3dRenderer) {
      this.css3dRenderer.render(this.scene, this.camera);
    }
  }

  /**
   * 반응형 처리 - 창 크기 변경 시 렌더러 및 카메라 조정
   */
  resize() {
    if (!this.container || !this.camera || !this.renderer) return;

    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
    
    // CSS3DRenderer 크기 조정
    if (this.css3dRenderer) {
      this.css3dRenderer.setSize(width, height);
    }
  }

  /**
   * 정리 - 리소스 해제
   */
  dispose() {
    // 애니메이션 루프 중지
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }

    // 기존 가구 제거
    if (this.currentProduct) {
      this.scene.remove(this.currentProduct);
      this.currentProduct = null;
    }

    // Controls 정리
    if (this.controls) {
      this.controls.dispose();
      this.controls = null;
    }

    // Renderer 정리
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer = null;
    }

    // 이벤트 리스너 제거
    window.removeEventListener('resize', () => this.resize());

    console.log('✅ [FurnitureViewer] 정리 완료');
  }
}

// 전역 변수로 노출 (기존 프로젝트와의 호환성)
if (typeof window !== 'undefined') {
  window.FurnitureViewer = FurnitureViewer;
}

// ES6 모듈로도 노출 (선택적)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FurnitureViewer;
}

