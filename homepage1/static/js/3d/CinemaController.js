/**
 * CinemaController - 시네마 모드 전담 제어 클래스
 * TV 비디오 재생 시 카메라와 조명을 부드럽게 제어하여 몰입감을 제공
 */
class CinemaController {
  constructor(showroom) {
    if (!showroom) {
      console.error("[CinemaController] showroom 인스턴스가 필요합니다.");
      return;
    }
    
    this.showroom = showroom;
    this.isActive = false;
    this.savedState = null;
    
    // 애니메이션 속도 계수 (0.02 = 매우 부드러운 전환 - Soft Landing)
    this.lerpSpeed = 0.02;
    
    // 목표 상태 (진입 시 설정됨)
    this.targetState = {
      camera: {
        position: null,
        quaternion: null
      },
      lights: {
        hemisphere: null,
        ambient: null,
        spotlights: [] // 각 스포트라이트의 목표 intensity
      }
    };
    
    // 현재 전환 진행도 (0.0 ~ 1.0)
    this.transitionProgress = 0.0;
  }
  
  /**
   * 시네마 모드 진입
   * @param {THREE.Vector3} tvPosition - TV의 3D 위치 (또는 {x, y, z} 객체)
   */
  enterCinema(tvPosition) {
    console.log("🎬 [Cinema] enterCinema called. TV Position:", tvPosition);
    
    if (this.isActive) {
      console.warn("[CinemaController] 이미 시네마 모드가 활성화되어 있습니다.");
      return;
    }
    
    // 1. 시네마 모드 플래그 즉시 활성화 (FPS 컨트롤 차단)
    this.showroom.isCinemaMode = true;
    
    // 2. 현재 상태 깊은 복사로 저장 (카메라는 나중에 이동할 때 사용)
    this.savedState = {
      camera: {
        position: this.showroom.camera.position.clone(),
        quaternion: this.showroom.camera.quaternion.clone()
      },
      lights: {
        hemisphere: this.showroom.hemisphereLight ? this.showroom.hemisphereLight.intensity : null,
        ambient: this.showroom.ambientLight ? this.showroom.ambientLight.intensity : null,
        spotlights: this.showroom.spotLights ? this.showroom.spotLights.map(light => light.intensity) : []
      }
    };
    
    // 3. 조명 즉시 변경 (5%로 대폭 감소 - 영상 집중을 위해 매우 어둡게)
    if (this.showroom.hemisphereLight) {
      this.targetState.lights.hemisphere = this.savedState.lights.hemisphere * 0.05;
      this.showroom.hemisphereLight.intensity = this.targetState.lights.hemisphere;
    }
    if (this.showroom.ambientLight) {
      this.targetState.lights.ambient = this.savedState.lights.ambient * 0.05;
      this.showroom.ambientLight.intensity = this.targetState.lights.ambient;
    }
    if (this.showroom.spotLights && this.showroom.spotLights.length > 0) {
      this.targetState.lights.spotlights = this.savedState.lights.spotlights.map(intensity => intensity * 0.05);
      this.showroom.spotLights.forEach((light, index) => {
        if (index < this.targetState.lights.spotlights.length) {
          light.intensity = this.targetState.lights.spotlights[index];
        }
      });
    }
    
    // 4. 카메라 위치 즉시 설정 (극장 경험)
    // TV 정중앙: (0, 707.5cm, 1500cm)
    // TV 화면 하단: 247.5cm, 사운드바 상단: 247.5cm
    // TV 화면 중앙: 707.5cm
    // 카메라 높이: TV와 사운드바 중간 (627.5cm) - 위로 50cm 추가 이동
    // TV 앞 거리: 13.2m (180cm) - 앞으로 30cm 추가 이동 (1.5m -> 1.8m)
    this.targetState.camera.position = new THREE.Vector3(0, 6.275, 1.8);
    
    // 카메라 시선: 수평으로 TV를 바라봄 (X축 회전 없음)
    const dummy = new THREE.Object3D();
    dummy.position.copy(this.targetState.camera.position);
    // 수평 시선: 카메라 높이(6.275m)와 같은 높이로 TV를 바라봄
    // Y축 회전만 사용 (X축 회전 없음 - 수평 유지)
    dummy.lookAt(0, 6.275, 15.0); // 수평 시선 유지 (카메라와 같은 높이로 바라봄)
    // 180도 회전 (TV 정면 방향으로)
    dummy.rotateY(Math.PI);
    this.targetState.camera.quaternion = dummy.quaternion.clone();
    
    // 카메라 즉시 이동 (부드러운 전환 없음)
    if (this.showroom.camera) {
      this.showroom.camera.position.copy(this.targetState.camera.position);
      this.showroom.camera.quaternion.copy(this.targetState.camera.quaternion);
    }
    
    this.isActive = true;
    
    console.log("✅ [Cinema] 시네마 모드 즉시 진입 완료! (조명만 변경, 카메라는 나중에)");
    console.log("   - Showroom.isCinemaMode:", this.showroom.isCinemaMode);
  }
  
