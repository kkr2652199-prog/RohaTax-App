# 🚨 상용화 전 '숨겨진 위험(Risk)' 정밀 탐색 보고서

> **작성일**: 2025-12-19  
> **목적**: 상용 서비스로서의 안정성과 법적/물리적 준비 상태 검증

---

## 📊 검증 결과 요약

| 항목 | 상태 | 위험도 | 비고 |
|------|------|--------|------|
| **1. Rate Limiting** | ❌ **미구현 (Risk)** | 🔴 **높음** | 무차별 공격에 무방비 |
| **2. File Cleanup** | ⚠️ **부분 구현** | 🟡 **중간** | 스케줄러 미등록 |
| **3. Legal Pages** | ⚠️ **부분 구현** | 🟡 **낮음** | 약관 내용 하드코딩 |
| **4. SMTP 설정** | ⚠️ **설정만 존재** | 🟡 **중간** | 실제 발송 미구현 |

---

## 1. 공격 방어 (Rate Limiting) ❌ **미구현 (Risk)**

### 현재 상태
- ❌ `Flask-Limiter` 라이브러리 **미설치** (`requirements.txt`에 없음)
- ❌ 로그인 엔드포인트(`POST /login`)에 **Rate Limiting 없음**
- ❌ 파일 변환 엔드포인트(`POST /api/convert/start`)에 **Rate Limiting 없음**
- ⚠️ `studio_api.py`에 메모리 기반 Rate Limiting 존재 (하루 20회 제한)
  - 하지만 이는 특정 API(`/api/studio`)에만 적용됨
  - 로그인/변환 엔드포인트에는 적용되지 않음

### 발견된 코드
```python
# routes/home_modules/auth_routes.py
@auth_bp.route('/login', methods=['POST'])
def login_post():
    # Rate Limiting 코드 없음
    # 무제한 로그인 시도 가능
```

```python
# routes/conversion_modules/conversion_engine_routes.py
@conversion_engine_bp.route('/api/convert/start', methods=['POST'])
def start_conversion():
    # Rate Limiting 코드 없음
    # 무제한 변환 요청 가능
```

### 위험도: 🔴 **높음**
- **무차별 로그인 공격(Brute Force)**: 비밀번호 추측 공격에 무방비
- **DDoS 공격**: 변환 API에 무제한 요청 가능
- **서버 리소스 고갈**: 디스크/메모리 고갈 위험

### 권장 조치
1. `Flask-Limiter` 설치 및 설정
2. 로그인 엔드포인트: **1분에 5회 제한**
3. 변환 엔드포인트: **1분에 10회 제한** (사용자당)
4. Redis 기반 Rate Limiting (장기)

---

## 2. 파일 청소 (File Cleanup) ⚠️ **부분 구현**

### 현재 상태
- ✅ `FileManager` 클래스 존재 (`core/file_manager.py`)
- ✅ `auto_cleanup()` 메서드 구현됨
- ✅ 로그 파일 정리 로직 존재 (`core/logging_setup.py`)
- ❌ **APScheduler에 파일 정리 작업 미등록**
- ⚠️ `app.py`에서 `file_manager.auto_cleanup()` 호출은 있으나, **수동 실행**에 의존

### 발견된 코드
```python
# app.py (라인 87-88)
if file_manager.should_run_cleanup():
    file_manager.auto_cleanup()
```
- 이 코드는 앱 시작 시 1회만 실행됨
- 정기적인 스케줄러 작업으로 등록되지 않음

### APScheduler 현재 등록된 작업
```python
# app.py (라인 206-212)
scheduler.add_job(
    func=backup_database,
    trigger=CronTrigger(hour=4, minute=0),  # 매일 새벽 04:00
    id='daily_backup',
    name='일일 데이터베이스 백업',
    replace_existing=True
)
```
- **백업 작업만 등록됨**
- 파일 정리 작업은 없음

### 위험도: 🟡 **중간**
- **디스크 공간 고갈**: `uploads/`, `outputs/`, `user_data/` 디렉토리에 파일이 계속 쌓임
- **서버 다운**: 디스크가 꽉 차면 서버가 멈출 수 있음

### 권장 조치
1. APScheduler에 파일 정리 작업 등록
   - 매일 새벽 05:00에 실행
   - 30일 이상 된 임시 파일 자동 삭제
2. `uploads/`, `outputs/` 디렉토리 정리 로직 추가

---

## 3. 필수 페이지 실재 여부 (Legal Pages) ⚠️ **부분 구현**

