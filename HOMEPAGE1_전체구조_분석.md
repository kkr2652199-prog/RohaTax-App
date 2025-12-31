# 📋 homepage1 전초기지 전체 구조 분석

> **목적**: homepage1의 모든 페이지, 구조, 기능을 100% 습득하여 배포 서버와 동기화

---

## 🏗️ 1. 프로젝트 구조 개요

```
homepage1/
├── app.py                    # 메인 Flask 애플리케이션
├── config/                   # 설정 파일
│   └── settings.py          # 환경 설정
├── core/                    # 핵심 기능 모듈 (130개 파일)
├── routes/                   # 라우트/페이지 정의 (52개 파일)
├── templates/                # HTML 템플릿 (67개 파일)
├── static/                   # 정적 파일 (154개 파일)
├── database/                 # 데이터베이스 관련
│   ├── schema.sql           # 데이터베이스 스키마
│   └── migrations/          # 마이그레이션 파일
└── kweon21/                  # AI 블로그 스튜디오 (React)
```

---

## 🗺️ 2. 주요 라우트/페이지 목록

### 2.1 메인 페이지
- **`/`** - 홈페이지 (homepage.html)
- **`/new`** - 신규 디자인 실험용 (homepage_new.html)
- **`/terms`** - 서비스 이용약관
- **`/privacy`** - 개인정보 처리방침
- **`/api/test`** - API 테스트 엔드포인트

### 2.2 인증 관련 (home_modules)
- **`/login`** - 로그인 (auth_bp)
- **`/register`** - 회원가입 (registration_bp)
- **`/profile`** - 프로필 관리 (profile_bp)
- **`/password`** - 비밀번호 변경 (password_bp)
- **`/email`** - 이메일 인증 (email_bp)

### 2.3 변환 기능 (conversion_modules)
- **`/conversion`** - 변환 메인 페이지 (conversion_engine_bp)
- **`/conversion/convert`** - 파일 변환 처리
- **`/conversion/guideline`** - 변환 가이드라인 (guideline_bp)
- **`/conversion/page`** - 변환 페이지 관리 (page_bp)
- **`/conversion/security`** - 보안 설정 (security_bp)
- **`/conversion/token`** - 토큰 관리 (token_bp)
- **`/conversion/user`** - 사용자 관리 (user_bp)
- **`/conversion/gold`** - 골드 고객 관리 (gold_customers_bp)

### 2.4 관리자 (admin)
- **`/admin`** - 관리자 대시보드 (admin_bp)
- **`/admin/users`** - 사용자 관리
- **`/admin/payments`** - 결제 관리
- **`/admin/products`** - 상품 관리
- **`/admin/tax`** - 세금계산서 관리 (admin_tax_bp)
- **`/admin/activity`** - 활동 로그 (activity_log_bp)
- **`/admin/studio`** - 가구 디자인 스튜디오

### 2.5 결제/상점 (payment_routes)
- **`/shop`** - 상점 페이지 (shop.html)
- **`/showroom`** - 쇼룸 페이지 (showroom.html)
- **`/payment`** - 결제 처리
- **`/payment/complete`** - 결제 완료

### 2.6 비즈니스 라운지 (biz_lounge_routes)
- **`/biz-lounge`** - 소상공인 대출상품 (index.html)

### 2.7 AI 블로그 스튜디오 (playground_routes)
- **`/studio`** - AI 블로그 스튜디오 메인 (kweon21_bp)
- **`/studio/app`** - React 앱
- **`/studio/api`** - Studio API (studio_api_bp)
- **`/playground`** - 블로그 연구소 대시보드 (playground_bp)

### 2.8 API 엔드포인트
- **`/api/user`** - 사용자 API (user_api_bp)
- **`/api/user/v2`** - 사용자 API V2 (user_api_v2_bp)
- **`/api/admin`** - 관리자 API (admin_api_bp)
- **`/api/order`** - 주문 API (order_bp)
- **`/api/payment/complete`** - 결제 완료 API (payment_complete_bp)

### 2.9 운영 (ops)
- **`/ops`** - 운영 관리 (ops_bp)

---

## 📄 3. 주요 템플릿 파일 목록

### 3.1 메인 페이지
- `homepage.html` - 메인 랜딩 페이지
- `homepage_new.html` - 신규 디자인
- `base.html` - 기본 레이아웃

### 3.2 인증
- `login.html` - 로그인
- `register.html` - 회원가입
- `profile_edit.html` - 프로필 수정
- `profile_modern.html` - 프로필 (모던)
- `profile_v2.html` - 프로필 V2
- `forgot_password.html` - 비밀번호 찾기
- `reset_password.html` - 비밀번호 재설정
- `email_verification_pending.html` - 이메일 인증 대기

### 3.3 관리자
- `admin.html` - 관리자 대시보드
- `admin_dashboard.html` - 관리자 대시보드 (대체)
- `admin/furniture_studio.html` - 가구 디자인 스튜디오
- `admin/tabs/product_management.html` - 상품 관리
- `admin/tabs/payment_management.html` - 결제 관리
- `admin/tabs/tax_report.html` - 세금계산서 리포트
- `admin/tabs/activity_log.html` - 활동 로그

### 3.4 결제/상점
- `payment/shop.html` - 상점
- `payment/showroom.html` - 쇼룸

### 3.5 변환
- `conversion.html` - 변환 페이지

### 3.6 비즈니스 라운지
- `biz_lounge/index.html` - 소상공인 대출상품

### 3.7 Playground
- `playground/index.html` - 블로그 연구소
- `playground/base_playground.html` - Playground 기본
- `studio/studio_overlay.html` - Studio 오버레이

