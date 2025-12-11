# 🏛️ 3D 쇼룸 구조 점검 보고서

**점검 일시**: 2025-01-XX  
**점검 대상**: `homepage1/static/js/3d/` 디렉토리  
**점검 목적**: 리팩토링 필요성 평가 및 코드 품질 분석

---

## 📊 파일 현황

### 파일 크기 분석

| 파일명 | 라인 수 | 상태 | 500줄 규칙 준수 |
|--------|---------|------|----------------|
| `Showroom.js` | **1,400줄** | ⚠️ **초과** | ❌ **2.8배 초과** |
| `ShowroomBuilder.js` | **1,221줄** | ⚠️ **초과** | ❌ **2.4배 초과** |
| `ProductFactory.js` | **700줄** | ⚠️ **초과** | ❌ **1.4배 초과** |
| `GiftBox3D.js` | **1,019줄** | ⚠️ **초과** | ❌ **2.0배 초과** |
| `event_products_3d_scene.js` | **596줄** | ⚠️ **초과** | ❌ **1.2배 초과** |
| `JewelryDisplay.js` | **209줄** | ✅ **정상** | ✅ **준수** |

**총 라인 수**: 5,145줄  
**500줄 초과 파일**: 5개  
**500줄 이하 파일**: 1개

---

## 🔍 구조 분석

### 1. Showroom.js (1,400줄) - 메인 쇼룸 클래스

#### 주요 책임
- ✅ 3D 씬 초기화 (Renderer, Scene, Camera)
- ✅ FPS 컨트롤 (WASD 이동, 마우스 시점)
- ✅ 조명 관리 (Spotlight, Ambient, Point)
- ✅ 상품 배치 및 레이아웃
- ✅ 애니메이션 루프 (animate)
- ⚠️ **진열대 생성** (createPodium) - ShowroomBuilder로 이동 가능
- ⚠️ **대리석 텍스처 생성** (createMarbleTexture) - ShowroomBuilder로 이동 가능
- ⚠️ **사용하지 않는 메서드** (createSimpleJewelryDisplay - deprecated)

#### 리팩토링 필요성: **높음** ⚠️

**문제점**:
1. **책임 과다**: 쇼룸 관리 + 진열대 생성 + 텍스처 생성
2. **사용하지 않는 코드**: `createSimpleJewelryDisplay()` (deprecated)
3. **중복 가능성**: `createMarbleTexture()`가 ShowroomBuilder에도 존재

**제안**:
- `createPodium()` → ShowroomBuilder로 이동
- `createMarbleTexture()` → ShowroomBuilder로 이동 (이미 존재하지만 중복 확인 필요)
- `createSimpleJewelryDisplay()` → 삭제 (deprecated)

---

### 2. ShowroomBuilder.js (1,221줄) - 쇼룸 인테리어 구성

#### 주요 책임
- ✅ 방 구성 (바닥, 벽, 천장)
- ✅ 진열대 생성 (createPedestal)
- ✅ CCTV 생성
- ✅ 조명 스트립 생성
- ✅ 대리석 텍스처 생성 (createMarbleTexture)
- ✅ 코브(Cove) 생성 (벽/바닥 모서리)
- ✅ 격자 천장 생성

#### 리팩토링 필요성: **중간** ⚠️

**문제점**:
1. **파일 크기**: 1,221줄로 500줄 규칙 2.4배 초과
2. **복잡한 메서드**: 각 생성 메서드가 상당히 길 수 있음

**제안**:
- **연동 모듈 분리 고려**:
  - `ShowroomBuilder_utils/FloorBuilder.js` - 바닥 관련
  - `ShowroomBuilder_utils/WallBuilder.js` - 벽 관련
  - `ShowroomBuilder_utils/CeilingBuilder.js` - 천장 관련
  - `ShowroomBuilder_utils/LightBuilder.js` - 조명 관련

**주의**: 연장형 모듈 관리 원칙 준수 (파일 분리 금지, 연동 모듈로만 확장)

---

### 3. ProductFactory.js (700줄) - 상품 3D 모델 생성

#### 주요 책임
- ✅ Standard 코인 생성
- ✅ Premium 큐브 생성
- ✅ Gold 크라운 생성
- ✅ 이벤트 상품 생성 (GiftBox3D 사용)
- ✅ Fallback 상품 생성
- ✅ Static Material/Geometry 공유 (WebGL 최적화)

#### 리팩토링 필요성: **낮음** ✅

**현재 상태**:
- ✅ 이미 WebGL 최적화 완료 (Static Material/Geometry 공유)
- ✅ 책임이 명확함 (상품 생성만 담당)
- ⚠️ 파일 크기만 500줄 초과 (기능적으로는 문제 없음)

**제안**:
- 현재 구조 유지 권장
- 필요시 연동 모듈로 확장 가능하지만 우선순위 낮음

---

### 4. GiftBox3D.js (1,019줄) - 선물 상자 3D 모델

#### 주요 책임
- ✅ 선물 상자 생성 (박스, 라이너, 리본)
- ✅ 컨페티 애니메이션
- ✅ Static Material 공유 (WebGL 최적화)

#### 리팩토링 필요성: **중간** ⚠️

