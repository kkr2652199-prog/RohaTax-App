/**
 * MagicFire - 불꽃 효과가 있는 액자 가구
 * 외부 CodePen 소스를 Three.js로 변환
 */
class MagicFire {
  constructor(options = {}) {
    this.group = new THREE.Group();
    this.options = {
      imageUrl: options.imageUrl || 'https://assets.codepen.io/12550455/good-place-2.jpg',
      particleCount: options.particleCount || 25, // 50 -> 25로 반으로 줄임
      frameWidth: options.frameWidth || 50,      // TV(14.0)보다 크게: 50
      frameHeight: options.frameHeight || 28,     // TV(8.4)보다 크게: 28
      frameDepth: options.frameDepth || 2.0      // 깊이 유지: 2.0
    };
    
    this.particles = [];
    this.particles2 = [];
    this.particles3 = [];
    this.animationId = null;
    
    this.createFrame();
    this.createImage();
    this.createFireParticles();
  }
  
  /**
   * 액자 프레임 생성 (프레임 삭제됨)
   */
  createFrame() {
    // 프레임이 삭제되어 빈 메서드로 유지
  }
  
  /**
   * 이미지 평면 생성
   */
  createImage() {
    const { frameWidth, frameHeight } = this.options;
    // 프레임이 없으므로 전체 크기 사용
    const imageWidth = frameWidth;
    const imageHeight = frameHeight;
    
    // 텍스처 로더
    const loader = new THREE.TextureLoader();
    loader.load(
      this.options.imageUrl,
      (texture) => {
        texture.minFilter = THREE.LinearFilter;
        texture.magFilter = THREE.LinearFilter;
        
        const imageMat = new THREE.MeshBasicMaterial({
          map: texture,
          side: THREE.DoubleSide
        });
        
        const imagePlane = new THREE.Mesh(
          new THREE.PlaneGeometry(imageWidth, imageHeight),
          imageMat
        );
        imagePlane.position.z = -this.options.frameDepth / 2 + 0.01;
        this.group.add(imagePlane);
      },
      undefined,
      (error) => {
        console.warn('⚠️ [MagicFire] 이미지 로드 실패:', error);
        // 대체 이미지 (단색 평면)
        const fallbackMat = new THREE.MeshBasicMaterial({
          color: 0x333333
        });
        const fallbackPlane = new THREE.Mesh(
          new THREE.PlaneGeometry(imageWidth, imageHeight),
          fallbackMat
        );
        fallbackPlane.position.z = -this.options.frameDepth / 2 + 0.01;
        this.group.add(fallbackPlane);
      }
    );
  }
  
  /**
   * 불꽃 파티클 생성
   */
  createFireParticles() {
    const { particleCount } = this.options;
    
    // 파티클 재질 생성 (더 자연스러운 불꽃 효과)
    const createParticleMaterial = (size, color) => {
      const canvas = document.createElement('canvas');
      canvas.width = 256; // 해상도 증가로 더 선명한 그라데이션
      canvas.height = 256;
      const ctx = canvas.getContext('2d');
      
      // 방사형 그라데이션 (더 자연스러운 불꽃 효과)
      const center = 128;
      const gradient = ctx.createRadialGradient(center, center, 0, center, center, 128);
      
      // 자연스럽고 눈이 편안한 불꽃 색상 (중앙 밝기 조정)
      if (color === 'yellow') {
        gradient.addColorStop(0, 'rgba(255, 220, 150, 0.6)');      // 중심: 밝은 노란색 (자연스러운 밝기)
        gradient.addColorStop(0.15, 'rgba(255, 200, 100, 0.7)');    // 약간 확산 (자연스러운 전환)
        gradient.addColorStop(0.3, 'rgba(255, 160, 60, 0.6)');    // 주황색으로 전환 (자연스러운 전환)
        gradient.addColorStop(0.5, 'rgba(255, 120, 40, 0.45)');    // 진한 주황 (자연스러운 전환)
        gradient.addColorStop(0.7, 'rgba(255, 80, 0, 0.25)');      // 빨간 주황 (자연스러운 전환)
        gradient.addColorStop(0.9, 'rgba(255, 40, 0, 0.1)');      // 약한 빨강
        gradient.addColorStop(1, 'rgba(255, 40, 0, 0)');          // 완전 투명
      } else {
        gradient.addColorStop(0, 'rgba(255, 240, 180, 0.55)');     // 중심: 밝은 흰색 (자연스러운 밝기)
        gradient.addColorStop(0.15, 'rgba(255, 220, 140, 0.65)');    // 약간 노란색 (자연스러운 전환)
        gradient.addColorStop(0.3, 'rgba(255, 180, 80, 0.55)');    // 주황색 (자연스러운 전환)
        gradient.addColorStop(0.5, 'rgba(255, 140, 50, 0.4)');   // 진한 주황 (자연스러운 전환)
        gradient.addColorStop(0.7, 'rgba(255, 90, 0, 0.22)');     // 빨간 주황 (자연스러운 전환)
        gradient.addColorStop(0.9, 'rgba(255, 50, 0, 0.08)');     // 약한 빨강
        gradient.addColorStop(1, 'rgba(255, 50, 0, 0)');          // 완전 투명
      }
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 256, 256);
      
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
      
      return new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
    };
    
