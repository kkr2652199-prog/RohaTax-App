/**
 * 이벤트 상품 3D 씬 (탁자 위에 2개 상자)
 * kwon3d 원본 구조를 기반으로 하나의 씬에 2개 상자 렌더링
 */

class EventProducts3DScene {
    constructor(containerId, productsData = []) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with id "${containerId}" not found`);
            return;
        }

        // 상품 데이터 (최대 2개: 토큰 이벤트, 기간 이벤트)
        this.products = productsData.slice(0, 2);
        
        // Three.js 설정
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.raycaster = null;
        this.mouse = new THREE.Vector2();
        
        // 상자 그룹들 (클릭 감지용)
        this.boxGroups = [];
        
        // 애니메이션
        this.animationId = null;
        
        // 색상 설정 (kwon3d 원본)
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
        this.container.style.width = '100%';
        this.container.style.height = '100vh';
        this.container.style.position = 'relative';
        this.container.style.background = 'transparent';

        // Three.js Scene 생성
        this.scene = new THREE.Scene();
        this.scene.background = null; // 투명 배경 (CSS에서 처리)

        // Camera 설정 (2개 상자를 모두 보이도록 조정)
        this.camera = new THREE.PerspectiveCamera(
            40,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        // 2개 상자가 나란히 있을 때 둘 다 보이도록 카메라를 더 뒤로 이동
        if (this.products.length === 2) {
            this.camera.position.set(0, 4, 8);
        } else {
            // 상품이 1개일 때는 kwon3d 원본과 동일
            this.camera.position.set(4, 3, 6);
        }
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

        // OrbitControls 초기화
        this.initControls();
        
        // 조명 설정 (kwon3d 원본과 동일)
        this.setupLighting();
        
        // 탁자와 상자들 생성
        this.createTable();
        this.createBoxes();
        
        // 이벤트 리스너
        this.setupEventListeners();
        
        // 애니메이션 시작
        this.animate();
        
        // 리사이즈 핸들러
        window.addEventListener('resize', () => this.handleResize());
    }

    initControls() {
        // OrbitControls가 로드될 때까지 대기
        const checkControls = () => {
            if (typeof THREE !== 'undefined' && typeof OrbitControls !== 'undefined') {
                if (typeof THREE.OrbitControls === 'undefined') {
                    THREE.OrbitControls = OrbitControls;
                }
                
                this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enablePan = false;
                this.controls.enableZoom = true;
                this.controls.minPolarAngle = 0;
                this.controls.maxPolarAngle = Math.PI / 2.2; // 탁자 아래로 가지 않도록
                this.controls.autoRotate = false;
                this.controls.target.set(0, 0.5, 0);
                this.controls.update();
            } else {
                setTimeout(checkControls, 100);
            }
        };
        checkControls();
    }

    setupLighting() {
        // Ambient Light (kwon3d 원본)
        const ambientLight = new THREE.AmbientLight(0xffddaa, 0.4);
        this.scene.add(ambientLight);
        
        // Main Spotlight (kwon3d 원본)
        const spotLight = new THREE.SpotLight(0xfff5cc, 2);
        spotLight.position.set(5, 8, 5);
        spotLight.angle = 0.4;
        spotLight.penumbra = 0.5;
        spotLight.castShadow = true;
        spotLight.shadow.mapSize.width = 1024;
        spotLight.shadow.mapSize.height = 1024;
        spotLight.shadow.bias = -0.0001;
        this.scene.add(spotLight);
        
        // Fill Light (kwon3d 원본)
        const fillLight = new THREE.PointLight(0xbd5e5e, 0.5);
        fillLight.position.set(-5, 2, -5);
        this.scene.add(fillLight);
        
        // Rim Light (kwon3d 원본)
        const rimLight = new THREE.SpotLight(0xffd700, 3);
        rimLight.position.set(0, 5, -8);
        rimLight.distance = 15;
        this.scene.add(rimLight);
    }

    createTable() {
        // 탁자 그룹
        const tableGroup = new THREE.Group();
        tableGroup.position.set(0, -1, 0);
        
        // 탁자 메시 (kwon3d 원본: cylinderGeometry)
        const tableGeometry = new THREE.CylinderGeometry(4, 4, 0.2, 64);
        const tableMaterial = new THREE.MeshStandardMaterial({
            color: 0x222222,
            roughness: 0.1,
            metalness: 0.2,
            envMapIntensity: 1
        });
        const tableMesh = new THREE.Mesh(tableGeometry, tableMaterial);
        tableMesh.position.set(0, -0.1, 0);
        tableMesh.receiveShadow = true;
        tableGroup.add(tableMesh);
        
        // ContactShadows (kwon3d 원본 스타일)
        // Three.js의 ContactShadows는 @react-three/drei의 기능이므로
        // 순수 Three.js로는 PlaneGeometry + ShadowMaterial로 대체
        const shadowPlane = new THREE.Mesh(
            new THREE.PlaneGeometry(10, 10),
            new THREE.ShadowMaterial({ opacity: 0.7 })
        );
        shadowPlane.rotation.x = -Math.PI / 2;
        shadowPlane.position.set(0, 0.01, 0);
        shadowPlane.receiveShadow = true;
        tableGroup.add(shadowPlane);
        
        this.scene.add(tableGroup);
    }

    createBoxes() {
        // 상품이 2개일 때: 왼쪽(-2, 0, 0), 오른쪽(2, 0, 0)
        // 상품이 1개일 때: 중앙(0, 0, 0)
        
        const positions = this.products.length === 2 
            ? [[-2, 0, 0], [2, 0, 0]]  // 왼쪽, 오른쪽
            : [[0, 0, 0]];  // 중앙
        
        this.products.forEach((product, index) => {
            if (index >= positions.length) return;
            
            const position = positions[index];
            const boxGroup = this.createSingleBox(product, position, index);
            this.boxGroups.push({ group: boxGroup, product: product });
            this.scene.add(boxGroup);
        });
    }

    createSingleBox(product, position, index) {
        const boxGroup = new THREE.Group();
        boxGroup.position.set(...position);
        
        // 상자 본체 (간단한 BoxGeometry로 구현)
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
        
        // 텍스트 추가 (Canvas Texture 사용)
        this.createText(boxGroup, product);
        
        // 뚜껑 추가
        this.createLid(boxGroup);
        
        // 클릭 감지를 위한 사용자 데이터 저장
        boxGroup.userData = {
            productId: product.id,
            productType: product.type,
            isActive: product.is_active === 'true' || product.is_active === true
        };
        
        return boxGroup;
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

    createText(parent, product) {
        // Canvas를 사용한 텍스트 텍스처 생성
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 512;
        const context = canvas.getContext('2d');

        // 배경 투명
        context.clearRect(0, 0, canvas.width, canvas.height);

        // 제목 텍스트
        const title = product.type === 'event' ? '🎉 토큰 이벤트' : '⏳ 기간 이벤트';
        context.fillStyle = '#ffdb4d';
        context.font = 'bold 80px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.strokeStyle = '#FFFFFF';
        context.lineWidth = 8;
        context.strokeText(title, canvas.width / 2, 120);
        context.fillText(title, canvas.width / 2, 120);

        // 서브타이틀
        context.fillStyle = '#ffe6b3';
        context.font = '48px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 4;
        context.strokeText('Welcome Event', canvas.width / 2, 200);
        context.fillText('Welcome Event', canvas.width / 2, 200);

        // 메인 혜택
        let mainBenefit = '';
        if (product.type === 'event') {
            mainBenefit = `신규 가입 혜택 (${product.token_amount || product.token || 0}토큰)`;
        } else {
            mainBenefit = `신규 가입 혜택 (${product.duration_days || product.duration || 0}일 무료)`;
        }
        
        context.fillStyle = '#ffffff';
        context.font = 'bold 60px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 6;
        context.strokeText(mainBenefit, canvas.width / 2, 300);
        context.fillText(mainBenefit, canvas.width / 2, 300);

        // 설명
        let description = '';
        if (product.type === 'event') {
            const tokenAmount = product.token_amount || product.token || 0;
            description = `${tokenAmount}개의 무료 토큰이\n즉시 지급됩니다.`;
        } else {
            const durationDays = product.duration_days || product.duration || 0;
            description = `${durationDays}일 동안 무료 체험이\n제공됩니다.`;
        }
        
        context.fillStyle = '#ffedcc';
        context.font = '40px Arial';
        context.strokeStyle = '#000000';
        context.lineWidth = 4;
        const lines = description.split('\n');
        lines.forEach((line, i) => {
            context.strokeText(line, canvas.width / 2, 380 + i * 50);
            context.fillText(line, canvas.width / 2, 380 + i * 50);
        });

        // 텍스처 생성
        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;
        texture.anisotropy = 16;

        // 텍스트 평면 생성
        const textGeometry = new THREE.PlaneGeometry(1.5, 0.75);
        const textMaterial = new THREE.MeshStandardMaterial({
            map: texture,
            transparent: true,
            side: THREE.DoubleSide
        });
        const textMesh = new THREE.Mesh(textGeometry, textMaterial);
        textMesh.position.set(0, this.boxHeight / 2, this.boxDepth / 2 + 0.07);
        parent.add(textMesh);
    }

    createLid(parent) {
        const hingePosition = [0, this.boxHeight, -this.boxDepth / 2];
        
        const lidGroup = new THREE.Group();
        lidGroup.position.set(...hingePosition);

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

        lidGroup.add(lidGroupInner);
        parent.add(lidGroup);
    }

    createBow(parent) {
        const bowGroup = new THREE.Group();
        bowGroup.position.set(0, this.lidHeight / 2 + 0.1, 0);
        
        // Loops
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
        
        // Center Knot
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

    setupEventListeners() {
        // Raycaster 초기화
        this.raycaster = new THREE.Raycaster();
        
        // 마우스 클릭 이벤트
        this.renderer.domElement.addEventListener('click', (event) => {
            this.onMouseClick(event);
        });
        
        // 마우스 이동 이벤트 (호버 효과)
        this.renderer.domElement.addEventListener('mousemove', (event) => {
            this.onMouseMove(event);
        });
    }

    onMouseClick(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(
            this.boxGroups.map(bg => bg.group),
            true
        );
        
        if (intersects.length > 0) {
            // 가장 가까운 객체 찾기
            const clickedObject = intersects[0].object;
            
            // 상자 그룹 찾기
            let clickedBoxGroup = null;
            for (const boxGroup of this.boxGroups) {
                if (boxGroup.group === clickedObject || 
                    boxGroup.group.children.includes(clickedObject) ||
                    this.isDescendant(boxGroup.group, clickedObject)) {
                    clickedBoxGroup = boxGroup;
                    break;
                }
            }
            
            if (clickedBoxGroup && clickedBoxGroup.product) {
                const product = clickedBoxGroup.product;
                
                // 해당 상품의 구매 버튼 찾아서 클릭 이벤트 트리거
                const buttons = document.querySelectorAll('.btn-purchase-fullscreen');
                buttons.forEach(btn => {
                    if (btn.getAttribute('data-id') == product.id) {
                        btn.click();
                    }
                });
            }
        }
    }

    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(
            this.boxGroups.map(bg => bg.group),
            true
        );
        
        // 호버 효과 (선택적)
        if (intersects.length > 0) {
            this.renderer.domElement.style.cursor = 'pointer';
        } else {
            this.renderer.domElement.style.cursor = 'grab';
        }
    }

    isDescendant(parent, child) {
        let node = child.parent;
        while (node !== null) {
            if (node === parent) {
                return true;
            }
            node = node.parent;
        }
        return false;
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        if (this.controls) {
            this.controls.update();
        }
        
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

    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        // 이벤트 리스너 제거
        window.removeEventListener('resize', this.handleResize);
    }
}

