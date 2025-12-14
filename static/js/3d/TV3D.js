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
    
    // Outer Ring (Trim) - 가장 큰 원 4개를 검정색으로 - 4배 확대 + 10% 추가 확대
    const outerRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.528, 0.066, 16, 64), // 4배 확대 + 10% 추가 (0.48 → 0.528, 0.06 → 0.066)
      new THREE.MeshStandardMaterial({
        color: 0x000000, // 검정색 (0x444444 → 0x000000)
        metalness: 0.8,
        roughness: 0.2
      })
    );
    driverGroup.add(outerRing);
    
    // Surround (Rubber) - 4배 확대 + 10% 추가 확대
    const surround = new THREE.Mesh(
      new THREE.TorusGeometry(0.44, 0.088, 16, 64), // 4배 확대 + 10% 추가 (0.4 → 0.44, 0.08 → 0.088)
      new THREE.MeshStandardMaterial({
        color: 0x111111,
        roughness: 0.6
      })
    );
    surround.position.z = -0.044; // 4배 확대 + 10% 추가 (-0.04 → -0.044)
    driverGroup.add(surround);
    
    // Speaker Ball (둥근 볼 4개 - 진한 금장색 광택) - 4배 확대 + 10% 추가 확대
    const speakerBall = new THREE.Mesh(
      new THREE.SphereGeometry(0.352, 32, 32), // 4배 확대 + 10% 추가 (0.32 → 0.352)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.GOLD, // 진한 금장색
        roughness: 0.1, // 광택 효과 (0.4 → 0.1)
        metalness: 1.0, // 금속감
        emissive: TV3D.THEME.GOLD, // 발광도 진한 금장색으로
        emissiveIntensity: 0.2 // 발광 강도 증가 (0.15 → 0.2)
      })
    );
    speakerBall.position.z = -0.088; // 4배 확대 + 10% 추가 (-0.08 → -0.088)
    driverGroup.add(speakerBall);
    
    // Dust Cap (Gold Accent) - 4배 확대 + 10% 추가 확대
    const dustCap = new THREE.Mesh(
      new THREE.SphereGeometry(0.154, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2), // 4배 확대 + 10% 추가 (0.14 → 0.154)
      TV3D.getGoldMaterial()
    );
    dustCap.position.z = 0.044; // 4배 확대 + 10% 추가 (0.04 → 0.044)
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
  static createModel(product = null, position = new THREE.Vector3(0, 0, 0), isPlaying = false) {
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

    // TV Frame - Deep Navy (원본: RoundedBox) - 4배 확대 + 10% 추가 확대
    const tvFrame = new THREE.Mesh(
      TV3D.createRoundedBox(15.4, 9.2, 0.35), // 4배 확대 + 10% 추가 (14.0 → 15.4, 8.4 → 9.2, 0.32 → 0.35)
      TV3D.getNavyMaterial()
    );
    tvFrame.castShadow = true;
    tvFrame.receiveShadow = true;
    tvGroup.add(tvFrame);

    // Gold Trim Border (TV 정면 테두리 패널 - 진한 금장색) - 프레임에 맞춰 4배 확대 + 10% 추가 확대
    const goldTrim = new THREE.Mesh(
      new THREE.BoxGeometry(15.4, 9.3, 0.035), // 4배 확대 + 10% 추가 (14.02 → 15.4, 8.42 → 9.3, 0.032 → 0.035)
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

    // Active Border Glow (재생 중일 때만) - 화면 크기에 맞춰 4배 확대 + 10% 추가 확대
    if (isPlaying) {
      const borderGlow = new THREE.Mesh(
        new THREE.BoxGeometry(14.7, 8.6, 0.044), // 4배 확대 + 10% 추가 (13.4 → 14.7, 7.8 → 8.6, 0.04 → 0.044)
        new THREE.MeshBasicMaterial({
          color: 0x4488ff,
          transparent: true,
          opacity: 0.15
        })
      );
      borderGlow.position.z = 0.18; // 4배 확대에 맞춰 위치 조정 (0.045 → 0.18)
      tvGroup.add(borderGlow);
    }

    // Back Panel (원본: RoundedBox) - 프레임에 맞춰 4배 확대 + 10% 추가 확대
    const backPanel = new THREE.Mesh(
      TV3D.createRoundedBox(14.5, 8.4, 0.66), // 4배 확대 + 10% 추가 (13.2 → 14.5, 7.6 → 8.4, 0.6 → 0.66)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY,
        roughness: 0.8
      })
    );
    backPanel.position.set(0, 0, -0.4); // 4배 확대에 맞춰 위치 조정 (-0.1 → -0.4)
    tvGroup.add(backPanel);

    // The Screen - 비디오 재생 기능 탑재
    // 비디오 엔진 탑재 (텍스처 생성 후 스크린에 적용)
    const video = document.createElement('video');
    video.src = '/static/videos/roha_conversion_demo.mp4.mp4'; // 로컬 영상 파일
    video.loop = false;
    video.playsInline = true;
    video.muted = true; // 자동 재생을 위해 음소거 (사용자 클릭 시 해제)
    video.preload = 'auto';
    
    // 비디오 텍스처 생성
    const videoTexture = new THREE.VideoTexture(video);
    videoTexture.minFilter = THREE.LinearFilter;
    videoTexture.magFilter = THREE.LinearFilter;
    
    // 스크린 메시 생성 (MeshBasicMaterial로 변경하여 비디오가 선명하게 보이도록)
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(14.7, 8.6), // 4배 확대 + 10% 추가 (13.4 → 14.7, 7.8 → 8.6)
      new THREE.MeshBasicMaterial({
        map: videoTexture // 비디오 텍스처 직접 적용
      })
    );
    screen.position.set(0, 0, 0.208); // 4배 확대에 맞춰 위치 조정 (0.052 → 0.208, z-fighting 방지)
    tvGroup.add(screen);
    
    // 비디오 첫 프레임으로 이동 (검은 화면 방지, 썸네일 노출)
    video.addEventListener('loadedmetadata', () => {
      video.currentTime = 0.1; // 0.1초로 이동하여 썸네일(첫 화면) 보여주기
    });

    // Standby Light (초록색 LED 불빛 방향이 TV 정면 정의 기준점)
    // 위치: (6.6, -4.0, 0.264) - 이 LED가 TV의 정면(프론트) 방향을 정의하는 기준점 (4배 확대 + 10% 추가)
    const standbyLight = new THREE.Mesh(
      new THREE.CircleGeometry(0.022, 16), // 4배 확대 + 10% 추가 (0.02 → 0.022)
      new THREE.MeshBasicMaterial({
        color: isPlaying ? 0x00ff00 : 0xff0000 // 재생 중: 초록색, 대기 중: 빨간색
      })
    );
    standbyLight.position.set(6.6, -4.0, 0.264); // 4배 확대 + 10% 추가 (6.0 → 6.6, -3.6 → -4.0, 0.24 → 0.264)
    tvGroup.add(standbyLight);

    // Ambilight (재생 중일 때만) - 4배 확대
    if (isPlaying) {
      const ambilight = new THREE.PointLight(0x4488ff, 1.0, 16); // 거리도 4배 확대 (4 → 16)
      ambilight.position.set(0, 0, 4.0); // 4배 확대에 맞춰 위치 조정 (1.0 → 4.0)
      ambilight.decay = 2;
      tvGroup.add(ambilight);
    }

    group.add(tvGroup);

    // --- 타임라인 패널 (Progress Bar) ---
    // TV 스크린과 사운드바 사이에 배치
    const progressCanvas = document.createElement('canvas');
    progressCanvas.width = 1200; // 고해상도
    progressCanvas.height = 150;
    const progressCtx = progressCanvas.getContext('2d');
    
    // 타임라인 그리기 함수
    const drawProgressBar = (currentTime, duration) => {
      if (!progressCtx || !duration) return;
      
      const width = progressCanvas.width;
      const height = progressCanvas.height;
      
      // 배경 초기화 (투명하게)
      progressCtx.clearRect(0, 0, width, height);
      
      // 진행률 계산
      const progress = duration > 0 ? currentTime / duration : 0;
      const progressWidth = width * progress;
      
      // 배경 선 (회색)
      progressCtx.strokeStyle = '#444444';
      progressCtx.lineWidth = 4;
      progressCtx.beginPath();
      progressCtx.moveTo(20, height / 2);
      progressCtx.lineTo(width - 20, height / 2);
      progressCtx.stroke();
      
      // 진행 선 (빨간색)
      if (progressWidth > 0) {
        progressCtx.strokeStyle = '#ff0000';
        progressCtx.lineWidth = 4;
        progressCtx.beginPath();
        progressCtx.moveTo(20, height / 2);
        progressCtx.lineTo(20 + progressWidth, height / 2);
        progressCtx.stroke();
      }
      
      // 시간 텍스트 (우측 하단) - 그림자 효과로 가독성 강화
      const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      };
      
      // 텍스트 그림자 설정
      progressCtx.shadowColor = 'black';
      progressCtx.shadowBlur = 4;
      progressCtx.shadowOffsetX = 2;
      progressCtx.shadowOffsetY = 2;
      
      progressCtx.fillStyle = '#ffffff';
      progressCtx.font = 'bold 32px Arial';
      const timeText = `${formatTime(currentTime)} / ${formatTime(duration)}`;
      const textMetrics = progressCtx.measureText(timeText);
      progressCtx.fillText(timeText, width - textMetrics.width - 20, 50); // 상단으로 이동 (height - 20 → 50)
      
      // 그림자 효과 초기화
      progressCtx.shadowColor = 'transparent';
      progressCtx.shadowBlur = 0;
      progressCtx.shadowOffsetX = 0;
      progressCtx.shadowOffsetY = 0;
    };
    
    // 초기 타임라인 그리기
    drawProgressBar(0, 0);
    
    // 캔버스 텍스처 생성
    const progressTexture = new THREE.CanvasTexture(progressCanvas);
    progressTexture.minFilter = THREE.LinearFilter;
    progressTexture.magFilter = THREE.LinearFilter;
    
    // 타임라인 메시 생성
    const progressMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(12, 1.5), // 가로 12, 세로 1.5
      new THREE.MeshStandardMaterial({
        map: progressTexture,
        emissiveMap: progressTexture, // 어둠 속에서도 보이게
        emissive: 0xffffff,
        emissiveIntensity: 0.8,
        transparent: true // 배경 투명화 필수
      })
    );
    // TV 하단(-4.1)과 사운드바 상단(-4.6) 사이 중간에 배치
    // TV 하단: -4.1, 사운드바 상단: -4.6, 중간: -4.35
    progressMesh.position.set(0, -4.35, 0.208); // TV와 사운드바 사이
    progressMesh.userData.isProgressBar = true;
    group.add(progressMesh);

    // --- LUXURY SOUNDBAR SLIM REDESIGN ---
    const soundbarGroup = new THREE.Group();
    // TV 하단(-4.1)과 사운드바 상단 간격 확보: TV 하단(-4.1) - 사운드바 상단(-4.6) = 0.5 간격
    // 사운드바 상단 = soundbarGroup.position.y + 1.2/2 = soundbarGroup.position.y + 0.6
    // -4.6 = soundbarGroup.position.y + 0.6 → soundbarGroup.position.y = -5.2
    soundbarGroup.position.set(0, -5.2, 0.208); // Y: -5.2 (TV와 겹치지 않도록 간격 확보), Z: TV 검정색 패널(화면)과 동일한 위치(0.208)

    // 1. Main Body (Slimmer Navy Cabinet) - 4배 확대 + 10% 추가 확대
    const soundbarBody = new THREE.Mesh(
      TV3D.createRoundedBox(10.6, 1.2, 0.66), // 4배 확대 + 10% 추가 (9.6 → 10.6, 1.12 → 1.2, 0.6 → 0.66)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY,
        roughness: 0.4,
        metalness: 0.4
      })
    );
    soundbarBody.castShadow = true;
    soundbarBody.receiveShadow = true;
    soundbarGroup.add(soundbarBody);

    // 2. Front Faceplate (Brushed Gold Aluminum - 진한 금장색 광택) - 4배 확대 + 10% 추가 확대
    const faceplate = new THREE.Mesh(
      new THREE.BoxGeometry(10.3, 1.1, 0.044), // 4배 확대 + 10% 추가 (9.4 → 10.3, 0.96 → 1.1, 0.04 → 0.044)
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

    // 3. Speaker Drivers (Hi-Fi Elements) - 4배 확대 + 10% 추가 확대에 맞춰 위치 조정
    const driverPositions = [
      [-4.0, 0, 0.352], // 4배 확대 + 10% 추가 (-3.6 → -4.0, 0.32 → 0.352)
      [4.0, 0, 0.352],  // 4배 확대 + 10% 추가 (3.6 → 4.0, 0.32 → 0.352)
      [-2.4, 0, 0.352], // 4배 확대 + 10% 추가 (-2.2 → -2.4, 0.32 → 0.352)
      [2.4, 0, 0.352]   // 4배 확대 + 10% 추가 (2.2 → 2.4, 0.32 → 0.352)
    ];
    
    driverPositions.forEach(pos => {
      const driver = TV3D.createHiFiDriver(pos);
      soundbarGroup.add(driver);
    });

    // 4. Center Control Cluster (The "Island") - 4배 확대 + 10% 추가 확대
    const controlGroup = new THREE.Group();
    controlGroup.position.set(0, 0, 0.352); // 4배 확대 + 10% 추가 (0.32 → 0.352)

    // Control Panel Background (Navy Pill Shape) - 4배 확대 + 10% 추가 확대
    const controlBg = new THREE.Mesh(
      new THREE.BoxGeometry(3.08, 0.704, 0.044), // 4배 확대 + 10% 추가 (2.8 → 3.08, 0.64 → 0.704, 0.04 → 0.044)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    controlBg.position.z = 0.022; // 4배 확대 + 10% 추가 (0.02 → 0.022)
    controlGroup.add(controlBg);

    // 좌우 원형 끝부분 - 4배 확대 + 10% 추가 확대
    const leftEnd = new THREE.Mesh(
      new THREE.CylinderGeometry(0.352, 0.352, 0.044, 32), // 4배 확대 + 10% 추가 (0.32 → 0.352, 0.04 → 0.044)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    leftEnd.rotation.x = Math.PI / 2;
    leftEnd.position.set(-1.54, 0, 0.022); // 4배 확대 + 10% 추가 (-1.4 → -1.54, 0.02 → 0.022)
    controlGroup.add(leftEnd);

    const rightEnd = new THREE.Mesh(
      new THREE.CylinderGeometry(0.352, 0.352, 0.044, 32), // 4배 확대 + 10% 추가 (0.32 → 0.352, 0.04 → 0.044)
      new THREE.MeshStandardMaterial({
        color: TV3D.THEME.NAVY_LIGHT,
        roughness: 0.3,
        metalness: 0.6
      })
    );
    rightEnd.rotation.x = Math.PI / 2;
    rightEnd.position.set(1.54, 0, 0.022); // 4배 확대 + 10% 추가 (1.4 → 1.54, 0.02 → 0.022)
    controlGroup.add(rightEnd);

    // 컨트롤 버튼들 (간단한 버전) - 4배 확대 + 10% 추가 확대
    // Rewind 버튼
    const rewindBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.264, 0.264, 0.088, 32), // 4배 확대 + 10% 추가 (0.24 → 0.264, 0.08 → 0.088)
      new THREE.MeshStandardMaterial({
        color: 0xffffff, // 완전 흰색
        roughness: 0.2
      })
    );
    rewindBtn.rotation.x = Math.PI / 2;
    rewindBtn.position.set(-0.968, 0, 0.12); // Z축 전진 (0.1 → 0.12) - 사운드바보다 확실히 튀어나오도록
    controlGroup.add(rewindBtn);

    // Play/Pause 버튼 (중앙, 더 큼) - 플레이 버튼을 누르면 일시정지되는 구조
    // 버튼 원: 화이트, 아이콘: 레드색 - 4배 확대 + 10% 추가 확대
    const playPauseBtnGroup = new THREE.Group();
    playPauseBtnGroup.position.set(0, 0, 0.12); // Z축 전진 (0.066 → 0.12) - 사운드바보다 확실히 튀어나오도록
    
    // 버튼 본체 (원) - 항상 화이트
    const playPauseBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.352, 0.352, 0.088, 32), // 4배 확대 + 10% 추가 (0.32 → 0.352, 0.08 → 0.088)
      new THREE.MeshStandardMaterial({
        color: 0xffffff, // 완전 흰색
        roughness: 0.2
      })
    );
    playPauseBtn.rotation.x = Math.PI / 2;
    playPauseBtnGroup.add(playPauseBtn);
    
    // 아이콘 표현 (플레이/일시정지) - 항상 레드색 - 4배 확대 + 10% 추가 확대
    // 두 아이콘을 모두 생성하고 visible로 제어 (동적 업데이트 가능)
    
    // 일시정지 아이콘: 두 개의 세로 막대 (||) - 레드색 (크기 20% 증가)
    const pauseBar1 = new THREE.Mesh(
      new THREE.BoxGeometry(0.079, 0.211, 0.026), // 크기 20% 증가 (0.066 → 0.079, 0.176 → 0.211, 0.022 → 0.026)
      new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
    );
    pauseBar1.position.set(-0.066, 0, 0.053); // 4배 확대 + 10% 추가 (-0.06 → -0.066, 0.048 → 0.053)
    pauseBar1.visible = false; // 초기 상태: 숨김 (Play 버튼 우선 노출)
    playPauseBtnGroup.add(pauseBar1);
    
    const pauseBar2 = new THREE.Mesh(
      new THREE.BoxGeometry(0.079, 0.211, 0.026), // 크기 20% 증가 (0.066 → 0.079, 0.176 → 0.211, 0.022 → 0.026)
      new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
    );
    pauseBar2.position.set(0.066, 0, 0.053); // 4배 확대 + 10% 추가 (0.06 → 0.066, 0.048 → 0.053)
    pauseBar2.visible = false; // 초기 상태: 숨김 (Play 버튼 우선 노출)
    playPauseBtnGroup.add(pauseBar2);
    
    // 재생 아이콘: 삼각형 (▶) - 레드색 (크기 20% 증가)
    const playTriangle = new THREE.Mesh(
      new THREE.ConeGeometry(0.132, 0.238, 3), // 크기 20% 증가 (0.11 → 0.132, 0.198 → 0.238)
      new THREE.MeshBasicMaterial({ color: 0xff0000 }) // 레드색
    );
    playTriangle.rotation.x = Math.PI / 2;
    playTriangle.rotation.z = -Math.PI / 2;
    playTriangle.position.set(0.044, 0, 0.053); // 4배 확대 + 10% 추가 (0.04 → 0.044, 0.048 → 0.053)
    playTriangle.visible = true; // 초기 상태: 표시 (Play 버튼 우선 노출)
    playPauseBtnGroup.add(playTriangle);
    
    controlGroup.add(playPauseBtnGroup);

    // Forward 버튼 - 4배 확대 + 10% 추가 확대
    const forwardBtn = new THREE.Mesh(
      new THREE.CylinderGeometry(0.264, 0.264, 0.088, 32), // 4배 확대 + 10% 추가 (0.24 → 0.264, 0.08 → 0.088)
      new THREE.MeshStandardMaterial({
        color: 0xffffff, // 완전 흰색
        roughness: 0.2
      })
    );
    forwardBtn.rotation.x = Math.PI / 2;
    forwardBtn.position.set(0.968, 0, 0.12); // Z축 전진 (0.1 → 0.12) - 사운드바보다 확실히 튀어나오도록
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
    // 초기 상태 명시적으로 설정 (Play 버튼 우선 노출 보장)
    group.userData.isPlaying = false; // 항상 false로 시작 (Play 아이콘 표시)
    
    // 비디오 및 타임라인 참조 저장 (외부 제어용)
    group.userData.videoElement = video;
    group.userData.videoTexture = videoTexture; // 텍스처 업데이트를 위한 참조 저장
    group.userData.progressMesh = progressMesh;
    group.userData.drawProgressBar = drawProgressBar;
    group.userData.progressTexture = progressTexture;
    
    // 버튼 참조 저장 (클릭 이벤트용)
    group.userData.buttons = {
      rewind: rewindBtn,
      playPause: playPauseBtn,
      forward: forwardBtn
    };
    
    // 아이콘 참조 저장 (동적 업데이트용)
    group.userData.playPauseIcons = {
      pauseBar1: pauseBar1,
      pauseBar2: pauseBar2,
      playTriangle: playTriangle
    };
    
    // 스크린 참조 저장
    screen.userData.type = 'tvScreen';
    screen.userData.tvGroup = tvGroup;
    screen.name = 'TV_Screen';
    
    // 버튼 식별자 추가
    rewindBtn.userData.type = 'soundbarButton';
    rewindBtn.userData.buttonType = 'rewind';
    rewindBtn.name = 'Soundbar_Rewind';
    
    playPauseBtn.userData.type = 'soundbarButton';
    playPauseBtn.userData.buttonType = 'playPause';
    playPauseBtn.name = 'Soundbar_PlayPause';
    
    forwardBtn.userData.type = 'soundbarButton';
    forwardBtn.userData.buttonType = 'forward';
    forwardBtn.name = 'Soundbar_Forward';

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