    // 액자 내부 영역 계산 (프레임이 없으므로 전체 영역 사용)
    const frameThickness = 0; // 프레임 삭제됨
    const innerWidth = this.options.frameWidth;  // 전체 너비
    const innerHeight = this.options.frameHeight; // 전체 높이
    const bottomY = -this.options.frameHeight / 2; // 하단 위치
    const topY = this.options.frameHeight / 2;      // 상단 위치
    
    // 첫 번째 파티클 그룹 (작은 불꽃) - 원본처럼 자연스럽게 위로 올라가는 효과
    const particleMat1 = createParticleMaterial(0.1, 'white');
    for (let i = 0; i < particleCount; i++) {
      const sprite = new THREE.Sprite(particleMat1);
      sprite.scale.set(0.008, 0.02, 1); // 작은 불꽃 (가로폭 대폭 감소)
      // 구름처럼 밀집된 시작 위치 (왼쪽, 위로 이동)
      const cloudRadius = 0.15; // 구름 반경
      const cloudCenterX = 0.3; // 왼쪽으로 이동
      const cloudCenterY = bottomY + 0.7; // 위로 이동
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * cloudRadius;
      const startX = cloudCenterX + Math.cos(angle) * radius; // 구름 형태로 분산
      const startY = cloudCenterY + Math.sin(angle) * radius * 0.5; // 구름 형태로 분산
      sprite.position.set(
        startX,
        startY,
        -this.options.frameDepth / 2 + 0.02 // 이미지와 붙이기
      );
      sprite.userData = {
        startY: startY,
        startX: startX,
        endY: topY - 0.1, // 액자 상단까지 올라감
        animationDelay: Math.random() * 3.0, // 각 파티클마다 다른 delay (0~3초)
        animationDuration: 2.0 + Math.random() * 1.5, // 올라가는 시간 (2~3.5초)
        swaySpeed: 1.5 + Math.random() * 1.0, // 좌우 흔들림 속도
        swayAmount: 0.02 + Math.random() * 0.03, // 좌우 흔들림 범위
        life: 0,
        phase: Math.random() * Math.PI * 2
      };
      sprite.material.opacity = 0; // 초기에는 보이지 않음
      this.particles.push(sprite);
      this.group.add(sprite);
    }
    