  /**
   * 시네마 모드 퇴장
   */
  exitCinema() {
    console.log("⏸️ [Cinema] exitCinema called. Current isActive:", this.isActive);
    
    if (!this.isActive) {
      console.warn("[CinemaController] 시네마 모드가 활성화되어 있지 않습니다.");
      return;
    }
    
    // 1. 시네마 모드 플래그 즉시 비활성화 (FPS 컨트롤 복구)
    this.showroom.isCinemaMode = false;
    
    // 2. 조명 즉시 복구 (원래 밝기로)
    if (this.savedState) {
      if (this.showroom.hemisphereLight && this.savedState.lights.hemisphere !== null) {
        this.showroom.hemisphereLight.intensity = this.savedState.lights.hemisphere;
      }
      if (this.showroom.ambientLight && this.savedState.lights.ambient !== null) {
        this.showroom.ambientLight.intensity = this.savedState.lights.ambient;
      }
      if (this.showroom.spotLights && this.savedState.lights.spotlights.length > 0) {
        this.showroom.spotLights.forEach((light, index) => {
          if (index < this.savedState.lights.spotlights.length) {
            light.intensity = this.savedState.lights.spotlights[index];
          }
        });
      }
      
      // 3. 카메라 즉시 복귀 (원래 위치로)
      if (this.showroom.camera && this.savedState.camera.position) {
        this.showroom.camera.position.copy(this.savedState.camera.position);
        this.showroom.camera.quaternion.copy(this.savedState.camera.quaternion);
      }
    }
    
    this.isActive = false;
    this.transitionProgress = 0.0;
    this.savedState = null;
    
    console.log("✅ [Cinema] 시네마 모드 즉시 해제 완료! (조명만 복구, 카메라는 나중에)");
    console.log("   - Showroom.isCinemaMode:", this.showroom.isCinemaMode);
  }
  
  /**
   * 애니메이션 업데이트 (매 프레임 호출)
   * Showroom.js의 animate() 루프에서 호출됨
   * 
   * 현재: 카메라 이동 비활성화, 조명만 즉시 변경
   * 나중에: 카메라 이동 로직 추가 예정
   */
  update() {
    // 카메라 이동은 나중에 처리 (지금은 비활성화)
    // 조명은 enterCinema/exitCinema에서 즉시 변경하므로 여기서는 아무것도 하지 않음
    
    // 디버깅: 주기적으로 상태 확인 (너무 많이 찍히지 않게)
    if (this.frameCount === undefined) {
      this.frameCount = 0;
    }
    this.frameCount++;
    
    if (this.frameCount % 300 === 0) {
      console.log("🔄 [Cinema] update() 실행 중... isActive:", this.isActive, "isCinemaMode:", this.showroom.isCinemaMode);
    }
    
    // 현재는 카메라 이동 없이 플래그만 관리
    // 나중에 카메라 이동 로직 추가 예정
  }
  
  /**
   * 시네마 모드 상태 확인
   * @returns {boolean} 시네마 모드 활성화 여부
   */
  getIsActive() {
    return this.isActive;
  }
}

// 전역 객체로 등록 (ES6 모듈이 아닌 환경에서 사용)
window.CinemaController = CinemaController;

