/**
 * Chandelier3D - 고급 3D 샹들리에 모델 (React 컴포넌트 기반)
 * 8개의 곡선형 팔과 앰버 크리스탈, 램프 쉐이드를 포함한 완전한 디자인
 * 
 * @class Chandelier3D
 * @description ProductFactory에서 사용하는 3D 샹들리에 가구 클래스
 */
class Chandelier3D {
  /**
   * Static Material 공유 (WebGL 텍스처 유닛 최적화)
   */
  static sharedMetalMat = null;
  static sharedCrystalMat = null;
  static sharedFabricMat = null;

  /**
   * 금속 Material 가져오기
   */
  static getMetalMaterial() {
    if (!Chandelier3D.sharedMetalMat) {
      Chandelier3D.sharedMetalMat = new THREE.MeshStandardMaterial({
        color: 0xe8dcc0, // Pale gold/cream
        roughness: 0.2,
        metalness: 0.8
      });
    }
    return Chandelier3D.sharedMetalMat;
  }

  /**
   * 크리스탈 Material 가져오기
   */
  static getCrystalMaterial() {
    if (!Chandelier3D.sharedCrystalMat) {
      Chandelier3D.sharedCrystalMat = new THREE.MeshPhysicalMaterial({
        color: 0xdda520, // Amber/Goldenrod
        roughness: 0,
        metalness: 0,
        transmission: 0.9, // Glass-like transparency
        thickness: 2,
        ior: 1.5,
        clearcoat: 1
      });
    }
    return Chandelier3D.sharedCrystalMat;
  }

  /**
   * 천 직물 Material 가져오기
   */
  static getFabricMaterial() {
    if (!Chandelier3D.sharedFabricMat) {
      Chandelier3D.sharedFabricMat = new THREE.MeshStandardMaterial({
        color: 0xfdf5e6, // Old Lace
        roughness: 0.8,
        side: THREE.DoubleSide
      });
    }
    return Chandelier3D.sharedFabricMat;
  }