    // 두 번째 파티클 그룹 (중간 불꽃) - 원본처럼 자연스럽게 위로 올라가는 효과
    const particleMat2 = createParticleMaterial(0.3, 'yellow');
    for (let i = 0; i < particleCount; i++) {
      const sprite = new THREE.Sprite(particleMat2);
      sprite.scale.set(0.025, 0.06, 1); // 중간 불꽃 (가로폭 대폭 감소)
      // 구름처럼 밀집된 시작 위치 (왼쪽, 위로 이동)
      const cloudRadius = 0.18; // 구름 반경
      const cloudCenterX = 0.3; // 왼쪽으로 이동
      const cloudCenterY = bottomY + 0.72; // 위로 이동
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * cloudRadius;
      const startX = cloudCenterX + Math.cos(angle) * radius; // 구름 형태로 분산
      const startY = cloudCenterY + Math.sin(angle) * radius * 0.5; // 구름 형태로 분산
      sprite.position.set(
        startX,
        startY,
        -this.options.frameDepth / 2 + 0.02 // 이미지와 붙이기
      );
      sprite.userData = {
        startY: startY,
        startX: startX,
        endY: topY - 0.15,
        animationDelay: Math.random() * 3.5,
        animationDuration: 2.5 + Math.random() * 2.0, // 더 느리게 올라감
        swaySpeed: 1.2 + Math.random() * 0.8,
        swayAmount: 0.025 + Math.random() * 0.035,
        life: 0,
        phase: Math.random() * Math.PI * 2
      };
      sprite.material.opacity = 0; // 초기에는 보이지 않음
      this.particles2.push(sprite);
      this.group.add(sprite);
    }
    
    // 세 번째 파티클 그룹 (큰 불꽃) - 원본처럼 자연스럽게 위로 올라가는 효과
    const particleMat3 = createParticleMaterial(0.8, 'yellow');
    for (let i = 0; i < particleCount; i++) {
      const sprite = new THREE.Sprite(particleMat3);
      sprite.scale.set(0.05, 0.12, 1); // 큰 불꽃 (가로폭 대폭 감소)
      // 구름처럼 밀집된 시작 위치 (왼쪽, 위로 이동)
      const cloudRadius = 0.2; // 구름 반경
      const cloudCenterX = 0.3; // 왼쪽으로 이동
      const cloudCenterY = bottomY + 0.75; // 위로 이동
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * cloudRadius;
      const startX = cloudCenterX + Math.cos(angle) * radius; // 구름 형태로 분산
      const startY = cloudCenterY + Math.sin(angle) * radius * 0.5; // 구름 형태로 분산
      sprite.position.set(
        startX,
        startY,
        -this.options.frameDepth / 2 + 0.02 // 이미지와 붙이기
      );
      sprite.userData = {
        startY: startY,
        startX: startX,
        endY: topY - 0.2,
        animationDelay: Math.random() * 4.0,
        animationDuration: 3.0 + Math.random() * 2.5, // 가장 느리게 올라감
        swaySpeed: 1.0 + Math.random() * 0.6,
        swayAmount: 0.03 + Math.random() * 0.04,
        life: 0,
        phase: Math.random() * Math.PI * 2
      };
      sprite.material.opacity = 0; // 초기에는 보이지 않음
      this.particles3.push(sprite);
      this.group.add(sprite);
    }
  }
  
  /**
   * 애니메이션 업데이트 (비활성화됨)
   */
  animate() {
    // 애니메이션 효과 삭제됨
  }
  
  /**
   * 그룹 반환
   */
  getGroup() {
    return this.group;
  }
  
  /**
   * 정리 (메모리 해제)
   */
  dispose() {
    // 파티클 재질 정리
    [...this.particles, ...this.particles2, ...this.particles3].forEach(particle => {
      if (particle.material) {
        particle.material.dispose();
        if (particle.material.map) {
          particle.material.map.dispose();
        }
      }
    });
    
    this.particles = [];
    this.particles2 = [];
    this.particles3 = [];
  }
}

// 전역 객체로 노출 (ES6 모듈과 호환)
if (typeof window !== 'undefined') {
  window.MagicFire = MagicFire;
}
console.log("✅ [MagicFire] 전역 객체로 노출 완료:", typeof window !== 'undefined' ? typeof window.MagicFire : 'N/A');