### 현재 상태
- ✅ 라우트는 존재 (`app.py` 라인 548, 573)
- ✅ `legal.html` 템플릿 사용 (약관 내용은 하드코딩)
- ✅ 회원가입 페이지에 링크 존재 (`templates/register.html`)
- ⚠️ 약관 내용이 코드에 하드코딩되어 있음 (템플릿 파일 분리 권장)

### 발견된 코드
```python
# app.py (라인 548-570)
@app.route("/terms")
def terms():
    """서비스 이용약관 페이지"""
    terms_content = """
    <h3>제 1 조 (목적)</h3>
    ...
    """
    return render_template("legal.html", title="서비스 이용약관", content=terms_content)

@app.route("/privacy")
def privacy():
    """개인정보 처리방침 페이지"""
    privacy_content = """
    <h3>1. 수집하는 개인정보 항목</h3>
    ...
    """
    return render_template("legal.html", title="개인정보 처리방침", content=privacy_content)
```

### 위험도: 🟡 **중간** (낮음으로 조정)
- ✅ 페이지는 존재하고 작동함
- ⚠️ 약관 내용 관리가 불편함 (코드 수정 필요)
- ⚠️ 법무팀 검토 후 업데이트가 어려움

```html
<!-- templates/register.html -->
<a href="/terms" target="_blank" class="register-terms-link">약관 보기</a>
<a href="/privacy" target="_blank" class="register-terms-link">약관 보기</a>
```

### 위험도: 🔴 **높음**
- **법적 문제**: 이용약관/개인정보처리방침 없이는 상용 서비스 운영 불가
- **사용자 신뢰 저하**: 링크 클릭 시 404 에러 발생
- **규제 위반**: 개인정보보호법 위반 가능성

### 권장 조치
1. `templates/terms.html` 생성 (이용약관)
2. `templates/privacy.html` 생성 (개인정보처리방침)
3. 법무팀 검토 후 배포

---

## 4. 이메일 발송 설정 (SMTP) ⚠️ **설정만 존재**

### 현재 상태
- ✅ SMTP 설정 코드 존재 (`app.py` 라인 385-393)
- ✅ 비밀번호 재설정 이메일 함수 존재 (`core/email_sender.py`)
- ⚠️ **환경 변수 미설정 시 실제 발송 안 됨**
- ⚠️ 환경 변수가 없으면 콘솔에만 토큰 출력

### 발견된 코드
```python
# app.py (라인 385-393)
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
```

```python
# core/email_sender.py (라인 44-49)
mail_server = os.environ.get('MAIL_SERVER')
if not mail_server:
    logger.warning("이메일 서버 설정이 없습니다. 콘솔에 토큰을 출력합니다.")
    logger.info(f"비밀번호 재설정 토큰 - 사용자: {username}, 이메일: {email}, 토큰: {token}")
    return False
```

### 위험도: 🟡 **중간**
- **비밀번호 찾기 기능 미작동**: 사용자가 비밀번호를 잊어버리면 복구 불가
- **사용자 경험 저하**: 이메일 발송 실패 시 콘솔 로그만 남음

### 권장 조치
1. 프로덕션 환경 변수 설정:
   ```bash
   export MAIL_SERVER="smtp.gmail.com"
   export MAIL_USERNAME="your-email@gmail.com"
   export MAIL_PASSWORD="your-app-password"
   ```
2. Gmail App Password 또는 SendGrid/SES 등 SMTP 서비스 연동
3. 이메일 발송 실패 시 사용자에게 명확한 오류 메시지 표시

---

## 🎯 우선순위별 조치 사항

### 🔴 긴급 (상용화 전 필수)
1. **Rate Limiting 구현** (로그인/변환 API)
2. **법적 페이지 검토** (이용약관/개인정보처리방침 내용 법무팀 검토)

### 🟡 중요 (1주일 내)
3. **파일 정리 스케줄러 등록**
4. **SMTP 환경 변수 설정**

---

## 📝 결론

현재 상태로는 **상용 서비스 운영에 위험**이 있습니다.

**즉시 조치 필요:**
- Rate Limiting 미구현 → 무차별 공격에 취약
- 법적 페이지 내용 검토 → 법무팀 검토 후 최종 확정 필요

**단기 조치 필요:**
- 파일 정리 자동화 → 디스크 공간 고갈 방지
- SMTP 설정 → 비밀번호 찾기 기능 활성화

---

**작성일**: 2025-12-19  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

