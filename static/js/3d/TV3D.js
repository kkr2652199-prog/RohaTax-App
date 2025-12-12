/**
 * TV3D - 고급 3D TV 모델 (원본 TVModel.tsx 기반)
 * Deep Royal Navy 색상의 TV와 Luxury Soundbar를 포함한 완전한 디자인
 * 
 * @class TV3D
 * @description ProductFactory에서 사용하는 3D TV 가구 클래스
 */
class TV3D {
  /**
   * Static Material 공유 (WebGL 텍스처 유닛 최적화)
   */
  static sharedNavyMat = null;
  static sharedGoldMat = null;

  /**
   * 색상 테마 (원본과 동일)
   */
  static THEME = {
    GOLD: 0xC89664,        // 진한 금장색 (0xE6C288 → 0xC89664)
    GOLD_HIGH: 0xFFD700,   // 더 밝은 금색 (발광용)
    NAVY: 0x0A1A2F,        // Deep Royal Navy
    NAVY_LIGHT: 0x152a45,
    SPEAKER_BLACK: 0x111111
  };

  /**
   * Navy Material 가져오기
   */
  static getNavyMaterial() {
    if (!TV3D.sharedNavyMat) {
      TV3D.sharedNavyMat = new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY,
        roughness: 0.2,
        metalness: 0.5
      });
    }
    return TV3D.sharedNavyMat;
  }

  /**
   * Gold Material 가져오기
   */
  static getGoldMaterial() {
    if (!TV3D.sharedGoldMat) {
      TV3D.sharedGoldMat = new THREE.MeshStandardMaterial({
        color: TV3D.THEME.GOLD,
        metalness: 1.0,
        roughness: 0.1
      });
    }
    return TV3D.sharedGoldMat;
  }


  /**
   * Hi-Fi Speaker Driver 생성 - 대폭 확대
   */
  static createHiFiDriver(position) {
    const driverGroup = new THREE.Group();
    
    // Outer Ring (Trim) - 가장 큰 원 4개를 검정색으로 - 4배 확대
    const outerRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.48, 0.06, 16, 64), // 4배 확대 (0.12 → 0.48, 0.015 → 0.06)
      new THREE.MeshStandardMaterial({
        color: 0x000000, // 검정색 (0x444444 → 0x000000)
        metalness: 0.8,
        roughness: 0.2
      })
    );
    driverGroup.add(outerRing);
    
    // Surround (Rubber) - 4배 확대
    const surround = new THREE.Mesh(
      new THREE.TorusGeometry(0.4, 0.08, 16, 64), // 4배 확대 (0.10 → 0.4, 0.02 → 0.08)
      new THREE.MeshStandardMaterial({
        color: 0x111111,
        roughness: 0.6
      })
    );
    surround.position.z = -0.04; // 4배 확대에 맞춰 위치 조정 (-0.01 → -0.04)
    driverGroup.add(surround);
    
    // Speaker Ball (둥근 볼 4개 - 진한 금장색 광택) - 4배 확대
    const speakerBall = new THREE.Mesh(
      new THREE.SphereGeometry(0.32, 32, 32), // 4배 확대 (0.08 → 0.32)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.GOLD, // 진한 금장색
        roughness: 0.1, // 광택 효과 (0.4 → 0.1)
        metalness: 1.0, // 금속감
        emissive: TV3D.THEME.GOLD, // 발광도 진한 금장색으로
        emissiveIntensity: 0.2 // 발광 강도 증가 (0.15 → 0.2)
      })
    );
    speakerBall.position.z = -0.08; // 4배 확대에 맞춰 위치 조정 (-0.02 → -0.08)
    driverGroup.add(speakerBall);
    
    // Dust Cap (Gold Accent) - 4배 확대
    const dustCap = new THREE.Mesh(
      new THREE.SphereGeometry(0.14, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2), // 4배 확대 (0.035 → 0.14)
      TV3D.getGoldMaterial()
    );
    dustCap.position.z = 0.04; // 4배 확대에 맞춰 위치 조정 (0.01 → 0.04)
    driverGroup.add(dustCap);
    
    driverGroup.position.set(position[0], position[1], position[2]);
    return driverGroup;
  }

  /**
   * RoundedBox 대체 함수 (BoxGeometry + 모서리 처리)
   */
  static createRoundedBox(width, height, depth, radius = 0.02) {
    // 간단한 버전: BoxGeometry 사용 (원본의 RoundedBox와 유사한 느낌)
    const geometry = new THREE.BoxGeometry(width, height, depth);
    return geometry;
  }

  /**
   * 3D TV 모델 생성 (원본 TVModel.tsx 디자인 기반)
   * @param {Object} product - 상품 데이터 (선택적)
   * @param {THREE.Vector3|Object} position - 위치
   * @param {boolean} isPlaying - 재생 중 여부 (기본값: true)
   * @returns {THREE.Group} TV 모델 그룹
   */
  static createModel(product = null, position = new THREE.Vector3(0, 0, 0), isPlaying = true) {
    const group = new THREE.Group();
    
    // 위치 설정
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(
          position?.x || 0, 
          position?.y || 0, 
          position?.z || 0
        );

    // --- TV UNIT ---
    const tvGroup = new THREE.Group();
    tvGroup.position.set(0, 0.5, 0); // 천장 방향으로 조금 더 올림 (0.0 → 0.5)

    // TV Frame - Deep Navy (원본: RoundedBox) - 4배 확대
    const tvFrame = new THREE.Mesh(
      TV3D.createRoundedBox(14.0, 8.4, 0.32), // 4배 확대 (3.5 → 14.0, 2.1 → 8.4, 0.08 → 0.32)
      TV3D.getNavyMaterial()
    );
    tvFrame.castShadow = true;
    tvFrame.receiveShadow = true;
    tvGroup.add(tvFrame);

    // Gold Trim Border (TV 정면 테두리 패널 - 진한 금장색) - 프레임에 맞춰 4배 확대
    const goldTrim = new THREE.Mesh(
      new THREE.BoxGeometry(14.02, 8.42, 0.032), // 4배 확대 (3.505 → 14.02, 2.105 → 8.42, 0.008 → 0.032)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.GOLD, // 진한 금장색 (색상 유지)
        metalness: 0.7, // 빛 반사 효과 30% 감소 (1.0 → 0.7)
        roughness: 0.3, // 빛 반사 효과 30% 감소 (0.1 → 0.3)
        emissive: TV3D.THEME.GOLD, // 발광도 진한 금장색으로 (색상 유지)
        emissiveIntensity: 0.14 // 발광 강도 30% 감소 (0.2 → 0.14)
      })
    );
    goldTrim.position.z = 0.164; // 4배 확대에 맞춰 위치 조정 (0.041 → 0.164)
    tvGroup.add(goldTrim);

    // Active Border Glow (재생 중일 때만) - 화면 크기에 맞춰 4배 확대
    if (isPlaying) {
      const borderGlow = new THREE.Mesh(
        new THREE.BoxGeometry(13.4, 7.8, 0.04), // 4배 확대 (3.35 → 13.4, 1.95 → 7.8, 0.01 → 0.04)
        new THREE.MeshBasicMaterial({
          color: 0x4488ff,
          transparent: true,
          opacity: 0.15
        })
      );
      borderGlow.position.z = 0.18; // 4배 확대에 맞춰 위치 조정 (0.045 → 0.18)
      tvGroup.add(borderGlow);
    }

    // Back Panel (원본: RoundedBox) - 프레임에 맞춰 4배 확대
    const backPanel = new THREE.Mesh(
      TV3D.createRoundedBox(13.2, 7.6, 0.6), // 4배 확대 (3.3 → 13.2, 1.9 → 7.6, 0.15 → 0.6)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY,
        roughness: 0.8
      })
    );
    backPanel.position.set(0, 0, -0.4); // 4배 확대에 맞춰 위치 조정 (-0.1 → -0.4)
    tvGroup.add(backPanel);

    // The Screen (영상 코드 삭제 - 나중에 별도 추가 예정) - 4배 확대 (빛 반사 효과 제거)
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(13.4, 7.8), // 4배 확대 (3.35 → 13.4, 1.95 → 7.8)
      new THREE.MeshStandardMaterial({
        color: 0x000000,
        roughness: 0.9, // 무광 효과 (0.05 → 0.9)
        metalness: 0.1 // 반사 효과 감소 (0.9 → 0.1)
      })
    );
    screen.position.set(0, 0, 0.208); // 4배 확대에 맞춰 위치 조정 (0.052 → 0.208, z-fighting 방지)
    tvGroup.add(screen);

    // Standby Light (초록색 LED 불빛 방향이 TV 정면 정의 기준점)
    // 위치: (6.0, -3.6, 0.24) - 이 LED가 TV의 정면(프론트) 방향을 정의하는 기준점 (4배 확대)
    const standbyLight = new THREE.Mesh(
      new THREE.CircleGeometry(0.02, 16), // 4배 확대 (0.005 → 0.02)
      new THREE.MeshBasicMaterial({
        color: isPlaying ? 0x00ff00 : 0xff0000 // 재생 중: 초록색, 대기 중: 빨간색
      })
    );
    standbyLight.position.set(6.0, -3.6, 0.24); // 4배 확대에 맞춰 위치 조정 (1.5 → 6.0, -0.9 → -3.6, 0.06 → 0.24)
    tvGroup.add(standbyLight);

    // Ambilight (재생 중일 때만) - 4배 확대
    if (isPlaying) {
      const ambilight = new THREE.PointLight(0x4488ff, 1.0, 16); // 거리도 4배 확대 (4 → 16)
      ambilight.position.set(0, 0, 4.0); // 4배 확대에 맞춰 위치 조정 (1.0 → 4.0)
      ambilight.decay = 2;
      tvGroup.add(ambilight);
    }

    group.add(tvGroup);

    // --- LUXURY SOUNDBAR SLIM REDESIGN ---
    const soundbarGroup = new THREE.Group();
    soundbarGroup.position.set(0, -4.7, 0.208); // Y: -4.7 (천장 방향으로 조금 더 올림, -5.2 → -4.7), Z: TV 검정색 패널(화면)과 동일한 위치(0.208)

    // 1. Main Body (Slimmer Navy Cabinet) - 4배 확대
    const soundbarBody = new THREE.Mesh(
      TV3D.createRoundedBox(9.6, 1.12, 0.6), // 4배 확대 (2.4 → 9.6, 0.28 → 1.12, 0.15 → 0.6)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY,
        roughness: 0.4,
        metalness: 0.4
      })
    );
    soundbarBody.castShadow = true;
    soundbarBody.receiveShadow = true;
    soundbarGroup.add(soundbarBody);

    // 2. Front Faceplate (Brushed Gold Aluminum - 진한 금장색 광택) - 4배 확대
    const faceplate = new THREE.Mesh(
      new THREE.BoxGeometry(9.4, 0.96, 0.04), // 4배 확대 (2.35 → 9.4, 0.24 → 0.96, 0.01 → 0.04)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.GOLD, // 진한 금장색
        roughness: 0.1, // 광택 효과 (0.3 → 0.1)
        metalness: 1.0, // 금속감 강화 (0.9 → 1.0)
        emissive: TV3D.THEME.GOLD, // 발광도 진한 금장색으로
        emissiveIntensity: 0.25 // 발광 강도 증가 (0.15 → 0.25)
      })
    );
    faceplate.position.z = 0.304; // 4배 확대에 맞춰 위치 조정 (0.076 → 0.304)
    soundbarGroup.add(faceplate);

    // 3. Speaker Drivers (Hi-Fi Elements) - 4배 확대에 맞춰 위치 조정
    const driverPositions = [
      [-3.6, 0, 0.32], // 4배 확대 (-0.9 → -3.6, 0.08 → 0.32)
      [3.6, 0, 0.32],  // 4배 확대 (0.9 → 3.6, 0.08 → 0.32)
      [-2.2, 0, 0.32], // 4배 확대 (-0.55 → -2.2, 0.08 → 0.32)
      [2.2, 0, 0.32]   // 4배 확대 (0.55 → 2.2, 0.08 → 0.32)
    ];
    
    driverPositions.forEach(pos => {
      const driver = TV3D.createHiFiDriver(pos);
      soundbarGroup.add(driver);
    });

    // 4. Center Control Cluster (The "Island") - 4배 확대
    const controlGroup = new THREE.Group();
    controlGroup.position.set(0, 0, 0.32); // 4배 확대에 맞춰 위치 조정 (0.08 → 0.32)

    // Control Panel Background (Navy Pill Shape) - 4배 확대
    const controlBg = new THREE.Mesh(
      new THREE.BoxGeometry(2.8, 0.64, 0.04), // 4배 확대 (0.7 → 2.8, 0.16 → 0.64, 0.01 → 0.04)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    controlBg.position.z = 0.02; // 4배 확대에 맞춰 위치 조정 (0.005 → 0.02)
    controlGroup.add(controlBg);

    // 좌우 원형 끝부분 - 4배 확대
    const leftEnd = new THREE.Mesh(
      new THREE.CylinderGeometry(0.32, 0.32, 0.04, 32), // 4배 확대 (0.08 → 0.32, 0.01 → 0.04)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    leftEnd.rotation.x = Math.PI / 2;
    leftEnd.position.set(-1.4, 0, 0.02); // 4배 확대에 맞춰 위치 조정 (-0.35 → -1.4, 0.005 → 0.02)
    controlGroup.add(leftEnd);

    const rightEnd = new THREE.Mesh(
      new THREE.CylinderGeometry(0.32, 0.32, 0.04, 32), // 4배 확대 (0.08 → 0.32, 0.01 → 0.04)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    rightEnd.rotation.x = Math.PI / 2;
    rightEnd.position.set(1.4, 0, 0.02); // 4배 확대에 맞춰 위치 조정 (0.35 → 1.4, 0.005 → 0.02)
    controlGroup.add(rightEnd);

    // 컨트롤 버튼들 (간단한 버전) - 4배 확대
    // Rewind 버튼
    const rewindBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.24, 0.24, 0.08, 32), // 4배 확대 (0.06 → 0.24, 0.02 → 0.08)
      new THREE.MeshStandardMaterial({
        color: 0xeeeeee,
        roughness: 0.2,
        metalness: 0.8
      })
    );
    rewindBtn.rotation.x = Math.PI / 2;
    rewindBtn.position.set(-0.88, 0, 0.06); // 4배 확대에 맞춰 위치 조정 (-0.22 → -0.88, 0.015 → 0.06)
    controlGroup.add(rewindBtn);

    // Play/Pause 버튼 (중앙, 더 큼) - 플레이 버튼을 누르면 일시정지되는 구조
    // 버튼 원: 화이트, 아이콘: 레드색 - 4배 확대
    const playPauseBtnGroup = new THREE.Group();
    playPauseBtnGroup.position.set(0, 0, 0.06); // 4배 확대에 맞춰 위치 조정 (0.015 → 0.06)
    
    // 버튼 본체 (원) - 항상 화이트
    const playPauseBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.32, 0.32, 0.08, 32), // 4배 확대 (0.08 → 0.32, 0.02 → 0.08)
      new THREE.MeshStandardMaterial({
        color: 0xffffff, // 화이트 (isPlaying 상태와 무관하게 항상 화이트)
        roughness: 0.2,
        metalness: 0.8
      })
    );
    playPauseBtn.rotation.x = Math.PI / 2;
    playPauseBtnGroup.add(playPauseBtn);
    
    // 아이콘 표현 (플레이/일시정지) - 항상 레드색 - 4배 확대
    if (isPlaying) {
      // 일시정지 상태: 두 개의 세로 막대 (||) - 레드색
      const pauseBar1 = new THREE.Mesh(
        new THREE.BoxGeometry(0.06, 0.16, 0.02), // 4배 확대 (0.015 → 0.06, 0.04 → 0.16, 0.005 → 0.02)
        new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
      );
      pauseBar1.position.set(-0.06, 0, 0.048); // 4배 확대에 맞춰 위치 조정 (-0.015 → -0.06, 0.012 → 0.048)
      playPauseBtnGroup.add(pauseBar1);
      
      const pauseBar2 = new THREE.Mesh(
        new THREE.BoxGeometry(0.06, 0.16, 0.02), // 4배 확대 (0.015 → 0.06, 0.04 → 0.16, 0.005 → 0.02)
        new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
      );
      pauseBar2.position.set(0.06, 0, 0.048); // 4배 확대에 맞춰 위치 조정 (0.015 → 0.06, 0.012 → 0.048)
      playPauseBtnGroup.add(pauseBar2);
    } else {
      // 재생 상태: 삼각형 (▶) - 레드색
      const playTriangle = new THREE.Mesh(
        new THREE.ConeGeometry(0.1, 0.18, 3), // 4배 확대 (0.025 → 0.1, 0.045 → 0.18)
        new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
      );
      playTriangle.rotation.x = Math.PI / 2;
      playTriangle.rotation.z = -Math.PI / 2;
      playTriangle.position.set(0.04, 0, 0.048); // 4배 확대에 맞춰 위치 조정 (0.01 → 0.04, 0.012 → 0.048)
      playPauseBtnGroup.add(playTriangle);
    }
    
    controlGroup.add(playPauseBtnGroup);

    // Forward 버튼 - 4배 확대
    const forwardBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.24, 0.24, 0.08, 32), // 4배 확대 (0.06 → 0.24, 0.02 → 0.08)
      new THREE.MeshStandardMaterial({
        color: 0xeeeeee,
        roughness: 0.2,
        metalness: 0.8
      })
    );
    forwardBtn.rotation.x = Math.PI / 2;
    forwardBtn.position.set(0.88, 0, 0.06); // 4배 확대에 맞춰 위치 조정 (0.22 → 0.88, 0.015 → 0.06)
    controlGroup.add(forwardBtn);

    soundbarGroup.add(controlGroup);
    group.add(soundbarGroup);

    // 전체 그룹 위치 설정
    group.position.copy(pos);

    // 그림자 설정
    group.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    // 상품 데이터 저장
    if (product) {
      group.userData.productData = product;
    }

    // 애니메이션 플래그 설정 (기본값: false - 사용자가 직접 제어할 때만 회전)
    group.userData.isAnimating = false; // 자동 회전 비활성화
    group.userData.rotationSpeed = 0.005;
    group.userData.isPlaying = isPlaying;

    console.log('✅ [TV3D] 고급 3D TV 모델 생성 완료 (원본 디자인 기반)');
    return group;
  }

  /**
   * 회전 애니메이션 업데이트
   * @param {THREE.Group} group - 애니메이션을 적용할 그룹
   */
  static animate(group) {
    if (!group || !group.userData.isAnimating) return;
    
    // Y축 중심으로 천천히 회전
    const rotationSpeed = group.userData.rotationSpeed || 0.005;
    group.rotation.y += rotationSpeed;
  }
}

// 전역 객체로 노출
if (typeof window !== 'undefined') {
  window.TV3D = TV3D;
}

// ES6 모듈로도 노출 (선택적)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TV3D;
}
