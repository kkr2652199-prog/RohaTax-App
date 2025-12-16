/**
 * Pedestal3D - 3D 진열대 클래스
 * ShowroomBuilder에서 분리된 독립적인 진열대 생성 모듈
 */
class Pedestal3D {
  /**
   * ✅ WebGL 텍스처 유닛 최적화: Static Material 공유
   * 모든 Pedestal3D 인스턴스가 동일한 Material을 공유하여 텍스처 유닛 절약
   */
  static sharedPedestalMat = null;  // 진열대 Material
  static sharedGoldMat = null;      // 골드 Material

  /**
   * 진열대 생성자
   * @param {THREE.Vector3|Object} position - 진열대 위치 (x, y, z 또는 {x, y, z})
   */
  constructor(position) {
    this.group = new THREE.Group();
    this.position = position;
    
    // 위치를 Vector3로 변환
    const pos = position instanceof THREE.Vector3 
      ? position 
      : new THREE.Vector3(position.x, position.y || 0, position.z);
    
    this._buildPedestal(pos);
  }

  /**
   * 진열대 메쉬 구성
   * @private
   */
  _buildPedestal(position) {
    const pedestalHeight = 1.4;
    const pedestalRadius = 0.5; // ⚠️ 둘레를 작게: 0.6 → 0.5
    const zFightingOffset = 0.001; // Z-Fighting 방지를 위한 최소 오프셋

    // 메인 기둥 - 투명한 유리 재질 (이쁘게!)
    const pedestalGeo = new THREE.CylinderGeometry(pedestalRadius, pedestalRadius, pedestalHeight, 32);
    // ✅ WebGL 최적화: Static Material 공유 + envMapIntensity 제거
    if (!Pedestal3D.sharedPedestalMat) {
      Pedestal3D.sharedPedestalMat = new THREE.MeshStandardMaterial({
        color: 0xe8f4f8, // 약간 푸른빛이 도는 흰색 (프로스트 글래스 느낌)
        transparent: true,
        opacity: 0.9, // 약간 더 보이도록 (유리 느낌 유지)
        roughness: 0.05, // 매우 매끄러운 표면 (고급 유리)
        metalness: 0.0, // 비금속
        side: THREE.DoubleSide, // 양면 렌더링 (투명 재질 필수)
        // transmission, ior, thickness, envMapIntensity 제거: MeshStandardMaterial로 변경하여 텍스처 유닛 절약
      });
    }
    const pedestalMat = Pedestal3D.sharedPedestalMat;
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    // 원기둥의 중심이 높이의 절반에 위치 (바닥면이 Y=0에 정확히 닿음)
    pedestal.position.y = pedestalHeight / 2; // 0.7 (바닥면이 Y=0.0에 정확히 닿음 - 물리법칙 준수)
    pedestal.castShadow = true;
    pedestal.receiveShadow = true; // 유리는 그림자를 받을 수 있음
    this.group.add(pedestal);

    // 상단 금색 링 (진열대 상단에 정확히 배치) - 유리와 대비되는 세련된 금색
    const topRimGeo = new THREE.TorusGeometry(pedestalRadius, 0.045, 16, 32); // 링 두께 약간 증가 (더 눈에 띄게)
    // ✅ WebGL 최적화: Static Material 공유
    if (!Pedestal3D.sharedGoldMat) {
      Pedestal3D.sharedGoldMat = new THREE.MeshStandardMaterial({
        color: 0xffd700,
        roughness: 0.1, // 매우 반짝이는 느낌 (고급 금속)
        metalness: 0.98, // 거의 완전한 금속 느낌
        emissive: 0xffd700, // 약간의 발광 효과
        emissiveIntensity: 0.15 // 은은한 발광
      });
    }
    const goldMat = Pedestal3D.sharedGoldMat;
    const topRim = new THREE.Mesh(topRimGeo, goldMat);
    topRim.position.y = pedestalHeight; // 1.4 (진열대 상단)
    topRim.rotation.x = Math.PI / 2;
    topRim.castShadow = true;
    this.group.add(topRim);

    // 하단 금색 링 (바닥에서 최소한의 간격으로 Z-Fighting만 방지) - 상단과 동일한 세련된 금색
    const bottomRim = new THREE.Mesh(topRimGeo, goldMat);
    bottomRim.position.y = zFightingOffset; // 0.001 (바닥에 거의 붙어 있지만 Z-Fighting 방지)
    bottomRim.rotation.x = Math.PI / 2;
    bottomRim.castShadow = true;
    this.group.add(bottomRim);

    // 위치 설정 (그룹의 Y=0으로 설정하여 바닥에 정확히 붙음)
    this.group.position.set(position.x, 0, position.z);

    // ⚠️ 물리 법칙 준수: 진열대는 바닥과 정확히 90도 수직!
    // lookAt()을 사용하면 진열대가 기울어질 수 있으므로 제거
    // rotation은 기본값(0, 0, 0)으로 유지하여 완벽한 수직 상태 보장
    this.group.rotation.set(0, 0, 0);
  }

  /**
   * 리소스 정리
   */
  dispose() {
    // Material은 Static 공유이므로 여기서 dispose하지 않음
    // Geometry는 Three.js가 자동으로 관리
    if (this.group) {
      this.group.clear();
      this.group = null;
    }
  }
}

// 전역 변수로 노출 (기존 프로젝트와의 호환성)
if (typeof window !== 'undefined') {
  window.Pedestal3D = Pedestal3D;
}

// ES6 모듈로도 노출 (선택적)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Pedestal3D;
}

