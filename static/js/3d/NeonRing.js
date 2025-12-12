/**
 * NeonRing - 네온 링 가구 3D 모델
 * 빛나는 고리 모양의 가구 (TorusGeometry 기반)
 * 
 * @class NeonRing
 * @description ProductFactory에서 사용하는 네온 링 가구 클래스
 */
class NeonRing {
  /**
   * Static Material 공유 (WebGL 텍스처 유닛 최적화)
   */
  static sharedNeonMat = null;

  /**
   * Static Geometry 공유 (메모리 최적화)
   */
  static sharedTorusGeo = null;

  /**
   * 네온 링 Material 가져오기
   */
  static getNeonMaterial() {
    if (!NeonRing.sharedNeonMat) {
      NeonRing.sharedNeonMat = new THREE.MeshStandardMaterial({
        color: 0x00ffff, // Cyan 기본 색상
        emissive: 0x00ffff, // 발광 색상 (Cyan 형광)
        emissiveIntensity: 1.5, // 발광 강도
        metalness: 0.3,
        roughness: 0.2
      });
    }
    return NeonRing.sharedNeonMat;
  }

  /**
   * Torus Geometry 가져오기
   */
  static getTorusGeometry() {
    if (!NeonRing.sharedTorusGeo) {
      // TorusGeometry(radius, tube, radialSegments, tubularSegments)
      NeonRing.sharedTorusGeo = new THREE.TorusGeometry(1.0, 0.3, 32, 64);
    }
    return NeonRing.sharedTorusGeo;
  }

  /**
   * 네온 링 모델 생성
   * @param {Object} product - 상품 데이터
   * @param {THREE.Vector3} position - 위치
   * @returns {THREE.Group} 네온 링 그룹
   */
  static createModel(product = null, position = new THREE.Vector3(0, 0, 0)) {
    const group = new THREE.Group();

    // Material과 Geometry 가져오기 (Static 공유)
    const neonMat = NeonRing.getNeonMaterial();
    const torusGeo = NeonRing.getTorusGeometry();

    // 메인 링 생성
    const mainRing = new THREE.Mesh(torusGeo, neonMat);
    mainRing.castShadow = true;
    mainRing.receiveShadow = true;
    group.add(mainRing);

    // 내부 링 추가 (디테일)
    const innerRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.7, 0.15, 24, 48),
      neonMat.clone()
    );
    innerRing.material.emissiveIntensity = 0.8;
    innerRing.castShadow = true;
    group.add(innerRing);

    // 외부 링 추가 (디테일)
    const outerRing = new THREE.Mesh(
      new THREE.TorusGeometry(1.3, 0.2, 24, 48),
      neonMat.clone()
    );
    outerRing.material.emissiveIntensity = 1.2;
    outerRing.castShadow = true;
    group.add(outerRing);

    // 위치 설정
    group.position.copy(position);

    // 회전 애니메이션을 위한 userData 설정
    group.userData.rotationSpeed = 0.01; // 회전 속도
    group.userData.isAnimating = true;

    // 상품 데이터 저장
    if (product) {
      group.userData.productData = product;
    }

    console.log('✅ [NeonRing] 네온 링 모델 생성 완료');
    return group;
  }

  /**
   * 회전 애니메이션 업데이트
   * @param {THREE.Group} group - 애니메이션을 적용할 그룹
   */
  static animate(group) {
    if (!group || !group.userData.isAnimating) return;

    // Y축 중심으로 천천히 회전
    group.rotation.y += group.userData.rotationSpeed || 0.01;

    // 약간의 X축 흔들림 추가 (선택적)
    // group.rotation.x = Math.sin(Date.now() * 0.001) * 0.1;
  }
}

// 전역 객체로 노출
if (typeof window !== 'undefined') {
  window.NeonRing = NeonRing;
}

// ES6 모듈로도 노출 (선택적)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NeonRing;
}


