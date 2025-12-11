/**
 * ShowroomBuilder - 쇼룸 인테리어 구성 연동 모듈
 * Showroom.js의 인테리어 요소 생성 기능을 담당
 */
class ShowroomBuilder {
  constructor(scene) {
    this.scene = scene;
    this.roomSize = { width: 30, height: 15, depth: 30 };
    this.room = null;
  }

  /**
   * 방 전체 구성 (바닥, 벽, 천장, 몰딩)
   */
  buildRoom() {
    // 충돌 범위 업데이트
    this.wallLimitX = this.roomSize.width / 2 - 1; // ±14 (벽 두께 고려)
    this.wallLimitZ = this.roomSize.depth / 2 - 1; // ±14

    // 바닥 텍스처 생성
    const floorTexture = this.createMarbleTexture();
    console.log("✅ [ShowroomBuilder] 바닥 텍스처:", floorTexture);

    // 텍스처 반복 설정 (타일 크기 적당히)
    floorTexture.wrapS = THREE.RepeatWrapping;
    floorTexture.wrapT = THREE.RepeatWrapping;
    floorTexture.repeat.set(5, 5); // 타일 크기 (원본 설정)

    // 단순 바닥 시공 (PlaneGeometry - 검은색 버그 원천 봉쇄)
    const floorSize = 30; // 벽과 동일한 크기
    const floorGeo = new THREE.PlaneGeometry(floorSize, floorSize);
    
    // 바닥 재질 (원본 설정 복구)
    const floorMat = new THREE.MeshPhysicalMaterial({
      map: floorTexture,
      color: 0x111111, // 검은색 바닥 (원본)
      roughness: 0.05, // 매우 매끄러운 표면 (대리석 반사)
      metalness: 0.2,
      side: THREE.FrontSide,
      flatShading: false
    });
    
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2; // 바닥에 눕힘
    floor.position.y = 0; // 정확히 바닥
    floor.receiveShadow = true;
    this.scene.add(floor);

    // 벽-바닥 모서리 코브 추가 (수평 코브)
    this.createFloorCornerCoves();

    // 천장 베이스 패널 (투명)
    const ceilingBaseMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a, // 다크 그레이 - 격자 천장 베이스
      roughness: 0.5,
      side: THREE.BackSide,
      flatShading: false,
      transparent: true,
      opacity: 0.3 // 투명하게 하여 격자 천장이 보이도록
    });
    const ceilingBaseGeo = new THREE.PlaneGeometry(
      this.roomSize.width,
      this.roomSize.depth
    );
    const ceilingBase = new THREE.Mesh(ceilingBaseGeo, ceilingBaseMat);
    ceilingBase.rotation.x = Math.PI / 2;
    ceilingBase.position.y = this.roomSize.height;
    this.scene.add(ceilingBase);

    // 단순 박스 벽 시공 (검은색 버그 원천 봉쇄)
    this.createSimpleWalls();

    // 벽면 매립형 수직 간접 조명 추가
    this.createWallLightStrips();

    // 벽 모서리 곡면 처리 (디버깅 중)
    this.createWallCornerCoves();

    // 모던 격자 천장 시공 (Commander 지시)
    this.createCofferedCeiling();

    // 창문 삭제 (Commander 지시)
    // this.createWindows();

    // 문 삭제 (Commander 지시)
    // this.createDoor();

    // 벽 선반 삭제 (Commander 지시)
    // this.createWallShelves();

    return {
      room: floor, // 바닥을 room으로 반환 (기존 호환성 유지)
      wallLimitX: this.wallLimitX,
      wallLimitZ: this.wallLimitZ
    };
  }

  /**
   * 대리석 바닥 텍스처 생성
   */
  createMarbleTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 2048;
    const ctx = canvas.getContext("2d");

    // 검은색 배경 (대리석의 기본)
    ctx.fillStyle = "#111111";
    ctx.fillRect(0, 0, 2048, 2048);

    // 타일 격자 그리기(검은색/회색 교차)
    const tileSize = 128;
    ctx.strokeStyle = "#888888";
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

    // 랜덤 곡선 무늬 (검은색/회색 교차)
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 2;
    for (let i = 0; i < 80; i++) {
      ctx.beginPath();
      ctx.moveTo(Math.random() * 2048, Math.random() * 2048);
      for (let j = 0; j < 8; j++) {
        ctx.lineTo(Math.random() * 2048, Math.random() * 2048);
      }
      ctx.stroke();
    }

    // 추가 회색 곡선
    ctx.strokeStyle = "rgba(200, 200, 200, 0.15)";
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
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = true;
    texture.anisotropy = 16;
    texture.repeat.set(5, 5);
    texture.needsUpdate = true;

    return texture;
  }

  /**
   * 둥근 사각형 Shape 생성 헬퍼 함수
   */
  createRoundedRectShape(width, height, radius) {
    const shape = new THREE.Shape();
    const w = width / 2;
    const h = height / 2;
    const r = radius;

    shape.moveTo(-w + r, -h);
    shape.lineTo(w - r, -h);
    shape.quadraticCurveTo(w, -h, w, -h + r);
    shape.lineTo(w, h - r);
    shape.quadraticCurveTo(w, h, w - r, h);
    shape.lineTo(-w + r, h);
    shape.quadraticCurveTo(-w, h, -w, h - r);
    shape.lineTo(-w, -h + r);
    shape.quadraticCurveTo(-w, -h, -w + r, -h);

    return shape;
  }

  /**
   * 벽-바닥 모서리 라운딩 (수평 코브)
   * 4개의 벽-바닥 접합부에 1/4 원통 형태의 코브 추가
   */
  createFloorCornerCoves() {
    const coveRadius = 0.3; // 코브 반지름 (30cm)
    const wallLength = 30; // 벽 길이
    const wallThickness = 1; // 벽 두께
    const wallCenterOffset = wallThickness / 2; // 벽 중심에서 안쪽 면까지: 0.5m
    const wallInnerEdge = 15.5 - wallCenterOffset; // 벽 안쪽 면: ±15.0
    
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xFFFFFF, // 벽과 동일한 화이트
      roughness: 0.5,
      side: THREE.DoubleSide
    });

    // 1/4 원통 Geometry 생성 (90도 호)
    const coveGeo = new THREE.CylinderGeometry(
      coveRadius,      // 반지름
      coveRadius,      // 반지름 (원통)
      wallLength,      // 길이 (벽 길이와 동일)
      16,              // 방사형 세그먼트
      1,               // 높이 세그먼트
      false,           // openEnded
      Math.PI / 2,     // thetaStart: 90도부터 시작
      Math.PI / 2      // thetaLength: 90도 호 (1/4 원)
    );

    // 2개의 벽-바닥 모서리만 생성 (앞벽, 뒷벽 제외 - 사용자 요청)
    // CylinderGeometry는 기본적으로 Y축을 따라 생성되므로, 벽의 길이 방향에 맞게 회전 필요
    const floorCoves = [
      {
        // 왼벽-바닥 (Z축 방향으로 눕힘, 벽 안쪽 향함)
        // 원통을 Z축 방향으로 눕히고, 1/4 원통이 벽 안쪽(방 안쪽)을 향하도록
        position: { x: -wallInnerEdge, y: coveRadius, z: 0 }, // x = -15.0
        rotation: { x: 0, y: Math.PI / 2, z: Math.PI / 2 } // Y축 90도 + Z축 90도 (Z축 방향으로 눕힘)
      },
      {
        // 오른벽-바닥 (Z축 방향으로 눕힘, 벽 안쪽 향함)
        position: { x: wallInnerEdge, y: coveRadius, z: 0 }, // x = 15.0
        rotation: { x: 0, y: -Math.PI / 2, z: Math.PI / 2 } // Y축 -90도 + Z축 90도 (Z축 방향으로 눕힘, 반대 방향)
      }
    ];

    floorCoves.forEach((coveConfig) => {
      const cove = new THREE.Mesh(coveGeo, wallMat);
      cove.position.set(
        coveConfig.position.x,
        coveConfig.position.y, // 바닥 위로 coveRadius만큼
        coveConfig.position.z
      );
      cove.rotation.set(
        coveConfig.rotation.x,
        coveConfig.rotation.y,
        coveConfig.rotation.z
      );
      cove.receiveShadow = true;
      this.scene.add(cove);
    });

    console.log("✅ [ShowroomBuilder] 벽-바닥 모서리 코브 추가 완료");
  }


  /**
   * 단순 박스 벽 시공 (검은색 버그 원천 봉쇄)
   * ExtrudeGeometry 대신 BoxGeometry 4개로 확실하게
   */
  createSimpleWalls() {
    // 투톤 벽 재질 정의
    // 하단 벽 재질 (우드 색상 - 진한 갈색)
    const darkBaseMat = new THREE.MeshStandardMaterial({
      color: 0x5C4A2F,       // 우드 색상 (진한 갈색)
      roughness: 0.8,        // 나무 질감을 위한 거칠기 증가
      metalness: 0.0,        // 비금속 (나무 느낌)
      side: THREE.DoubleSide
    });

    // 상단 벽 재질 (화이트 - 고급 석고 질감)
    const lightUpperMat = new THREE.MeshStandardMaterial({
      color: 0xFFFFFF,       // 화이트
      roughness: 0.8,
      metalness: 0.1,
      side: THREE.DoubleSide
    });

    // 벽 높이 설정
    const pedestalHeight = 1.4; // 상품 거치대 높이
    const bottomHeight = 1.0;   // 하단 벽 높이 (1.2m → 1.0m로 조금 더 감소)
    const topHeight = 14.0;     // 상단 벽 높이 (13.8m → 14.0m로 조정, 총 높이 15m 유지)
    const bottomY = bottomHeight / 2;  // 하단 벽 Y 위치: 0.5
    const topY = bottomHeight + (topHeight / 2);  // 상단 벽 Y 위치: 8.0

    // 뒷벽 (z = -15.5) - 투톤 벽
    // 하단 벽
    const backWallBottom = new THREE.Mesh(
      new THREE.BoxGeometry(30, bottomHeight, 1),
      darkBaseMat
    );
    backWallBottom.position.set(0, bottomY, -15.5);
    backWallBottom.receiveShadow = true;
    this.scene.add(backWallBottom);

    // 상단 벽
    const backWallTop = new THREE.Mesh(
      new THREE.BoxGeometry(30, topHeight, 1),
      lightUpperMat
    );
    backWallTop.position.set(0, topY, -15.5);
    backWallTop.receiveShadow = true;
    this.scene.add(backWallTop);

    // 왼벽 (x = -15.5) - 투톤 벽
    // 하단 벽
    const leftWallBottom = new THREE.Mesh(
      new THREE.BoxGeometry(1, bottomHeight, 30),
      darkBaseMat
    );
    leftWallBottom.position.set(-15.5, bottomY, 0);
    leftWallBottom.receiveShadow = true;
    this.scene.add(leftWallBottom);

    // 상단 벽
    const leftWallTop = new THREE.Mesh(
      new THREE.BoxGeometry(1, topHeight, 30),
      lightUpperMat
    );
    leftWallTop.position.set(-15.5, topY, 0);
    leftWallTop.receiveShadow = true;
    this.scene.add(leftWallTop);

    // 오른벽 (x = 15.5) - 투톤 벽
    // 하단 벽
    const rightWallBottom = new THREE.Mesh(
      new THREE.BoxGeometry(1, bottomHeight, 30),
      darkBaseMat
    );
    rightWallBottom.position.set(15.5, bottomY, 0);
    rightWallBottom.receiveShadow = true;
    this.scene.add(rightWallBottom);

    // 상단 벽
    const rightWallTop = new THREE.Mesh(
      new THREE.BoxGeometry(1, topHeight, 30),
      lightUpperMat
    );
    rightWallTop.position.set(15.5, topY, 0);
    rightWallTop.receiveShadow = true;
    this.scene.add(rightWallTop);

    // 앞벽 (z = 15.5) - 투톤 벽
    // 하단 벽
    const frontWallBottom = new THREE.Mesh(
      new THREE.BoxGeometry(30, bottomHeight, 1),
      darkBaseMat
    );
    frontWallBottom.position.set(0, bottomY, 15.5);
    frontWallBottom.receiveShadow = true;
    this.scene.add(frontWallBottom);

    // 상단 벽
    const frontWallTop = new THREE.Mesh(
      new THREE.BoxGeometry(30, topHeight, 1),
      lightUpperMat
    );
    frontWallTop.position.set(0, topY, 15.5);
    frontWallTop.receiveShadow = true;
    this.scene.add(frontWallTop);

    console.log("✅ [ShowroomBuilder] 투톤 벽 시공 완료 (하단 우드 8m + 상단 화이트 7m)");
  }

  /**
   * 벽면 수직 간접 조명 (PointLight 광원)
   * 왼벽과 오른벽에 각각 2개씩, 총 4개의 PointLight 배치
   */
  createWallLightStrips() {
    const wallInnerEdge = 15.0; // 벽 안쪽 면
    const lightY = 7.5; // 조명 Y 위치 (벽 높이 중앙)
    
    // 왼벽 PointLight 2개
    const leftWallLights = [
      { position: { x: -wallInnerEdge, y: lightY, z: 5 } },   // 왼벽 조명 1
      { position: { x: -wallInnerEdge, y: lightY, z: -5 } }   // 왼벽 조명 2
    ];

    // 오른벽 PointLight 2개
    const rightWallLights = [
      { position: { x: wallInnerEdge, y: lightY, z: 5 } },     // 오른벽 조명 1
      { position: { x: wallInnerEdge, y: lightY, z: -5 } }    // 오른벽 조명 2
    ];

    // 모든 PointLight 생성 및 배치
    [...leftWallLights, ...rightWallLights].forEach((lightConfig) => {
      const pointLight = new THREE.PointLight(0xFFFFFF, 0.8, 15); // 흰색, 강도 0.8, 거리 15m
      pointLight.position.set(
        lightConfig.position.x,
        lightConfig.position.y,
        lightConfig.position.z
      );
      pointLight.castShadow = true;
      this.scene.add(pointLight);
    });

    console.log("✅ [ShowroomBuilder] 벽면 수직 간접 조명 추가 완료 (PointLight 4개)");
  }

  /**
   * 벽 모서리 곡면 처리 (4개 수직 모서리만)
   * 벽 위치는 고정하고, 모서리 부분만 곡면으로 처리
   */
  createWallCornerCoves() {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:308',message:'createWallCornerCoves entry',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    const coveRadius = 4.0; // 코브 반지름 (천장과 동일한 4.0m)
    const wallHeight = 15; // 벽 높이
    const wallThickness = 1; // 벽 두께
    const wallCenterOffset = wallThickness / 2; // 벽 중심에서 안쪽 면까지: 0.5m
    const wallInnerEdge = 15.5 - wallCenterOffset; // 벽 안쪽 면: 15.0m
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:315',message:'벽 모서리 코브 계산값',data:{coveRadius,wallHeight,wallThickness,wallCenterOffset,wallInnerEdge},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xFFFFFF, // 벽과 동일한 화이트
      roughness: 0.5,
      side: THREE.DoubleSide
    });

    // 수직 원통형 코브 Geometry (벽 높이만큼, 1/4 원통)
    // CylinderGeometry의 기본 방향:
    // - thetaStart=Math.PI/2 (90도)는 +Y 방향에서 시작
    // - thetaLength=Math.PI/2 (90도)는 90도부터 180도까지의 호를 그립니다
    // - 즉, +Y 방향에서 시작하여 -X 방향으로 가는 호입니다
    // 
    // 천장의 곡면과 일치시키려면:
    // - 천장의 곡면은 각 모서리에서 양쪽 벽을 따라 곡선으로 연결됩니다
    // - 벽 모서리 코브는 각 모서리에서 천장 곡면과 정확히 일치하도록 회전해야 합니다
    const coveGeo = new THREE.CylinderGeometry(
      coveRadius,      // 반지름
      coveRadius,      // 반지름 (원통)
      wallHeight,      // 높이 (벽 높이와 동일)
      16,              // 방사형 세그먼트
      1,               // 높이 세그먼트
      false,           // openEnded
      Math.PI / 2,     // thetaStart: 90도부터 시작 (+Y 방향)
      Math.PI / 2      // thetaLength: 90도 호 (1/4 원, +Y에서 -X로)
    );
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:343',message:'CylinderGeometry 기본 방향 분석',data:{thetaStart:'Math.PI/2 (90도, +Y 방향)',thetaLength:'Math.PI/2 (90도, +Y에서 -X로)',note:'기본 방향: +Y에서 시작하여 -X로 가는 호'},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
    // #endregion
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:331',message:'CylinderGeometry 생성 완료',data:{coveRadius,wallHeight,thetaStart:'Math.PI/2',thetaLength:'Math.PI/2'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    // #endregion

    // 4개의 벽 모서리 위치 (벽 안쪽 면 기준)
    // 천장의 곡면처럼 각 모서리에서 방 안쪽을 향하도록 배치
    // 
    // 천장의 곡면 처리 방식 분석 (createRoundedRectShape):
    // - 오른쪽 위 모서리 (w, h): quadraticCurveTo(w, h, w - r, h) - 모서리에서 왼쪽(-X)으로 곡선
    // - 오른쪽 아래 모서리 (w, -h): quadraticCurveTo(w, -h, w, -h + r) - 모서리에서 위(+Y)로 곡선
    // - 왼쪽 위 모서리 (-w, h): quadraticCurveTo(-w, h, -w, h - r) - 모서리에서 아래(-Y)로 곡선
    // - 왼쪽 아래 모서리 (-w, -h): quadraticCurveTo(-w, -h, -w + r, -h) - 모서리에서 오른쪽(+X)으로 곡선
    // 
    // 3D 공간에서 각 모서리의 위치와 천장 곡면 방향:
    // - 앞-왼 모서리 (-15, 15): 천장에서 왼쪽(-X)과 앞(+Z) 방향으로 곡선 → 대각선 방향: -X, +Z
    // - 앞-오른 모서리 (15, 15): 천장에서 오른쪽(+X)과 앞(+Z) 방향으로 곡선 → 대각선 방향: +X, +Z
    // - 뒤-왼 모서리 (-15, -15): 천장에서 왼쪽(-X)과 뒤(-Z) 방향으로 곡선 → 대각선 방향: -X, -Z
    // - 뒤-오른 모서리 (15, -15): 천장에서 오른쪽(+X)과 뒤(-Z) 방향으로 곡선 → 대각선 방향: +X, -Z
    // 
    // CylinderGeometry의 기본 방향 (thetaStart=Math.PI/2, thetaLength=Math.PI/2):
    // - +Y 방향에서 시작하여 -X 방향으로 가는 호입니다
    // - 즉, 기본적으로 위(+Y)에서 시작하여 왼쪽(-X)으로 가는 호입니다
    // 
    // 각 모서리에서 천장 곡면과 일치시키려면:
    // - CylinderGeometry의 기본 방향(+Y에서 -X)을 각 모서리의 천장 곡면 방향으로 회전해야 합니다
    // - 앞-왼 모서리: 기본 방향(+Y→-X)을 (-X, +Z) 방향으로 회전 → Y축 회전: 45도 추가 → 90도 + 45도 = 135도
    // - 앞-오른 모서리: 기본 방향(+Y→-X)을 (+X, +Z) 방향으로 회전 → Y축 회전: 135도 추가 → 90도 + 135도 = 225도
    // - 뒤-왼 모서리: 기본 방향(+Y→-X)을 (-X, -Z) 방향으로 회전 → Y축 회전: -45도 추가 → 90도 - 45도 = 45도
    // - 뒤-오른 모서리: 기본 방향(+Y→-X)을 (+X, -Z) 방향으로 회전 → Y축 회전: -135도 추가 → 90도 - 135도 = -45도 (315도)
    //
    // 하지만 실제로는 CylinderGeometry가 수직 원통이므로, 각 모서리에서 천장 곡면의 시작 방향을 정확히 맞춰야 합니다.
    // 천장 곡면은 각 모서리에서 45도 대각선 방향으로 시작하므로, 벽 모서리 코브도 동일한 각도로 시작해야 합니다.
    const wallCorners = [
      {
        // 앞-왼 모서리 (x = -15.0, z = 15.0)
        // 천장 곡면: 왼쪽(-X)과 앞(+Z) 방향으로 곡선
        // 기본 방향(+Y→-X)을 45도 회전하여 (-X, +Z) 방향으로 맞춤
        position: { x: -wallInnerEdge, y: wallHeight / 2, z: wallInnerEdge },
        rotation: { x: 0, y: Math.PI / 2 + Math.PI / 4, z: 0 } // Y축 135도 (90도 + 45도)
      },
      {
        // 앞-오른 모서리 (x = 15.0, z = 15.0)
        // 천장 곡면: 오른쪽(+X)과 앞(+Z) 방향으로 곡선
        // 기본 방향(+Y→-X)을 135도 회전하여 (+X, +Z) 방향으로 맞춤
        position: { x: wallInnerEdge, y: wallHeight / 2, z: wallInnerEdge },
        rotation: { x: 0, y: Math.PI / 2 + (3 * Math.PI) / 4, z: 0 } // Y축 225도 (90도 + 135도)
      },
      {
        // 뒤-왼 모서리 (x = -15.0, z = -15.0)
        // 천장 곡면: 왼쪽(-X)과 뒤(-Z) 방향으로 곡선
        // 기본 방향(+Y→-X)을 -45도 회전하여 (-X, -Z) 방향으로 맞춤
        position: { x: -wallInnerEdge, y: wallHeight / 2, z: -wallInnerEdge },
        rotation: { x: 0, y: Math.PI / 2 - Math.PI / 4, z: 0 } // Y축 45도 (90도 - 45도)
      },
      {
        // 뒤-오른 모서리 (x = 15.0, z = -15.0)
        // 천장 곡면: 오른쪽(+X)과 뒤(-Z) 방향으로 곡선
        // 기본 방향(+Y→-X)을 -135도 회전하여 (+X, -Z) 방향으로 맞춤
        position: { x: wallInnerEdge, y: wallHeight / 2, z: -wallInnerEdge },
        rotation: { x: 0, y: Math.PI / 2 - (3 * Math.PI) / 4, z: 0 } // Y축 -45도 (90도 - 135도 = -45도)
      }
    ];
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:409',message:'벽 모서리 회전 방향 최종 계산',data:{wallCorners:wallCorners.map((c,i)=>({corner:i,position:c.position,rotationY:c.rotation.y,rotationDeg:c.rotation.y*180/Math.PI,baseRotation:'Math.PI/2 (90도)',additionalRotation:c.rotation.y - Math.PI/2})),note:'CylinderGeometry 기본 방향(+Y→-X)에서 천장 곡면 방향으로 회전'},timestamp:Date.now(),sessionId:'debug-session',runId:'run4',hypothesisId:'I'})}).catch(()=>{});
    // #endregion
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:397',message:'벽 모서리 회전 방향 재계산',data:{wallCorners:wallCorners.map((c,i)=>({corner:i,position:c.position,rotationY:c.rotation.y,rotationDeg:c.rotation.y*180/Math.PI})),note:'천장 곡면과 정확히 일치하도록 회전값 수정'},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'H'})}).catch(()=>{});
    // #endregion
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:375',message:'벽 모서리 회전 방향 계산',data:{wallCorners:wallCorners.map(c=>({position:c.position,rotationY:c.rotation.y}))},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
    // #endregion

    wallCorners.forEach((cornerConfig, index) => {
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:365',message:'벽 모서리 코브 생성 시작',data:{cornerIndex:index,position:cornerConfig.position,rotation:cornerConfig.rotation},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      
      const cove = new THREE.Mesh(coveGeo, wallMat);
      cove.position.set(
        cornerConfig.position.x,
        cornerConfig.position.y, // 벽 높이의 절반 (7.5m)
        cornerConfig.position.z
      );
      cove.rotation.set(
        cornerConfig.rotation.x,
        cornerConfig.rotation.y,
        cornerConfig.rotation.z
      );
      
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:377',message:'벽 모서리 코브 배치 완료',data:{cornerIndex:index,finalPosition:{x:cove.position.x,y:cove.position.y,z:cove.position.z},finalRotation:{x:cove.rotation.x,y:cove.rotation.y,z:cove.rotation.z}},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      
      cove.receiveShadow = true;
      this.scene.add(cove);
    });

    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/6cdbf604-cbc7-4e56-ae78-2c8a9e87b4b7',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ShowroomBuilder.js:382',message:'createWallCornerCoves exit',data:{totalCorners:wallCorners.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    console.log("✅ [ShowroomBuilder] 벽 모서리 곡면 처리 완료 (4개 수직 모서리)");
  }

  /**
   * 벽 하단 몰딩 추가 - 삭제됨 (검은색 버그 원천 봉쇄)
   */
  // addBaseboard() 메서드 삭제됨

  /**
   * 곡선 코너 조명 슬롯 생성 - 삭제됨 (검은색 버그 원천 봉쇄)
   */
  // createCornerLightSlots() 메서드 완전 삭제됨

  /**
   * 창문 생성 (좌/우 벽면에 아치형 통유리 창문)
   */
  createWindows() {
    const windowWidth = 4.0;
    const windowHeight = 3.0;
    const windowDepth = 0.3;

    // 창문 프레임 재질 (다크 우드)
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0x4a3728, // 다크 우드
      roughness: 0.7,
      metalness: 0.1
    });

    // 창문 유리 재질 (푸른 빛)
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.3,
      roughness: 0.1,
      metalness: 0.0,
      transmission: 0.9,
      emissive: 0xdddfff, // 푸른 빛 (밖에서 빛이 들어오는 효과)
      emissiveIntensity: 0.5
    });

    // 좌측 벽 창문 (Z-Fighting 방지를 위해 벽에서 0.2 안쪽으로)
    this.createArchWindow(
      -this.roomSize.width / 2 + 0.2, // -15 + 0.2 = -14.8
      windowWidth,
      windowHeight,
      windowDepth,
      frameMat,
      glassMat,
      Math.PI / 2 // Y축 회전 (벽면에 수직)
    );

    // 우측 벽 창문 (Z-Fighting 방지를 위해 벽에서 0.2 안쪽으로)
    this.createArchWindow(
      this.roomSize.width / 2 - 0.2, // 15 - 0.2 = 14.8
      windowWidth,
      windowHeight,
      windowDepth,
      frameMat,
      glassMat,
      -Math.PI / 2 // 반대 방향
    );
  }

  /**
   * 아치형 창문 생성 (간단한 버전)
   */
  createArchWindow(x, width, height, depth, frameMat, glassMat, rotationY) {
    const windowGroup = new THREE.Group();
    const windowY = height / 2 + 2; // 벽 중간 높이

    // [1] 창문 프레임 (사각형)
    const frameGeo = new THREE.BoxGeometry(width, height, depth);
    const frame = new THREE.Mesh(frameGeo, frameMat);
    frame.position.y = windowY;
    windowGroup.add(frame);

    // [2] 아치형 상단 (반원형 Torus를 사용하여 간단하게)
    const archRadius = width / 2;
    const archTorus = new THREE.Mesh(
      new THREE.TorusGeometry(archRadius, 0.15, 16, 32, Math.PI),
      frameMat
    );
    archTorus.rotation.x = Math.PI / 2;
    archTorus.position.y = windowY + height / 2;
    windowGroup.add(archTorus);

    // [3] 유리 (사각형)
    const glassGeo = new THREE.BoxGeometry(width * 0.9, height * 0.9, depth * 0.1);
    const glass = new THREE.Mesh(glassGeo, glassMat);
    glass.position.y = windowY;
    glass.position.z = depth / 2 - 0.05; // 프레임 앞쪽
    windowGroup.add(glass);

    // 아치형 유리 (반원형 Plane)
    const archGlassGeo = new THREE.PlaneGeometry(width * 0.9, archRadius * 0.9);
    const archGlass = new THREE.Mesh(archGlassGeo, glassMat);
    archGlass.rotation.x = -Math.PI / 2;
    archGlass.position.y = windowY + height / 2;
    archGlass.position.z = depth / 2 - 0.05;
    windowGroup.add(archGlass);

    // 위치 및 회전 설정
    windowGroup.position.set(x, 0, 0);
    windowGroup.rotation.y = rotationY;

    this.scene.add(windowGroup);

    // 창문에서 빛이 들어오는 효과 (DirectionalLight)
    const windowLight = new THREE.DirectionalLight(0xdddfff, 0.3);
    windowLight.position.set(x * 2, windowY, 0);
    this.scene.add(windowLight);

    return windowGroup;
  }

  /**
   * 문 생성 (삭제됨 - Commander 지시)
   */
  // createDoor() 메서드 삭제됨

  /**
   * 벽 선반 생성 (삭제됨 - Commander 지시)
   */
  // createWallShelves() 메서드 삭제됨
  // createShelf() 메서드 삭제됨
  // addShelfDecorations() 메서드 삭제됨

  /**
   * 샹들리에 생성 (삭제됨 - Commander 지시)
   */
  // createChandelier() 메서드 삭제됨

  /**
   * 진열대 생성 (바닥에 정확히 붙음)
   */
  createPedestal(position) {
    const pedestalGroup = new THREE.Group();
    const pedestalHeight = 1.4;
    const pedestalRadius = 0.5; // ⚠️ 둘레를 작게: 0.6 → 0.5
    const zFightingOffset = 0.001; // Z-Fighting 방지를 위한 최소 오프셋

    // 메인 기둥 - 투명한 유리 재질 (이쁘게!)
    const pedestalGeo = new THREE.CylinderGeometry(pedestalRadius, pedestalRadius, pedestalHeight, 32);
    const pedestalMat = new THREE.MeshPhysicalMaterial({
      color: 0xe8f4f8, // 약간 푸른빛이 도는 흰색 (프로스트 글래스 느낌)
      transparent: true,
      opacity: 0.9, // 약간 더 보이도록 (유리 느낌 유지)
      roughness: 0.05, // 매우 매끄러운 표면 (고급 유리)
      metalness: 0.0, // 비금속
      transmission: 0.92, // 거의 완전 투명 (유리 효과)
      ior: 1.5, // 유리의 굴절률 (Glass Index of Refraction)
      thickness: 0.6, // 두께감 (약간 증가하여 더 명확하게)
      side: THREE.DoubleSide, // 양면 렌더링 (투명 재질 필수)
      envMapIntensity: 1.2 // 환경 반사 강도 (유리가 주변을 반사하도록)
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    // 원기둥의 중심이 높이의 절반에 위치 (바닥면이 Y=0에 정확히 닿음)
    pedestal.position.y = pedestalHeight / 2; // 0.7 (바닥면이 Y=0.0에 정확히 닿음 - 물리법칙 준수)
    pedestal.castShadow = true;
    pedestal.receiveShadow = true; // 유리는 그림자를 받을 수 있음
    pedestalGroup.add(pedestal);

    // 상단 금색 링 (진열대 상단에 정확히 배치) - 유리와 대비되는 세련된 금색
    const topRimGeo = new THREE.TorusGeometry(pedestalRadius, 0.045, 16, 32); // 링 두께 약간 증가 (더 눈에 띄게)
    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      roughness: 0.1, // 매우 반짝이는 느낌 (고급 금속)
      metalness: 0.98, // 거의 완전한 금속 느낌
      emissive: 0xffd700, // 약간의 발광 효과
      emissiveIntensity: 0.15 // 은은한 발광
    });
    const topRim = new THREE.Mesh(topRimGeo, goldMat);
    topRim.position.y = pedestalHeight; // 1.4 (진열대 상단)
    topRim.rotation.x = Math.PI / 2;
    topRim.castShadow = true;
    pedestalGroup.add(topRim);

    // 하단 금색 링 (바닥에서 최소한의 간격으로 Z-Fighting만 방지) - 상단과 동일한 세련된 금색
    const bottomRim = new THREE.Mesh(topRimGeo, goldMat);
    bottomRim.position.y = zFightingOffset; // 0.001 (바닥에 거의 붙어 있지만 Z-Fighting 방지)
    bottomRim.rotation.x = Math.PI / 2;
    bottomRim.castShadow = true;
    pedestalGroup.add(bottomRim);

    // 위치 설정 (그룹의 Y=0으로 설정하여 바닥에 정확히 붙음)
    pedestalGroup.position.set(position.x, 0, position.z);

    // ⚠️ 물리 법칙 준수: 진열대는 바닥과 정확히 90도 수직!
    // lookAt()을 사용하면 진열대가 기울어질 수 있으므로 제거
    // rotation은 기본값(0, 0, 0)으로 유지하여 완벽한 수직 상태 보장
    pedestalGroup.rotation.set(0, 0, 0);

    this.scene.add(pedestalGroup);
    return pedestalGroup;
  }

  /**
   * 모던 면조명 천장 (Luminous Ceiling) 시공
   * 애플 스토어 스타일의 심플하고 거대한 면조명
   */
  createCofferedCeiling() {
    const ceilingGroup = new THREE.Group();
    const ceilingY = this.roomSize.height; // Y = 15 (천장 높이)
    
    // [Step 1] 하부 프레임 (White Ring) - 30x30에 24x24 구멍
    const outerFrameSize = 30; // 방 크기만큼
    const innerHoleSize = 24; // 구멍 크기
    const frameThickness = 0.5; // 두께 0.5m
    const cornerRadius = 4.0; // 둥근 모서리 반지름 4.0m

    const outerFrameShape = this.createRoundedRectShape(outerFrameSize, outerFrameSize, cornerRadius);
    const innerHoleShape = this.createRoundedRectShape(innerHoleSize, innerHoleSize, cornerRadius);
    outerFrameShape.holes.push(innerHoleShape);

    const frameGeo = new THREE.ExtrudeGeometry(outerFrameShape, {
      depth: frameThickness,
      bevelEnabled: false,
      curveSegments: 32
    });

    const frameMat = new THREE.MeshStandardMaterial({
      color: 0xFFFFFF, // 화이트
      roughness: 0.8,
      metalness: 0.0
    });

    const frame = new THREE.Mesh(frameGeo, frameMat);
    frame.rotation.x = Math.PI / 2; // 눕히기
    frame.position.y = ceilingY - frameThickness / 2; // y = 15
    ceilingGroup.add(frame);

    // [Step 2] 황금 내벽 (Golden Wall) - 24x24에 23.5x23.5 구멍, 높이 1.5m
    const goldenWallOuterSize = 24; // 프레임 구멍 크기와 동일
    const goldenWallInnerSize = 23.5; // 두께 0.25짜리 벽
    const goldenWallHeight = 1.5; // 높이 1.5m

    const goldenWallOuterShape = this.createRoundedRectShape(goldenWallOuterSize, goldenWallOuterSize, cornerRadius);
    const goldenWallInnerShape = this.createRoundedRectShape(goldenWallInnerSize, goldenWallInnerSize, cornerRadius);
    goldenWallOuterShape.holes.push(goldenWallInnerShape);

    const goldenWallGeo = new THREE.ExtrudeGeometry(goldenWallOuterShape, {
      depth: goldenWallHeight, // 높이 1.5m
      bevelEnabled: false,
      curveSegments: 32
    });

    const goldenWallMat = new THREE.MeshStandardMaterial({
      color: 0xFFD700, // 골드
      metalness: 1.0,
      roughness: 0.2
    });

    const goldenWall = new THREE.Mesh(goldenWallGeo, goldenWallMat);
    goldenWall.rotation.x = Math.PI / 2; // 눕히기
    goldenWall.position.y = ceilingY; // y = 15 (프레임 위에서 시작)
    ceilingGroup.add(goldenWall);

    // [Step 3] 상부 뚜껑 (Black Lid) - 24x24, 두께 0.1m, y=16.5
    const lidSize = 24; // 황금 벽 외곽 크기와 동일
    const lidThickness = 0.1; // 두께 0.1m
    const lidY = ceilingY + 1.5; // y = 16.5 (15 + 1.5)

    const lidShape = this.createRoundedRectShape(lidSize, lidSize, cornerRadius);
    const lidGeo = new THREE.ExtrudeGeometry(lidShape, {
      depth: lidThickness,
      bevelEnabled: false,
      curveSegments: 32
    });

    const lidMat = new THREE.MeshPhysicalMaterial({
      color: 0x050505, // 완전한 블랙
      roughness: 0.0, // 거울처럼 매끈하게
      metalness: 0.1,
      clearcoat: 1.0, // 자동차 도장 같은 광택
      clearcoatRoughness: 0.0 // 완벽한 광택
    });

    const lid = new THREE.Mesh(lidGeo, lidMat);
    lid.rotation.x = Math.PI / 2; // 눕히기
    lid.position.y = lidY; // y = 16.5
    lid.castShadow = true;
    lid.receiveShadow = true;
    ceilingGroup.add(lid);

    // [Step 4] 중앙 조명 (The Arc Reactor) - 하이테크 렌즈 스타일
    const sunRadius = 2.0; // 반지름 2m
    const sunY = lidY - 0.15; // y = 16.35 (뚜껑보다 15cm 아래, Z-fighting 해결)

    // 베이스 링 (Base Ring) - 두께를 키운 골드 링
    const baseRimGeo = new THREE.TorusGeometry(
      sunRadius, // 반지름 2.0m
      0.08, // 튜브 반지름 0.08m (두께 증가)
      16,
      64
    );
    const baseRimMat = new THREE.MeshStandardMaterial({
      color: 0xFFD700, // 골드
      metalness: 1.0,
      roughness: 0.2
    });
    const baseRim = new THREE.Mesh(baseRimGeo, baseRimMat);
    baseRim.rotation.x = Math.PI / 2; // 수평으로 배치
    baseRim.position.y = sunY; // 조명과 같은 높이
    baseRim.userData.isArcReactorBase = true; // 애니메이션용 태그
    ceilingGroup.add(baseRim);

    // 다크 렌즈 (Dark Glass) - 검투명 유리
    const darkLensGeo = new THREE.CircleGeometry(sunRadius, 64);
    const darkLensMat = new THREE.MeshPhysicalMaterial({
      color: 0x000000, // 검정색
      transparent: true,
      opacity: 0.5, // 투명도 0.5
      roughness: 0.1,
      metalness: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1 // 반사율 높음
    });
    const darkLens = new THREE.Mesh(darkLensGeo, darkLensMat);
    darkLens.rotation.x = -Math.PI / 2; // 바닥을 보게 눕힘
    darkLens.position.y = sunY; // y = 16.35
    ceilingGroup.add(darkLens);

    // 발광 코어 (Glowing Core) - RingGeometry 3개 겹쳐서 배치
    const coreRings = [];
    const coreColors = [0xFFFFFF, 0x00FFFF, 0xFFFFFF]; // 화이트-시안-화이트
    const coreRadii = [1.2, 0.8, 0.4]; // 내부에서 외부로
    const coreThicknesses = [0.15, 0.12, 0.1]; // 두께

    for (let i = 0; i < 3; i++) {
      const coreRingGeo = new THREE.RingGeometry(
        coreRadii[i] - coreThicknesses[i] / 2,
        coreRadii[i] + coreThicknesses[i] / 2,
        64
      );
      const coreRingMat = new THREE.MeshBasicMaterial({
        color: coreColors[i],
        emissive: coreColors[i],
        emissiveIntensity: 1.0, // 강력한 발광
        transparent: true,
        opacity: 0.9,
        side: THREE.DoubleSide
      });
      const coreRing = new THREE.Mesh(coreRingGeo, coreRingMat);
      coreRing.rotation.x = -Math.PI / 2; // 바닥을 보게 눕힘
      coreRing.position.y = sunY + 0.001 * (i + 1); // 살짝씩 위로 올림
      coreRing.userData.isArcReactorCore = true; // 애니메이션용 태그
      coreRing.userData.rotationSpeed = (i % 2 === 0 ? 1 : -1) * 0.005; // 반대 방향 회전
      ceilingGroup.add(coreRing);
      coreRings.push(coreRing);
    }

    // 그릴망 (The Grille) - 십자가 모양 금속 프레임
    const grilleGroup = new THREE.Group();
    const grilleThickness = 0.02;
    const grilleLength = sunRadius * 0.8;
    
    // 가로선
    const horizontalGrille = new THREE.Mesh(
      new THREE.BoxGeometry(grilleLength, grilleThickness, grilleThickness),
      new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.8, roughness: 0.3 })
    );
    horizontalGrille.rotation.z = Math.PI / 2;
    grilleGroup.add(horizontalGrille);
    
    // 세로선
    const verticalGrille = new THREE.Mesh(
      new THREE.BoxGeometry(grilleLength, grilleThickness, grilleThickness),
      new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.8, roughness: 0.3 })
    );
    verticalGrille.rotation.x = Math.PI / 2;
    grilleGroup.add(verticalGrille);
    
    grilleGroup.rotation.x = -Math.PI / 2; // 바닥을 보게 눕힘
    grilleGroup.position.y = sunY + 0.002; // 렌즈 위에 살짝 올림
    ceilingGroup.add(grilleGroup);

    // [Step 3-1] 코너 장식 (Gold Studs) - 블랙 패널 네 귀퉁이에 황금 볼트 4개
    const studRadius = 0.3; // 볼트 반지름
    const studHeight = 0.1; // 볼트 높이 (납작한 원기둥)
    const studY = lidY + lidThickness / 2; // y = 16.45 (패널에 박혀있는 느낌)
    const studOffset = lidSize / 2 - 2.0; // 패널 안쪽으로 조금 들어온 위치 (±10 정도)

    const studGeo = new THREE.CylinderGeometry(studRadius, studRadius, studHeight, 16);
    const studMat = new THREE.MeshStandardMaterial({
      color: 0xFFD700, // 골드
      metalness: 1.0,
      roughness: 0.2
    });

    // 앞쪽 좌측 볼트
    const stud1 = new THREE.Mesh(studGeo, studMat);
    stud1.rotation.x = Math.PI / 2; // 눕히기
    stud1.position.set(-studOffset, studY, studOffset);
    ceilingGroup.add(stud1);

    // 앞쪽 우측 볼트
    const stud2 = new THREE.Mesh(studGeo, studMat);
    stud2.rotation.x = Math.PI / 2;
    stud2.position.set(studOffset, studY, studOffset);
    ceilingGroup.add(stud2);

    // 뒷쪽 좌측 볼트
    const stud3 = new THREE.Mesh(studGeo, studMat);
    stud3.rotation.x = Math.PI / 2;
    stud3.position.set(-studOffset, studY, -studOffset);
    ceilingGroup.add(stud3);

    // 뒷쪽 우측 볼트
    const stud4 = new THREE.Mesh(studGeo, studMat);
    stud4.rotation.x = Math.PI / 2;
    stud4.position.set(studOffset, studY, -studOffset);
    ceilingGroup.add(stud4);

    // [Step 5] 황금 환풍구 (Golden Vents) - 리얼한 그릴 스타일
    /**
     * 환풍구 생성 헬퍼 함수
     * @param {number} x - X 위치
     * @param {number} z - Z 위치
     * @returns {THREE.Group} 환풍구 그룹
     */
    const createVent = (x, z) => {
      const ventGroup = new THREE.Group();
      const ventWidth = 4; // 가로 길이
      const ventHeight = 0.1; // 높이
      const ventDepth = 8; // 세로 길이
      const ventY = lidY - 0.3; // y = 15.2 (블랙 패널 표면)
      
      const ventMat = new THREE.MeshStandardMaterial({
        color: 0xFFD700, // 골드
        metalness: 1.0,
        roughness: 0.4 // 너무 번쩍이지 않게 거칠기 증가
      });

      // 프레임: 4개의 얇은 막대로 외곽틀 조립 (중앙 비움)
      const frameThickness = 0.08; // 프레임 두께
      
      // 상단 막대
      const topFrame = new THREE.Mesh(
        new THREE.BoxGeometry(ventWidth, ventHeight, frameThickness),
        ventMat
      );
      topFrame.position.set(x, ventY, z + ventDepth / 2 - frameThickness / 2);
      ventGroup.add(topFrame);
      
      // 하단 막대
      const bottomFrame = new THREE.Mesh(
        new THREE.BoxGeometry(ventWidth, ventHeight, frameThickness),
        ventMat
      );
      bottomFrame.position.set(x, ventY, z - ventDepth / 2 + frameThickness / 2);
      ventGroup.add(bottomFrame);
      
      // 좌측 막대
      const leftFrame = new THREE.Mesh(
        new THREE.BoxGeometry(frameThickness, ventHeight, ventDepth - frameThickness * 2),
        ventMat
      );
      leftFrame.position.set(x - ventWidth / 2 + frameThickness / 2, ventY, z);
      ventGroup.add(leftFrame);
      
      // 우측 막대
      const rightFrame = new THREE.Mesh(
        new THREE.BoxGeometry(frameThickness, ventHeight, ventDepth - frameThickness * 2),
        ventMat
      );
      rightFrame.position.set(x + ventWidth / 2 - frameThickness / 2, ventY, z);
      ventGroup.add(rightFrame);

      // 살(Slats): 가로지르는 얇은 막대 15개 등간격 배치
      const slatCount = 15;
      const slatWidth = 3.8; // 프레임 안쪽에 맞춤
      const slatThickness = 0.05; // 막대 두께
      const slatDepth = 0.2; // 막대 깊이
      const slatGap = 0.35; // 간격 (막대 두께보다 넓음 - 줄무늬 효과)
      const totalSlatSpace = (slatCount - 1) * slatGap + slatThickness; // 전체 공간
      const startZ = z - totalSlatSpace / 2 + slatThickness / 2; // 시작 위치
      
      for (let i = 0; i < slatCount; i++) {
        const slat = new THREE.Mesh(
          new THREE.BoxGeometry(slatWidth, ventHeight, slatDepth),
          ventMat
        );
        slat.position.set(x, ventY, startZ + i * slatGap);
        ventGroup.add(slat);
      }

      return ventGroup;
    };

    // 좌측 환풍구
    const leftVent = createVent(-8, 0);
    ceilingGroup.add(leftVent);

    // 우측 환풍구
    const rightVent = createVent(8, 0);
    ceilingGroup.add(rightVent);

    // [Step 6] 돔형 CCTV (Security Cameras) - 천장 프레임 네 귀퉁이
    const cctvRadius = 0.5; // CCTV 반지름
    const cctvX = 12; // 천장 프레임 귀퉁이 위치
    const cctvZ = 12;
    const cctvY = ceilingY + 0.1; // y = 15.1 (천장 프레임 위)

    const cctvMat = new THREE.MeshPhysicalMaterial({
      color: 0xEEEEEE, // 화이트/실버 (천장에서 눈에 띄게)
      roughness: 0.1,
      metalness: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1
    });

    const redDotMat = new THREE.MeshBasicMaterial({
      color: 0xFF0000, // 빨간 점
      emissive: 0xFF0000,
      emissiveIntensity: 5.0 // 레이저처럼 강하게 빛남
    });

    // 방 중앙을 바라보는 회전 계산 헬퍼 (45도 각도로 정확히 꺾임)
    const lookAtCenter = (cameraGroup, x, z) => {
      const centerX = 0;
      const centerZ = 0;
      const dx = centerX - x;
      const dz = centerZ - z;
      const angle = Math.atan2(dx, dz);
      cameraGroup.rotation.y = angle; // Y축 회전 (수평)
      // 아래를 보도록 약간 기울임 (45도 각도)
      cameraGroup.rotation.x = -Math.PI / 4; // -45도
    };

    // 앞쪽 좌측 CCTV
    const cctv1Group = new THREE.Group();
    const cctv1 = new THREE.Mesh(
      new THREE.SphereGeometry(cctvRadius, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      cctvMat
    );
    cctv1.rotation.x = Math.PI; // 아래를 보게 뒤집기
    cctv1Group.add(cctv1);
    // 빨간 점 (크기 증가)
    const redDot1 = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16), // 크기 증가 (0.05 -> 0.08)
      redDotMat
    );
    redDot1.position.set(0, -cctvRadius * 0.7, 0); // 반구 중앙 아래
    cctv1Group.add(redDot1);
    cctv1Group.position.set(-cctvX, cctvY, cctvZ);
    lookAtCenter(cctv1Group, -cctvX, cctvZ);
    ceilingGroup.add(cctv1Group);

    // 앞쪽 우측 CCTV
    const cctv2Group = new THREE.Group();
    const cctv2 = new THREE.Mesh(
      new THREE.SphereGeometry(cctvRadius, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      cctvMat
    );
    cctv2.rotation.x = Math.PI;
    cctv2Group.add(cctv2);
    const redDot2 = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16), // 크기 증가
      redDotMat
    );
    redDot2.position.set(0, -cctvRadius * 0.7, 0);
    cctv2Group.add(redDot2);
    cctv2Group.position.set(cctvX, cctvY, cctvZ);
    lookAtCenter(cctv2Group, cctvX, cctvZ);
    ceilingGroup.add(cctv2Group);

    // 뒷쪽 좌측 CCTV
    const cctv3Group = new THREE.Group();
    const cctv3 = new THREE.Mesh(
      new THREE.SphereGeometry(cctvRadius, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      cctvMat
    );
    cctv3.rotation.x = Math.PI;
    cctv3Group.add(cctv3);
    const redDot3 = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16), // 크기 증가
      redDotMat
    );
    redDot3.position.set(0, -cctvRadius * 0.7, 0);
    cctv3Group.add(redDot3);
    cctv3Group.position.set(-cctvX, cctvY, -cctvZ);
    lookAtCenter(cctv3Group, -cctvX, -cctvZ);
    ceilingGroup.add(cctv3Group);

    // 뒷쪽 우측 CCTV
    const cctv4Group = new THREE.Group();
    const cctv4 = new THREE.Mesh(
      new THREE.SphereGeometry(cctvRadius, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
      cctvMat
    );
    cctv4.rotation.x = Math.PI;
    cctv4Group.add(cctv4);
    const redDot4 = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16), // 크기 증가
      redDotMat
    );
    redDot4.position.set(0, -cctvRadius * 0.7, 0);
    cctv4Group.add(redDot4);
    cctv4Group.position.set(cctvX, cctvY, -cctvZ);
    lookAtCenter(cctv4Group, cctvX, -cctvZ);
    ceilingGroup.add(cctv4Group);

    // 중앙 PointLight - 황금 벽을 비추는 강한 조명
    const centerLight = new THREE.PointLight(0xFFFFFF, 2.0, 30);
    centerLight.position.set(0, ceilingY + 1.0, 0); // y = 16 (황금 벽 중간)
    this.scene.add(centerLight);

    // 천장 그룹을 씬에 추가
    this.scene.add(ceilingGroup);

    console.log("✅ [ShowroomBuilder] 확실한 계단식 천장 시공 완료");
    return ceilingGroup;
  }


  /**
   * 샹들리에 애니메이션 업데이트 (삭제됨 - Commander 지시)
   */
  // updateChandelierAnimation() 메서드 삭제됨
}

// 전역 객체로 노출
window.ShowroomBuilder = ShowroomBuilder;
console.log("✅ [ShowroomBuilder] 전역 객체로 노출 완료:", typeof window.ShowroomBuilder);

