# 📊 로하택스 메인 페이지 vs 변환 페이지 비교 분석

## 📋 개요

로하택스 서비스의 두 가지 주요 페이지를 비교 분석한 보고서입니다.

---

## 🏠 메인 페이지 (`/`)

### 기본 정보
- **URL**: `/`
- **라우트**: `app.py` → `homepage()` 함수
- **템플릿**: `templates/homepage.html`
- **접근 권한**: **공개 페이지** (로그인 불필요)

### 주요 특징

#### 1. 목적
- **랜딩 페이지 (Landing Page)**
- 서비스 소개 및 마케팅
- 신규 사용자 유치

#### 2. 기능
- ✅ 서비스 소개 (Hero 섹션)
- ✅ 통계 정보 표시
- ✅ 문제-해결책 소개
- ✅ 사용 사례 (Use Cases)
- ✅ 작동 방식 설명
- ✅ 기능 소개 (Features)
- ✅ 가격 정보 (Pricing)
- ✅ 회사 소개
- ✅ 고객 후기 (Testimonials)
- ✅ FAQ
- ✅ CTA (Call to Action)

#### 3. 데이터
- 상품 정보 (`_build_shop_context()`)
- 멤버십 정보 (무료 2종 + 유료 3종)
- 가격 정보
- 토큰 정보

#### 4. 사용자 인터랙션
- 회원가입 유도
- 무료 체험 신청
- 상품 구매 페이지로 이동
- 로그인 페이지로 이동

#### 5. 레이아웃
- **전체 화면 레이아웃**
- 섹션별 스크롤
- 헤더 + 푸터 포함
- 반응형 디자인

#### 6. JavaScript
- `homepage.js` - 페이지 인터랙션
- `video_player.js` - 비디오 재생
- `testimonials.js` - 후기 슬라이더
- Lucide Icons

---

## 🔄 변환 페이지 (`/conversion`)

### 기본 정보
- **URL**: `/conversion`
- **라우트**: `routes/conversion_modules/main_routes.py` → `conversion()` 함수
- **템플릿**: `templates/conversion.html`
- **접근 권한**: **회원 전용** (로그인 필수)

### 주요 특징

#### 1. 목적
- **워크스페이스 (Workspace)**
- 실제 서비스 사용
- 파일 변환 작업 수행

#### 2. 기능
- ✅ 파일 업로드
- ✅ 엑셀 → 전자세금계산서 변환
- ✅ 토큰 관리 (지급/사용/잔액)
- ✅ 사용자 정보 조회
- ✅ 변환 이력 확인
- ✅ 다운로드 기능

#### 3. 데이터
- 사용자 토큰 정보 (`token_status`)
- 사용자 프로필 정보
- 변환 이력
- 파일 업로드/다운로드

#### 4. 사용자 인터랙션
- 파일 드래그 앤 드롭
- 변환 시작 버튼
- 토큰 상태 확인
- 사용자 정보 조회
- 변환 결과 다운로드

#### 5. 레이아웃
- **사이드바 + 메인 콘텐츠 레이아웃**
- 사이드바: 토큰 상태, 사용자 정보
- 메인: 파일 업로드 영역, 변환 결과
- 고정 헤더 없음 (base.html 상속)

#### 6. JavaScript
- `conversion.js` - 변환 로직
- `token_alert_modal.js` - 토큰 알림 모달
- API 호출: `/api/user-info`, `/api/v2/user/token-summary`

---

## 🔍 주요 차이점 비교표

| 항목 | 메인 페이지 (`/`) | 변환 페이지 (`/conversion`) |
|------|------------------|---------------------------|
| **접근 권한** | 공개 (로그인 불필요) | 회원 전용 (로그인 필수) |
| **목적** | 마케팅/랜딩 | 실제 서비스 사용 |
| **템플릿 구조** | 독립 템플릿 | base.html 상속 |
| **레이아웃** | 전체 화면 스크롤 | 사이드바 + 메인 콘텐츠 |
| **헤더/푸터** | 포함 | 헤더만 (base.html) |
| **주요 기능** | 정보 제공 | 파일 변환 작업 |
| **데이터 소스** | 상품 정보 | 사용자 토큰/프로필 |
| **JavaScript** | 인터랙션/애니메이션 | API 호출/변환 로직 |
| **사용자 상태** | 불필요 | 필수 (세션) |
| **토큰 정보** | 표시만 (가격 정보) | 실제 사용 (잔액 확인) |
| **API 호출** | 없음 | `/api/user-info`, `/api/v2/user/token-summary` |