  /**
   * 샹들리에 팔 생성
   * @param {number} rotation - Y축 회전 각도
   * @param {THREE.Group} parentGroup - 부모 그룹
   */
  static createArm(rotation, parentGroup) {
    const armGroup = new THREE.Group();
    armGroup.rotation.y = rotation;

    // 곡선 경로 정의 (S/U 형태)
    // 샹들리에는 아래로 내려가는 구조이므로, 허브를 기준으로 팔이 아래로 내려가도록 조정
    const points = [
      new THREE.Vector3(0, 0, 0),         // Start at center hub
      new THREE.Vector3(0.5, -0.2, 0),    // Slightly out and down
      new THREE.Vector3(1.5, -2.0, 0),   // Deep swoop down (2.5 → 2.0으로 조정)
      new THREE.Vector3(3.5, -0.8, 0),   // Curve back up and out (-1.0 → -0.8)
      new THREE.Vector3(3.8, 0.5, 0),     // End point where shade sits
    ];
    const curve = new THREE.CatmullRomCurve3(points);

    // 금속 팔 튜브 (성능 최적화: 세그먼트 64 → 32로 감소)
    const armTube = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 32, 0.08, 12, false),
      Chandelier3D.getMetalMaterial()
    );
    armTube.castShadow = true;
    armGroup.add(armTube);

    // 중앙 연결 장식 링 (성능 최적화: 세그먼트 32 → 16으로 감소)
    const connectionRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.15, 0.04, 16, 16),
      Chandelier3D.getMetalMaterial()
    );
    connectionRing.position.set(0.4, 0, 0);
    connectionRing.rotation.z = Math.PI / 2;
    armGroup.add(connectionRing);

    // 팔 끝 조립체 (크리스탈 + 쉐이드)
    const endAssembly = new THREE.Group();
    endAssembly.position.set(3.8, 0.5, 0);

    // 앰버 크리스탈 볼 장식 (쉐이드 아래)
    const crystalGroup = new THREE.Group();
    crystalGroup.position.set(0, -0.6, 0);

    // 크리스탈을 지지하는 금속 줄기
    const crystalStem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.6, 8),
      Chandelier3D.getMetalMaterial()
    );
    crystalStem.position.set(0, 0.3, 0);
    crystalGroup.add(crystalStem);

    // 앰버 구체 (성능 최적화: 세그먼트 32 → 16으로 감소)
    const crystalBall = new THREE.Mesh(
      new THREE.SphereGeometry(0.35, 16, 16),
      Chandelier3D.getCrystalMaterial()
    );
    crystalBall.castShadow = true;
    crystalGroup.add(crystalBall);

    // 구체 하단의 작은 피니얼 (성능 최적화: 세그먼트 16 → 12로 감소)
    const finial = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 12, 12),
      Chandelier3D.getMetalMaterial()
    );
    finial.position.set(0, -0.4, 0);
    crystalGroup.add(finial);

    endAssembly.add(crystalGroup);

    // 촛불 홀더/컵 (성능 최적화: 세그먼트 32 → 16으로 감소)
    const candleHolder = new THREE.Mesh(
      new THREE.CylinderGeometry(0.25, 0.1, 0.3, 16),
      Chandelier3D.getMetalMaterial()
    );
    endAssembly.add(candleHolder);

    // 쉐이드 아래 꽃잎 장식
    const petalDetail = new THREE.Mesh(
      new THREE.TorusGeometry(0.2, 0.05, 16, 6),
      Chandelier3D.getMetalMaterial()
    );
    petalDetail.position.set(0, -0.1, 0);
    endAssembly.add(petalDetail);

    // 램프 쉐이드
    const shadeGroup = new THREE.Group();
    shadeGroup.position.set(0, 1.2, 0);

    // 쉐이드 원뿔 (성능 최적화: 세그먼트 64 → 32로 감소)
    const shade = new THREE.Mesh(
      new THREE.CylinderGeometry(0.6, 1.0, 2.0, 32, 1, true),
      Chandelier3D.getFabricMaterial()
    );
    shade.castShadow = true;
    shadeGroup.add(shade);

    // 내부 조명 (PointLight) - 장식용 미광 (누출 방지: 짧은 거리)
    const pointLight = new THREE.PointLight(0xffffff, 2.0, 3, 2);
    pointLight.position.set(0, 0, 0);
    pointLight.castShadow = false; // 성능 최적화: 그림자 비활성화
    shadeGroup.add(pointLight);

    // 시각적 전구 (가짜) (성능 최적화: 세그먼트 16 → 12로 감소)
    const bulb = new THREE.Mesh(
      new THREE.SphereGeometry(0.15, 12, 12),
      new THREE.MeshBasicMaterial({ 
        color: 0xffffff, 
        toneMapped: false 
      })
    );
    bulb.position.set(0, -0.2, 0);
    shadeGroup.add(bulb);

    endAssembly.add(shadeGroup);
    armGroup.add(endAssembly);

    parentGroup.add(armGroup);
  }

  /**
   * 중앙 허브 생성
   * @param {THREE.Group} parentGroup - 부모 그룹
   */
  static createCenterHub(parentGroup) {
    // 중앙 허브 (원통형) (성능 최적화: 세그먼트 32 → 16으로 감소)
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.3, 0.3, 0.4, 16),
      Chandelier3D.getMetalMaterial()
    );
    hub.position.y = 0;
    hub.castShadow = true;
    parentGroup.add(hub);

    // 허브 상단 장식 (성능 최적화: 세그먼트 32 → 16으로 감소)
    const topDeco = new THREE.Mesh(
      new THREE.TorusGeometry(0.35, 0.05, 16, 16),
      Chandelier3D.getMetalMaterial()
    );
    topDeco.position.y = 0.2;
    parentGroup.add(topDeco);

    // 허브 하단 장식 (성능 최적화: 세그먼트 32 → 16으로 감소)
    const bottomDeco = new THREE.Mesh(
      new THREE.TorusGeometry(0.35, 0.05, 16, 16),
      Chandelier3D.getMetalMaterial()
    );
    bottomDeco.position.y = -0.2;
    parentGroup.add(bottomDeco);

    // 천장 고리 (90도 세워서 수직 배치)
    const ceilingRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.25, 0.04, 16, 16),
      Chandelier3D.getMetalMaterial()
    );
    ceilingRing.position.y = 0.3; // 허브 상단 위에 배치
    ceilingRing.rotation.x = Math.PI / 2; // 90도 세워서 수직 배치
    ceilingRing.castShadow = true;
    parentGroup.add(ceilingRing);

    // 천장 고정 봉 (중앙 허브 윗면에서 천장 방향으로 수직 배치)
    const ceilingRod = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.08, 4.5, 16), // 반지름 0.08, 높이 4.5 (추가 확대)
      Chandelier3D.getMetalMaterial()
    );
    // 허브 윗면(y=0.2)에서 시작하여 봉의 중심이 봉 높이의 절반만큼 위에 위치
    ceilingRod.position.set(0, 0.2 + 2.25, 0); // y = 0.2 (허브 윗면) + 2.25 (봉 높이 4.5의 절반)
    ceilingRod.castShadow = true;
    parentGroup.add(ceilingRod);
  }

  /**
   * 샹들리에 모델 생성
   * @param {Object} product - 상품 데이터 (선택사항)
   * @param {THREE.Vector3} position - 위치
   * @param {boolean} isPlaying - 재생 상태 (선택사항)
   * @returns {THREE.Group} 샹들리에 그룹
   */
  static createModel(product = null, position = new THREE.Vector3(0, 0, 0), isPlaying = false) {
    const group = new THREE.Group();
    
    // 샹들리에는 아래로 내려가는 구조이므로, 허브를 y=2에 배치하여 팔이 위아래로 균형있게 보이도록 함
    // (팔이 y=-2.0까지 내려가므로, 허브가 y=2에 있으면 전체적으로 y=0~4 범위에 분포)
    const hubY = 2.0;
    group.position.set(position.x, position.y + hubY, position.z);

    // 중앙 허브 생성
    Chandelier3D.createCenterHub(group);

    // 8개의 팔 생성
    const numArms = 8;
    for (let i = 0; i < numArms; i++) {
      const angle = (i / numArms) * Math.PI * 2;
      Chandelier3D.createArm(angle, group);
    }

    // 메인 조명 (SpotLight) - 실제 조명용 메인광 (바닥까지 도달)
    const mainLight = new THREE.SpotLight(
      0xffffee,  // 따뜻한 럭셔리 톤
      15.0,      // 강도: 8개 전구를 합친 것만큼 강력
      28.0,      // 거리: 천장 15m에서 바닥 구석까지 닿도록
      Math.PI / 1.5,  // 각도: 약 120도 (넓게 퍼지게)
      0.5,       // penumbra: 가장자리 부드럽게
      2          // decay: 물리 법칙 준수 (역제곱 감쇠)
    );
    mainLight.position.set(0, -3.0, 0);  // 샹들리에 몸통보다 더 아래로 내려서 팔에 가려지지 않게
    mainLight.target.position.set(0, -20, 0);  // 수직 하강
    mainLight.castShadow = true;  // 메인 조명만 그림자 생성
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    mainLight.shadow.camera.near = 0.1;
    mainLight.shadow.camera.far = 30;
    group.add(mainLight);
    group.add(mainLight.target);

    // 천장 전용 무드등 (Ceiling Glow) - 천장 밝기 확보
    const ceilingGlow = new THREE.PointLight(
      0xffffee,  // 따뜻한 흰색
      8.0,       // 강도: 천장 전체와 금테두리를 밝히기 위해 대폭 상향 (3.0 -> 8.0)
      30,        // 거리: 천장 끝의 금테두리까지 빛이 닿도록 확장 (15 -> 30)
      2          // decay: 물리 법칙 준수
    );
    ceilingGlow.position.set(0, 0.5, 0);  // 샹들리에 중심에서 약간 위 (광원이 천장면에서 조금 더 떨어져서 빛이 넓게 퍼짐)
    ceilingGlow.castShadow = false;  // 절대 켜지 마라. 렉 유발함.
    group.add(ceilingGlow);

    // 애니메이션 속도 저장 (나중에 제어 가능)
    group.userData.rotationSpeed = 0.05;
    group.userData.isRotating = true;

    // 전체 크기를 절반으로 줄임 (1배 줄이기 = 50% 크기)
    group.scale.set(0.5, 0.5, 0.5);

    // 바운딩 박스 계산 (스케일 적용 후 계산하여 정확한 크기 반영)
    const box = new THREE.Box3().setFromObject(group);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    
    // userData에 저장하여 ProductFactory에서 재사용
    group.userData.boundingBox = { size, center };
    
    console.log(`[Chandelier3D] 생성 완료 - 크기: (${size.x.toFixed(2)}, ${size.y.toFixed(2)}, ${size.z.toFixed(2)}), 중심: (${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)})`);

    return group;
  }

  /**
   * 애니메이션 업데이트 (외부에서 호출)
   * @param {THREE.Group} group - 샹들리에 그룹
   * @param {number} delta - 시간 델타
   */
  static animate(group, delta) {
    if (group.userData.isRotating) {
      group.rotation.y += delta * group.userData.rotationSpeed;
    }
  }
}

// 전역 객체로 노출
window.Chandelier3D = Chandelier3D;
console.log("✅ [Chandelier3D] 전역 객체로 노출 완료:", typeof window.Chandelier3D);

