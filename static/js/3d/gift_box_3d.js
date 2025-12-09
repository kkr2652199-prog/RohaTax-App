/**
 * 3D 선물 상자 렌더러 (순수 JavaScript/Three.js)
 * React 컴포넌트를 순수 JavaScript로 변환
 */

class GiftBox3D {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with id "${containerId}" not found`);
            return;
        }

        // 옵션 설정
        this.options = {
            productName: options.productName || '토큰 이벤트',
            tokenAmount: options.tokenAmount || 60,
            productType: options.productType || 'event', // 'event' or 'event_period'
            durationDays: options.durationDays || 0,
            isActive: options.isActive !== false,
            onPurchaseClick: options.onPurchaseClick || null,
            ...options
        };

        // Three.js 설정
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.lidGroup = null;
        this.isOpen = false;
        this.animationId = null;

        // 색상 설정
        this.BOX_RED = "#7f1d1d";
        this.RIBBON_GOLD = "#fbbf24";
        this.RIBBON_ACCENT = "#b45309";
        this.TEXT_COLOR = "#ffedcc";

        // 크기 설정
        this.boxWidth = 2.0;
        this.boxDepth = 2.0;
        this.boxHeight = 1.8;
        this.wallThickness = 0.15;
        this.ribbonWidth = 0.3;
        this.ribbonThick = 0.02;
        this.lidHeight = 0.4;
        this.lidOverhang = 0.1;
        this.boxRadius = 0.1;
        this.bevelSize = 0.03;

        this.init();
    }

    init() {
        // 컨테이너 스타일 설정
        // 전체 화면 컨테이너인지 확인
        const isFullscreen = this.container.classList.contains('gift-box-3d-fullscreen');
        
        this.container.style.width = '100%';
        this.container.style.height = isFullscreen ? '100vh' : '400px';
        this.container.style.position = 'relative';
        this.container.style.background = 'transparent';

        // Three.js Scene 생성
        this.scene = new THREE.Scene();
        this.scene.background = null; // 투명 배경

        // Camera 설정
        this.camera = new THREE.PerspectiveCamera(
            40,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(4, 3, 6);
        this.camera.lookAt(0, 0.5, 0);

        // Renderer 설정
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.container.appendChild(this.renderer.domElement);

        // OrbitControls 추가 (마우스로 회전 가능)
        // OrbitControls가 로드될 때까지 대기
        const initControls = () => {
            if (typeof THREE !== 'undefined') {
                // OrbitControls가 전역으로 로드되었는지 확인
                if (typeof OrbitControls !== 'undefined') {
                    if (typeof THREE.OrbitControls === 'undefined') {
                        THREE.OrbitControls = OrbitControls;
                    }
                    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                    this.controls.enablePan = false;
                    this.controls.enableZoom = true;
                    this.controls.minPolarAngle = 0;
                    this.controls.maxPolarAngle = Math.PI / 2.2;
                    this.controls.autoRotate = false;
                    this.controls.target.set(0, 0.5, 0);
                    this.controls.update();
                } else {
                    // OrbitControls가 아직 로드되지 않았으면 재시도
                    setTimeout(initControls, 100);
                }
            }
        };
        initControls();

        // 조명 설정
        this.setupLights();

        // 3D 상자 생성
        this.createGiftBox();

        // 애니메이션 시작
        this.animate();

        // 리사이즈 핸들러
        window.addEventListener('resize', () => this.handleResize());
    }

    setupLights() {
        // Ambient Light
        const ambientLight = new THREE.AmbientLight(0xffddaa, 0.4);
        this.scene.add(ambientLight);

        // Main Spotlight
        const spotLight = new THREE.SpotLight(0xfff5cc, 2);
        spotLight.position.set(5, 8, 5);
        spotLight.angle = 0.4;
        spotLight.penumbra = 0.5;
        spotLight.castShadow = true;
        spotLight.shadow.mapSize.width = 1024;
        spotLight.shadow.mapSize.height = 1024;
        spotLight.shadow.bias = -0.0001;
        this.scene.add(spotLight);

        // Fill Light
        const pointLight = new THREE.PointLight(0xbd5e5e, 0.5);
        pointLight.position.set(-5, 2, -5);
        this.scene.add(pointLight);

        // Rim Light
        const rimLight = new THREE.SpotLight(0xffd700, 3);
        rimLight.position.set(0, 5, -8);
        rimLight.distance = 15;
        this.scene.add(rimLight);
    }

    createGiftBox() {
        const mainGroup = new THREE.Group();
        mainGroup.scale.set(1.5, 1.5, 1.5);
        mainGroup.position.set(0, -1, 0);

        // 상자 본체 생성
        this.createBoxBody(mainGroup);

        // 뚜껑 생성
        this.createLid(mainGroup);

        // 텍스트 추가
        this.createText(mainGroup);

        // 테이블/바닥
        this.createTable(mainGroup);

        this.scene.add(mainGroup);
    }

    createBoxBody(parent) {
        const boxGroup = new THREE.Group();

        // 둥근 모서리 상자 생성 (간단한 버전)
        const boxGeometry = new THREE.BoxGeometry(
            this.boxWidth,
            this.boxHeight,
            this.boxDepth,
            16, 16, 16
        );

        const boxMaterial = new THREE.MeshPhysicalMaterial({
            color: this.BOX_RED,
            roughness: 0.25,
            metalness: 0.1,
            clearcoat: 0.8,
            clearcoatRoughness: 0.2
        });

        const boxMesh = new THREE.Mesh(boxGeometry, boxMaterial);
        boxMesh.castShadow = true;
        boxMesh.receiveShadow = true;
        boxGroup.add(boxMesh);

        // 리본 추가
        this.createRibbons(boxGroup);

        parent.add(boxGroup);
    }

    createRibbons(parent) {
        // 가로 리본
        const horizontalRibbon = new THREE.Mesh(
            new THREE.BoxGeometry(this.ribbonWidth, this.ribbonThick, this.boxDepth - 0.2),
            new THREE.MeshPhysicalMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.6,
                roughness: 0.3
            })
        );
        horizontalRibbon.position.set(0, -this.ribbonThick / 2, 0);
        horizontalRibbon.receiveShadow = true;
        parent.add(horizontalRibbon);

        // 세로 리본
        const verticalRibbon = new THREE.Mesh(
            new THREE.BoxGeometry(this.boxWidth - 0.2, this.ribbonThick, this.ribbonWidth),
            new THREE.MeshPhysicalMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.6,
                roughness: 0.3
            })
        );
        verticalRibbon.position.set(0, -this.ribbonThick / 2, 0);
        verticalRibbon.receiveShadow = true;
        parent.add(verticalRibbon);
    }

    createLid(parent) {
        const hingePosition = [0, this.boxHeight, -this.boxDepth / 2];
        
        this.lidGroup = new THREE.Group();
        this.lidGroup.position.set(...hingePosition);

        const lidGroupInner = new THREE.Group();
        lidGroupInner.position.set(0, this.lidHeight / 2, this.boxDepth / 2);

        // 뚜껑 메시
        const lidGeometry = new THREE.BoxGeometry(
            this.boxWidth + this.lidOverhang,
            this.lidHeight,
            this.boxDepth + this.lidOverhang,
            16, 16, 16
        );

        const lidMaterial = new THREE.MeshPhysicalMaterial({
            color: this.BOX_RED,
            roughness: 0.25,
            metalness: 0.1,
            clearcoat: 0.8
        });

        const lidMesh = new THREE.Mesh(lidGeometry, lidMaterial);
        lidMesh.castShadow = true;
        lidGroupInner.add(lidMesh);

        // 뚜껑 리본
        const lidRibbon1 = new THREE.Mesh(
            new THREE.BoxGeometry(
                this.ribbonWidth + 0.02,
                this.lidHeight + 0.01,
                this.boxDepth + this.lidOverhang + 0.02
            ),
            new THREE.MeshPhysicalMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.6,
                roughness: 0.3
            })
        );
        lidGroupInner.add(lidRibbon1);

        const lidRibbon2 = new THREE.Mesh(
            new THREE.BoxGeometry(
                this.boxWidth + this.lidOverhang + 0.02,
                this.lidHeight + 0.01,
                this.ribbonWidth + 0.02
            ),
            new THREE.MeshPhysicalMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.6,
                roughness: 0.3
            })
        );
        lidGroupInner.add(lidRibbon2);

        // 리본 장식 (Bow)
        this.createBow(lidGroupInner);

        this.lidGroup.add(lidGroupInner);
        parent.add(this.lidGroup);
    }

    createBow(parent) {
        const bowGroup = new THREE.Group();
        bowGroup.position.set(0, this.lidHeight / 2 + 0.1, 0);

        // 루프
        const loop1 = new THREE.Mesh(
            new THREE.TorusGeometry(0.3, 0.12, 16, 32),
            new THREE.MeshStandardMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.4,
                roughness: 0.4
            })
        );
        loop1.position.set(-0.35, 0.15, 0);
        loop1.rotation.z = 0.6;
        bowGroup.add(loop1);

        const loop2 = new THREE.Mesh(
            new THREE.TorusGeometry(0.3, 0.12, 16, 32),
            new THREE.MeshStandardMaterial({
                color: this.RIBBON_GOLD,
                metalness: 0.4,
                roughness: 0.4
            })
        );
        loop2.position.set(0.35, 0.15, 0);
        loop2.rotation.z = -0.6;
        bowGroup.add(loop2);

        // 중앙 매듭
        const centerKnot = new THREE.Mesh(
            new THREE.SphereGeometry(0.18, 16, 16),
            new THREE.MeshStandardMaterial({
                color: this.RIBBON_ACCENT,
                metalness: 0.4,
                roughness: 0.4
            })
        );
        centerKnot.position.set(0, 0.05, 0);
        bowGroup.add(centerKnot);

        parent.add(bowGroup);
    }

    createText(parent) {
        // Canvas를 사용한 텍스트 텍스처 생성
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 512;
        const context = canvas.getContext('2d');

        // 배경 투명
        context.clearRect(0, 0, canvas.width, canvas.height);

        // 제목 텍스트 (이벤트 타입에 따라 다르게)
        const isPeriodEvent = this.options.productType === 'event_period';
        const titleText = isPeriodEvent ? '⏳ 기간 이벤트' : '🎉 토큰 이벤트';
        
        context.fillStyle = '#ffdb4d';
        context.font = 'bold 80px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.strokeStyle = '#FFFFFF';
        context.lineWidth = 8;
        context.strokeText(titleText, canvas.width / 2, 120);
        context.fillText(titleText, canvas.width / 2, 120);

        // 서브타이틀
        context.fillStyle = '#ffe6b3';
        context.font = '48px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 4;
        context.strokeText('Welcome Event', canvas.width / 2, 200);
        context.fillText('Welcome Event', canvas.width / 2, 200);

        // 메인 혜택
        context.fillStyle = '#ffffff';
        context.font = 'bold 72px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 6;
        
        let mainText = '';
        if (isPeriodEvent) {
            mainText = `신규 가입 혜택 (${this.options.durationDays}일 무료)`;
        } else {
            mainText = `신규 가입 혜택 (${this.options.tokenAmount}토큰)`;
        }
        context.strokeText(mainText, canvas.width / 2, 300);
        context.fillText(mainText, canvas.width / 2, 300);

        // 설명
        context.fillStyle = '#ffedcc';
        context.font = '40px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 3;
        
        let descText = '';
        if (isPeriodEvent) {
            descText = `${this.options.durationDays}일 동안 무료 체험이\n제공됩니다.`;
        } else {
            descText = `${this.options.tokenAmount}개의 무료 토큰이\n즉시 지급됩니다.`;
        }
        
        const lines = descText.split('\n');
        lines.forEach((line, i) => {
            context.strokeText(line, canvas.width / 2, 380 + i * 50);
            context.fillText(line, canvas.width / 2, 380 + i * 50);
        });

        // 텍스처 생성
        const texture = new THREE.CanvasTexture(canvas);
        texture.anisotropy = 16;
        texture.colorSpace = THREE.SRGBColorSpace;

        // 평면에 텍스트 적용
        const textGeometry = new THREE.PlaneGeometry(1.8, 0.9);
        const textMaterial = new THREE.MeshStandardMaterial({
            map: texture,
            transparent: true,
            emissive: '#ffedcc',
            emissiveIntensity: 0.2
        });

        const textMesh = new THREE.Mesh(textGeometry, textMaterial);
        textMesh.position.set(0, this.boxHeight / 2, this.boxDepth / 2 + 0.07);
        parent.add(textMesh);
    }

    createTable(parent) {
        // 테이블/바닥
        const tableGeometry = new THREE.CylinderGeometry(4, 4, 0.2, 64);
        const tableMaterial = new THREE.MeshStandardMaterial({
            color: '#222',
            roughness: 0.1,
            metalness: 0.2
        });
        const table = new THREE.Mesh(tableGeometry, tableMaterial);
        table.position.set(0, -0.1, 0);
        table.receiveShadow = true;
        parent.add(table);
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        // 뚜껑 애니메이션
        if (this.lidGroup) {
            const targetRotation = this.isOpen ? -Math.PI * 0.65 : 0;
            // THREE.MathUtils가 없으면 직접 lerp 함수 사용
            const lerp = (a, b, t) => a + (b - a) * t;
            this.lidGroup.rotation.x = lerp(
                this.lidGroup.rotation.x,
                targetRotation,
                0.05
            );
        }

        // Controls 업데이트
        if (this.controls) {
            this.controls.update();
        }

        // 렌더링
        this.renderer.render(this.scene, this.camera);
    }

    handleResize() {
        if (!this.container || !this.camera || !this.renderer) return;

        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    toggleLid() {
        this.isOpen = !this.isOpen;
    }

    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        if (this.controls) {
            this.controls.dispose();
        }

        if (this.renderer) {
            this.renderer.dispose();
            if (this.container && this.renderer.domElement) {
                this.container.removeChild(this.renderer.domElement);
            }
        }

        // Scene 정리
        if (this.scene) {
            this.scene.traverse((object) => {
                if (object.geometry) object.geometry.dispose();
                if (object.material) {
                    if (Array.isArray(object.material)) {
                        object.material.forEach(m => m.dispose());
                    } else {
                        object.material.dispose();
                    }
                }
            });
        }
    }
}

// 전역으로 노출
window.GiftBox3D = GiftBox3D;