**문제점**:
1. **파일 크기**: 1,019줄로 500줄 규칙 2.0배 초과
2. **복잡한 애니메이션 로직**: 컨페티 생성 및 애니메이션

**제안**:
- **연동 모듈 분리 고려**:
  - `GiftBox3D_utils/BoxBuilder.js` - 박스 생성
  - `GiftBox3D_utils/ConfettiAnimator.js` - 컨페티 애니메이션

**주의**: 연장형 모듈 관리 원칙 준수

---

### 5. event_products_3d_scene.js (596줄) - 이벤트 상품 씬

#### 주요 책임
- ✅ 이벤트 상품 3D 씬 관리
- ✅ GiftBox3D 연동

#### 리팩토링 필요성: **낮음** ✅

**현재 상태**:
- ✅ 파일 크기가 500줄에 근접하지만 기능적으로 문제 없음
- ✅ 책임이 명확함

**제안**:
- 현재 구조 유지 권장

---

### 6. JewelryDisplay.js (209줄) - 보석 진열대

#### 주요 책임
- ✅ 보석 진열대 생성
- ✅ 유리 케이스 생성

#### 리팩토링 필요성: **없음** ✅

**현재 상태**:
- ✅ 500줄 규칙 준수
- ✅ 책임이 명확함
- ✅ 코드 품질 양호

---

## 🎯 종합 평가

### 리팩토링 우선순위

| 우선순위 | 파일 | 이유 | 작업량 |
|---------|------|------|--------|
| **1순위** | `Showroom.js` | 책임 과다, 사용하지 않는 코드, 중복 가능성 | 중간 |
| **2순위** | `ShowroomBuilder.js` | 파일 크기 과다, 복잡한 메서드 | 높음 |
| **3순위** | `GiftBox3D.js` | 파일 크기 과다, 복잡한 애니메이션 | 중간 |
| **4순위** | `ProductFactory.js` | 파일 크기만 초과, 기능적으로 문제 없음 | 낮음 |
| **5순위** | `event_products_3d_scene.js` | 500줄에 근접하지만 문제 없음 | 낮음 |

### 리팩토링 필요성: **중간** ⚠️

**결론**:
- ✅ **기능적으로는 정상 작동** (WebGL 최적화 완료)
- ⚠️ **코드 품질 측면에서 개선 여지 있음** (500줄 규칙 위반)
- ⚠️ **유지보수성 향상 필요** (특히 Showroom.js)

---

## 📋 리팩토링 제안

### Phase 1: Showroom.js 정리 (우선순위 높음)

1. **사용하지 않는 코드 제거**:
   - `createSimpleJewelryDisplay()` 삭제 (deprecated)

2. **책임 분리**:
   - `createPodium()` → ShowroomBuilder로 이동 검토
   - `createMarbleTexture()` → ShowroomBuilder로 이동 (중복 확인 후)

3. **코드 정리**:
   - 주석 정리
   - 불필요한 변수 제거

### Phase 2: ShowroomBuilder.js 모듈화 (우선순위 중간)

1. **연동 모듈 생성** (연장형 원칙 준수):
   - `ShowroomBuilder_utils/FloorBuilder.js` - 바닥 관련
   - `ShowroomBuilder_utils/WallBuilder.js` - 벽 관련
   - `ShowroomBuilder_utils/CeilingBuilder.js` - 천장 관련

2. **주의사항**:
   - 메인 파일(`ShowroomBuilder.js`) 분리 금지
   - 연동 모듈로만 확장

### Phase 3: GiftBox3D.js 모듈화 (우선순위 낮음)

1. **연동 모듈 생성**:
   - `GiftBox3D_utils/ConfettiAnimator.js` - 컨페티 애니메이션 분리

---

## ✅ 현재 상태 요약

### 잘 된 점
- ✅ **WebGL 최적화 완료**: Static Material/Geometry 공유로 텍스처 유닛 절약
- ✅ **모듈화 구조**: Showroom, Builder, Factory로 책임 분리
- ✅ **연동 모듈 패턴**: 연장형 모듈 관리 원칙 준수
- ✅ **기능 정상 작동**: 모든 기능이 정상적으로 작동

### 개선 필요
- ⚠️ **파일 크기**: 5개 파일이 500줄 규칙 위반
- ⚠️ **책임 분리**: Showroom.js에 과도한 책임
- ⚠️ **코드 정리**: 사용하지 않는 코드(deprecated) 존재

---

## 🎯 최종 권고사항

### 즉시 조치 (High Priority)
1. **Showroom.js 정리**: 사용하지 않는 코드 제거
2. **책임 분리**: createPodium, createMarbleTexture 이동 검토

### 단기 조치 (Medium Priority)
1. **ShowroomBuilder.js 모듈화**: 연동 모듈로 확장
2. **GiftBox3D.js 모듈화**: 컨페티 애니메이션 분리

### 장기 조치 (Low Priority)
1. **ProductFactory.js**: 현재 상태 유지 (기능적으로 문제 없음)
2. **event_products_3d_scene.js**: 현재 상태 유지

---

**점검 완료**: 2025-01-XX  
**다음 점검 예정**: 리팩토링 완료 후