---

## 🔐 인증 및 보안

### 메인 페이지
- ❌ 로그인 불필요
- ❌ 세션 확인 없음
- ✅ 공개 접근 가능
- ✅ SEO 최적화 (메타 태그)

### 변환 페이지
- ✅ 로그인 필수
- ✅ 세션 확인 (`session.get('user_id')`)
- ✅ 미로그인 시 리다이렉트 (`/registration/register`)
- ✅ 토큰 상태 확인
- ✅ Guest 모드 지원 (제한적 접근)

---

## 📱 사용자 경험 (UX)

### 메인 페이지
1. **첫 방문자**
   - 서비스 소개 확인
   - 가격 정보 확인
   - 회원가입 유도

2. **기존 사용자**
   - 로그인 후 변환 페이지로 이동
   - 상품 구매 페이지로 이동

### 변환 페이지
1. **로그인 사용자**
   - 파일 업로드
   - 변환 작업 수행
   - 토큰 사용

2. **비로그인 사용자**
   - Guest 모드 오버레이 표시
   - 로그인/회원가입 유도

---

## 🎨 디자인 차이

### 메인 페이지
- **마케팅 중심 디자인**
- 밝은 색상, 그라데이션
- 애니메이션 효과
- 카드 기반 레이아웃
- 섹션별 구분

### 변환 페이지
- **기능 중심 디자인**
- 다크 테마 (사이드바)
- 미니멀한 UI
- 실용적인 버튼/폼
- 작업 영역 중심

---

## 🔧 기술적 차이

### 메인 페이지
```python
# app.py
@app.route("/")
def homepage():
    context = _build_shop_context()  # 상품 정보
    return render_template("homepage.html", **context)
```

**특징:**
- 단순 렌더링
- 정적 데이터 표시
- API 호출 없음

### 변환 페이지
```python
# routes/conversion_modules/main_routes.py
@main_bp.route('/conversion')
def conversion():
    if not session.get('user_id'):  # 로그인 확인
        return redirect(url_for('registration.register'))
    
    token_status = get_token_status_from_user_table(session['user_id'])
    return render_template('conversion.html', 
                         available_tokens=available_tokens,
                         total_tokens=token_status['token_balance'],
                         used_tokens=token_status['tokens_used'])
```

**특징:**
- 세션 기반 인증
- 동적 데이터 로딩
- API 호출 필요

---

## 📊 데이터 흐름

### 메인 페이지
```
사용자 → 메인 페이지 → 상품 정보 표시 (정적)
```

### 변환 페이지
```
사용자 → 로그인 확인 → 세션 확인 → 토큰 정보 조회 → 
API 호출 (/api/user-info) → 사용자 정보 표시
```

---

## ⚠️ 발견된 문제점

### 변환 페이지 유저 정보 불러오기 문제
- **문제**: `/api/user-info` 엔드포인트에서 유저 정보를 불러오지 못함
- **원인**: `user_routes.py`의 import 경로 오류
- **해결**: `from ..utils.auth` → `from routes.utils.auth`로 수정 완료

---

## ✅ 권장사항

### 메인 페이지
1. SEO 최적화 유지
2. 로딩 속도 최적화
3. 모바일 반응형 개선

### 변환 페이지
1. API 오류 처리 강화
2. 로딩 상태 표시 개선
3. 오프라인 모드 지원 고려

---

## 📝 결론

**메인 페이지**는 **마케팅/랜딩** 목적의 공개 페이지이고,  
**변환 페이지**는 **실제 서비스 사용**을 위한 회원 전용 워크스페이스입니다.

두 페이지는 서로 다른 목적과 사용자 경험을 제공하며,  
메인 페이지에서 변환 페이지로 자연스럽게 이어지는 사용자 여정을 구성하고 있습니다.

---

**작성일**: 2025-12-19  
**분석 대상**: homepage1 워크트리