### 3.8 컴포넌트
- `partials/header.html` - 헤더
- `components/myhome_header.html` - 마이홈 헤더
- `components/myhome_tabs.html` - 마이홈 탭
- `components/token_history_table.html` - 토큰 이력 테이블
- `components/video_player.html` - 비디오 플레이어
- `components/chatbot_widget.html` - 챗봇 위젯

### 3.9 에러 페이지
- `errors/404.html` - 404 에러
- `errors/500.html` - 500 에러
- `errors/429.html` - Rate Limit 에러
- `maintenance.html` - 점검 모드

---

## 🗄️ 4. 데이터베이스 구조

### 4.1 주요 테이블
1. **users** - 사용자 정보
2. **payment_history** - 결제 내역
3. **token_history** - 토큰 이력
4. **product_packages** - 상품 패키지
5. **subscription_plans** - 구독 플랜
6. **activity_logs** - 활동 로그
7. **conversion_logs** - 변환 로그
8. **usage_logs** - 사용 로그
9. **gold_customers** - 골드 고객
10. **user_subscriptions** - 사용자 구독
11. **password_reset_tokens** - 비밀번호 재설정 토큰
12. **sms_verification_codes** - SMS 인증 코드
13. **validation_logs** - 검증 로그
14. **policies** - 정책
15. **settings** - 설정

### 4.2 마이그레이션 파일
- `001_create_activity_logs.sql`
- `002_create_payment_history.sql`
- `003_create_product_packages.sql`
- `004_add_previous_plan_type.sql` (previous_plan_type 컬럼 추가)
- `005_add_source_type_to_token_history.sql` (source_type 컬럼 추가)

---

## ⚙️ 5. 핵심 기능 모듈 (core/)

### 5.1 데이터베이스
- `core/db.py` - 데이터베이스 연결 및 초기화
- `core/change_detector.py` - 변경 감지
- `core/version_manager.py` - 버전 관리

### 5.2 보안
- `core/security.py` - 보안 기능 (CSRF 등)
- `core/security_enhancement.py` - 보안 강화 미들웨어

### 5.3 파일 처리
- `core/file_manager.py` - 파일 관리
- `core/file_parser.py` - 파일 파싱
- `core/file_size_monitor.py` - 파일 크기 모니터링

### 5.4 이메일
- `core/email_sender.py` - 이메일 발송

### 5.5 기타
- `core/extensions.py` - Flask 확장 (Rate Limiter)
- `core/content_loader.py` - 콘텐츠 로더
- `core/logging_setup.py` - 로깅 설정

---

## 🔧 6. 설정 파일

### 6.1 config/settings.py
- **PORT**: 기본 포트 (5001 - homepage1 전용)
- **HOST**: 기본 호스트 (127.0.0.1)
- **DEBUG**: 디버그 모드
- **SECRET_KEY**: 세션 암호화 키
- **DATABASE_URL**: 데이터베이스 연결 문자열
- **MAX_FILE_SIZE**: 최대 파일 크기
- **UPLOAD_FOLDER**: 업로드 폴더
- **OUTPUT_FOLDER**: 출력 폴더

### 6.2 환경 변수 (.env)
- `FLASK_RUN_HOST` - Flask 호스트 (0.0.0.0 또는 127.0.0.1)
- `FLASK_RUN_PORT` - Flask 포트 (5001 또는 5000)
- `FLASK_ENV` - Flask 환경 (development/production)
- `SECRET_KEY` - 시크릿 키
- `DATABASE_URL` - 데이터베이스 URL

---

## 📦 7. 블루프린트 등록 순서

```python
# 1. 홈 관련
- home_bp
- home_api_bp
- auth_bp
- registration_bp
- profile_bp
- password_bp
- email_bp

# 2. 변환 관련
- conversion_engine_bp
- guideline_bp
- page_bp
- security_bp
- token_bp
- user_bp
- gold_customers_bp

# 3. 관리자 관련
- admin_bp
- activity_log_bp
- admin_tax_bp
- admin_api_bp

# 4. API 관련
- user_api_bp
- user_api_v2_bp
- order_bp
- payment_complete_bp

# 5. 결제/상점
- payment_bp

# 6. 비즈니스 라운지
- biz_lounge_bp

# 7. Playground
- kweon21_bp
- studio_api_bp
- playground_bp

# 8. 운영
- ops_bp
```

---

## 🎯 8. 주요 기능 목록

### 8.1 사용자 관리
- 회원가입/로그인
- 프로필 관리
- 비밀번호 변경
- 이메일 인증
- SMS 인증

### 8.2 변환 기능
- 엑셀 → 세금계산서 변환
- 변환 가이드라인 관리
- 변환 이력 관리
- 토큰 기반 사용량 관리

### 8.3 결제/상점
- 상품 관리
- 결제 처리
- 주문 관리
- 쇼룸 (3D 체험)

### 8.4 관리자
- 사용자 관리
- 결제 관리
- 상품 관리
- 세금계산서 리포트
- 활동 로그
- 통계 대시보드

### 8.5 AI 블로그 스튜디오
- 블로그 작성
- AI 기반 콘텐츠 생성
- 카테고리별 주제 추천

### 8.6 비즈니스 라운지
- 소상공인 대출상품 정보

---

## 🔍 9. 다음 단계

이제 homepage1의 구조를 100% 습득했으므로:

1. ✅ **구조 파악 완료** - 모든 페이지, 라우트, 기능 확인
2. ⏳ **배포 서버 비교** - 배포 서버와 차이점 확인
3. ⏳ **동기화 작업** - homepage1 → 배포 서버 동기화

---

## 📝 참고사항

- **포트**: homepage1은 5001, 배포 서버는 5000
- **환경**: homepage1은 개발용, 배포 서버는 프로덕션
- **데이터베이스**: 동일한 스키마 사용
- **코드**: homepage1과 배포 서버는 쌍둥이 구조

