# 🔐 소셜 로그인 구현 가이드

> **목적**: 구글, 네이버, 카카오 소셜 로그인 기능 추가  
> **현재 상태**: 기본 회원가입/로그인만 있음, 소셜 로그인 없음

---

## 📊 현재 상태 분석

### ✅ 현재 구현된 기능

1. **기본 회원가입** ✅
   - 위치: `routes/home_modules/registration_routes.py`
   - 기능: 아이디, 비밀번호, 사업자 정보 입력
   - 상태: 완벽하게 구현됨

2. **기본 로그인** ✅
   - 위치: `routes/home_modules/auth_routes.py`
   - 기능: 아이디/비밀번호 로그인
   - 상태: 완벽하게 구현됨

3. **세션 관리** ✅
   - 세션 기반 인증
   - 세션 보안 설정 완료

### ❌ 현재 없는 기능

1. **소셜 로그인** ❌
   - 구글 로그인 없음
   - 네이버 로그인 없음
   - 카카오 로그인 없음

2. **OAuth 관련 데이터베이스 컬럼** ❌
   - `oauth_provider` 컬럼 없음
   - `social_id` 컬럼 없음

---

## 🎯 소셜 로그인 구현 계획

### 구현 가능 여부

**답변: ✅ 완전히 가능합니다!**

**이유:**
1. 현재 회원가입/로그인 시스템이 잘 구현되어 있음
2. Flask는 OAuth 라이브러리 지원이 우수함
3. 구글/네이버/카카오 모두 OAuth 2.0 제공

### 개발 시기 결정

**질문: 지금 만들어야 하는가?**

**답변: 🟡 선택사항입니다. 다음을 고려하세요:**

#### 지금 개발해야 하는 경우:
- ✅ 사용자 편의성 우선 (회원가입 절차 간소화)
- ✅ 빠른 사용자 유입 필요
- ✅ 모바일 사용자 많음

#### 나중에 개발해도 되는 경우:
- ✅ 현재 회원가입 절차가 문제없이 작동
- ✅ B2B 서비스 (사업자 정보 필수)
- ✅ 초기 사용자 규모 작음

**권장**: **초기에는 기본 회원가입만으로 시작, 사용자 피드백 후 소셜 로그인 추가**

---

## 📋 구현 단계

### 1단계: 데이터베이스 스키마 수정

**마이그레이션 파일 생성:**

```sql
-- database/migrations/add_social_login.sql
ALTER TABLE users ADD COLUMN oauth_provider TEXT;  -- 'google', 'naver', 'kakao', NULL
ALTER TABLE users ADD COLUMN social_id TEXT;       -- 소셜 플랫폼의 사용자 ID
ALTER TABLE users ADD COLUMN social_email TEXT;    -- 소셜 플랫폼의 이메일

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_users_social ON users(oauth_provider, social_id);
```

**실행 방법:**
```bash
# SQLite에서 직접 실행
sqlite3 database/app.db < database/migrations/add_social_login.sql
```

---

### 2단계: 필요한 패키지 설치

```bash
pip install flask-oauthlib  # 또는
pip install authlib  # 더 최신 라이브러리 (권장)
```

**requirements.txt에 추가:**
```
authlib==1.2.1
requests==2.32.5
```

---

### 3단계: OAuth 설정 파일 생성

**`core/oauth_config.py` 생성:**

```python
"""
소셜 로그인 OAuth 설정
"""
import os
from typing import Dict, Any

# 환경 변수에서 OAuth 클라이언트 정보 가져오기
def get_oauth_config() -> Dict[str, Any]:
    return {
        'google': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://accounts.google.com/o/oauth2/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scope': 'openid email profile'
        },
        'naver': {
            'client_id': os.getenv('NAVER_CLIENT_ID', ''),
            'client_secret': os.getenv('NAVER_CLIENT_SECRET', ''),
            'authorize_url': 'https://nid.naver.com/oauth2.0/authorize',
            'token_url': 'https://nid.naver.com/oauth2.0/token',
            'userinfo_url': 'https://openapi.naver.com/v1/nid/me',
            'scope': ''
        },
        'kakao': {
            'client_id': os.getenv('KAKAO_CLIENT_ID', ''),
            'client_secret': os.getenv('KAKAO_CLIENT_SECRET', ''),
            'authorize_url': 'https://kauth.kakao.com/oauth/authorize',
            'token_url': 'https://kauth.kakao.com/oauth/token',
            'userinfo_url': 'https://kapi.kakao.com/v2/user/me',
            'scope': 'profile_nickname account_email'
        }
    }
```

---

### 4단계: 소셜 로그인 라우트 생성

**`routes/home_modules/social_auth_routes.py` 생성:**

```python
"""
소셜 로그인 라우트
- 구글, 네이버, 카카오 로그인 지원
"""
from flask import Blueprint, redirect, url_for, session, request, flash
from authlib.integrations.flask_client import OAuth
import sqlite3
import logging
from core.db import get_conn_optimized as get_conn
from core.oauth_config import get_oauth_config

logger = logging.getLogger(__name__)
social_auth_bp = Blueprint('social_auth', __name__, url_prefix='/auth')

# OAuth 클라이언트 초기화 (app.py에서 설정)
oauth = OAuth()

def init_oauth(app):
    """OAuth 클라이언트 초기화"""
    oauth.init_app(app)
    config = get_oauth_config()
    
    # 구글
    if config['google']['client_id']:
        oauth.register(
            name='google',
            client_id=config['google']['client_id'],
            client_secret=config['google']['client_secret'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    
    # 네이버
    if config['naver']['client_id']:
        oauth.register(
            name='naver',
            client_id=config['naver']['client_id'],
            client_secret=config['naver']['client_secret'],
            authorize_url=config['naver']['authorize_url'],
            authorize_params=None,
            access_token_url=config['naver']['token_url'],
            access_token_params=None,
            refresh_token_url=None,
            redirect_uri=url_for('social_auth.naver_callback', _external=True),
            client_kwargs={'scope': ''}
        )
    
    # 카카오
    if config['kakao']['client_id']:
        oauth.register(
            name='kakao',
            client_id=config['kakao']['client_id'],
            client_secret=config['kakao']['client_secret'],
            authorize_url=config['kakao']['authorize_url'],
            authorize_params=None,
            access_token_url=config['kakao']['token_url'],
            access_token_params=None,
            refresh_token_url=None,
            redirect_uri=url_for('social_auth.kakao_callback', _external=True),
            client_kwargs={'scope': 'profile_nickname account_email'}
        )


@social_auth_bp.route('/google')
def google_login():
    """구글 로그인 시작"""
    redirect_uri = url_for('social_auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@social_auth_bp.route('/google/callback')
def google_callback():
    """구글 로그인 콜백"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        
        # 구글 사용자 정보 추출
        social_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        return handle_social_login('google', social_id, email, name)
    except Exception as e:
        logger.error(f"구글 로그인 오류: {e}")
        flash('구글 로그인에 실패했습니다.', 'error')
        return redirect(url_for('auth.login'))


@social_auth_bp.route('/naver')
def naver_login():
    """네이버 로그인 시작"""
    redirect_uri = url_for('social_auth.naver_callback', _external=True)
    return oauth.naver.authorize_redirect(redirect_uri)


@social_auth_bp.route('/naver/callback')
def naver_callback():
    """네이버 로그인 콜백"""
    try:
        token = oauth.naver.authorize_access_token()
        resp = oauth.naver.get('https://openapi.naver.com/v1/nid/me', token=token)
        user_info = resp.json()
        
        # 네이버 사용자 정보 추출
        naver_data = user_info.get('response', {})
        social_id = naver_data.get('id')
        email = naver_data.get('email', '')
        name = naver_data.get('name', '')
        
        return handle_social_login('naver', social_id, email, name)
    except Exception as e:
        logger.error(f"네이버 로그인 오류: {e}")
        flash('네이버 로그인에 실패했습니다.', 'error')
        return redirect(url_for('auth.login'))


@social_auth_bp.route('/kakao')
def kakao_login():
    """카카오 로그인 시작"""
    redirect_uri = url_for('social_auth.kakao_callback', _external=True)
    return oauth.kakao.authorize_redirect(redirect_uri)


@social_auth_bp.route('/kakao/callback')
def kakao_callback():
    """카카오 로그인 콜백"""
    try:
        token = oauth.kakao.authorize_access_token()
        resp = oauth.kakao.get('https://kapi.kakao.com/v2/user/me', token=token)
        user_info = resp.json()
        
        # 카카오 사용자 정보 추출
        kakao_account = user_info.get('kakao_account', {})
        social_id = str(user_info.get('id'))
        email = kakao_account.get('email', '')
        name = kakao_account.get('profile', {}).get('nickname', '')
        
        return handle_social_login('kakao', social_id, email, name)
    except Exception as e:
        logger.error(f"카카오 로그인 오류: {e}")
        flash('카카오 로그인에 실패했습니다.', 'error')
        return redirect(url_for('auth.login'))


def handle_social_login(provider: str, social_id: str, email: str, name: str):
    """
    소셜 로그인 처리 공통 함수
    - 기존 계정이 있으면 로그인
    - 없으면 회원가입 페이지로 리다이렉트 (추가 정보 입력)
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 소셜 ID로 기존 계정 찾기
        user = conn.execute(
            """
            SELECT id, username, is_admin, is_active, approval_status
            FROM users
            WHERE oauth_provider = ? AND social_id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (provider, social_id)
        ).fetchone()
        
        if user:
            # 기존 계정 로그인
            if not user['is_active']:
                flash('비활성화된 계정입니다.', 'error')
                return redirect(url_for('auth.login'))
            
            if user['approval_status'] != 'approved':
                flash('승인 대기 중인 계정입니다.', 'error')
                return redirect(url_for('auth.login'))
            
            # 세션 설정
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = int(user['is_admin'] or 0)
            session.permanent = True
            
            flash('로그인 성공', 'success')
            return redirect(url_for('home.home'))
        else:
            # 신규 회원가입 - 추가 정보 입력 필요
            # 소셜 정보를 세션에 임시 저장
            session['social_signup'] = {
                'provider': provider,
                'social_id': social_id,
                'email': email,
                'name': name
            }
            
            # 사업자 정보 입력 페이지로 리다이렉트
            flash('소셜 로그인 성공! 추가 정보를 입력해주세요.', 'info')
            return redirect(url_for('registration.social_register'))


# app.py에 등록 필요
# from routes.home_modules.social_auth_routes import social_auth_bp, init_oauth
# init_oauth(app)
# app.register_blueprint(social_auth_bp)
```

---

### 5단계: 소셜 회원가입 페이지 생성

**`routes/home_modules/registration_routes.py`에 추가:**

```python
@registration_bp.route('/register/social')
def social_register():
    """소셜 로그인 후 추가 정보 입력"""
    if 'social_signup' not in session:
        flash('소셜 로그인을 먼저 진행해주세요.', 'error')
        return redirect(url_for('auth.login'))
    
    social_info = session['social_signup']
    return render_template('register_social.html', social_info=social_info)


@registration_bp.route('/register/social', methods=['POST'])
def social_register_post():
    """소셜 회원가입 처리"""
    if 'social_signup' not in session:
        flash('소셜 로그인을 먼저 진행해주세요.', 'error')
        return redirect(url_for('auth.login'))
    
    social_info = session['social_signup']
    
    # 사업자 정보 입력받기
    username = request.form.get('username')
    business_number = request.form.get('business_number')
    representative_name = request.form.get('representative_name')
    company_name = request.form.get('company_name')
    phone = request.form.get('phone')
    address = request.form.get('address', '')
    business_type = request.form.get('business_type', '')
    business_category = request.form.get('business_category', '')
    
    # 검증 로직 (기존과 동일)
    # ... 검증 코드 ...
    
    # 사용자 생성 (소셜 정보 포함)
    with get_conn() as conn:
        try:
            conn.execute(
                """
                INSERT INTO users (
                    username, email, password, company_name, business_number,
                    representative_name, phone, address, business_type, business_category,
                    oauth_provider, social_id, social_email, approval_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    social_info['email'],
                    None,  # 소셜 로그인은 비밀번호 없음
                    company_name,
                    business_number,
                    representative_name,
                    phone,
                    address,
                    business_type,
                    business_category,
                    social_info['provider'],
                    social_info['social_id'],
                    social_info['email'],
                    'approved'  # 소셜 로그인은 자동 승인
                )
            )
            conn.commit()
            
            # 세션 정리
            session.pop('social_signup', None)
            
            flash('회원가입이 완료되었습니다.', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash('이미 사용 중인 정보입니다.', 'error')
            return redirect(url_for('registration.social_register'))
```

---

### 6단계: 로그인 페이지에 소셜 로그인 버튼 추가

**`templates/login.html` 수정:**

```html
<!-- 기존 로그인 폼 아래에 추가 -->
<div class="social-login">
    <h3>소셜 로그인</h3>
    <a href="{{ url_for('social_auth.google_login') }}" class="btn-social google">
        구글로 로그인
    </a>
    <a href="{{ url_for('social_auth.naver_login') }}" class="btn-social naver">
        네이버로 로그인
    </a>
    <a href="{{ url_for('social_auth.kakao_login') }}" class="btn-social kakao">
        카카오로 로그인
    </a>
</div>
```

---

## 🔑 OAuth 클라이언트 등록 방법

### 1. 구글 OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성
3. "API 및 서비스" → "사용자 인증 정보" → "OAuth 클라이언트 ID 만들기"
4. 승인된 리디렉션 URI 추가:
   ```
   https://your-domain.com/auth/google/callback
   ```
5. Client ID와 Client Secret 복사

### 2. 네이버 OAuth 설정

1. [네이버 개발자 센터](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. 서비스 URL 및 Callback URL 설정:
   ```
   Callback URL: https://your-domain.com/auth/naver/callback
   ```
4. Client ID와 Client Secret 복사

### 3. 카카오 OAuth 설정

1. [카카오 개발자 센터](https://developers.kakao.com/) 접속
2. 애플리케이션 등록
3. 플랫폼 설정 (웹 플랫폼 추가)
4. Redirect URI 설정:
   ```
   https://your-domain.com/auth/kakao/callback
   ```
5. 동의 항목 설정 (이메일, 닉네임 등)
6. REST API 키와 Client Secret 복사

---

## 📝 환경 변수 설정

**.env 파일에 추가:**

```bash
# 구글 OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# 네이버 OAuth
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

# 카카오 OAuth
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret
```

---

## ✅ 구현 체크리스트

### 데이터베이스
- [ ] `oauth_provider` 컬럼 추가
- [ ] `social_id` 컬럼 추가
- [ ] `social_email` 컬럼 추가
- [ ] 인덱스 생성

### 코드
- [ ] `authlib` 패키지 설치
- [ ] `core/oauth_config.py` 생성
- [ ] `routes/home_modules/social_auth_routes.py` 생성
- [ ] `app.py`에 OAuth 초기화 및 Blueprint 등록
- [ ] 소셜 회원가입 페이지 생성
- [ ] 로그인 페이지에 소셜 로그인 버튼 추가

### OAuth 설정
- [ ] 구글 OAuth 클라이언트 등록
- [ ] 네이버 OAuth 클라이언트 등록
- [ ] 카카오 OAuth 클라이언트 등록
- [ ] 환경 변수 설정

### 테스트
- [ ] 구글 로그인 테스트
- [ ] 네이버 로그인 테스트
- [ ] 카카오 로그인 테스트
- [ ] 기존 계정과 연동 테스트

---

## 🎯 개발 시기 권장사항

### 지금 개발해야 하는 경우:
- ✅ 사용자 편의성 최우선
- ✅ 빠른 사용자 유입 필요
- ✅ 모바일 사용자 비중 높음
- ✅ 경쟁 서비스에 소셜 로그인 있음

### 나중에 개발해도 되는 경우:
- ✅ 현재 회원가입 절차가 문제없음
- ✅ B2B 서비스 (사업자 정보 필수)
- ✅ 초기 사용자 규모 작음
- ✅ 개발 리소스 제한

**권장**: **초기에는 기본 회원가입만으로 시작, 사용자 100명 이상 또는 피드백 수집 후 소셜 로그인 추가**

---

## 💰 비용

**소셜 로그인 자체는 무료입니다!**

- 구글 OAuth: 무료
- 네이버 OAuth: 무료
- 카카오 OAuth: 무료

**추가 비용 없음**

---

## ⏱️ 예상 개발 시간

- **데이터베이스 마이그레이션**: 30분
- **OAuth 설정 및 코드 작성**: 4-6시간
- **테스트 및 디버깅**: 2-3시간
- **OAuth 클라이언트 등록**: 1-2시간

**총 예상 시간**: **8-12시간** (하루 작업)

---

## 🎯 결론

### 질문에 대한 답변

**Q1: 회원가입 로직을 인터넷 서버에 저장하고 구글/네이버/카카오로 회원가입이 가능한가?**
**A: ✅ 네, 완전히 가능합니다!**

**Q2: 지금 개발해야 하는가?**
**A: 🟡 선택사항입니다. 초기에는 기본 회원가입만으로 시작하고, 사용자 피드백 후 추가하는 것을 권장합니다.**

**이유:**
- 현재 회원가입 시스템이 잘 작동함
- B2B 서비스 특성상 사업자 정보 입력이 필수
- 소셜 로그인 후에도 추가 정보 입력 필요
- 개발 리소스를 다른 우선순위 기능에 투자 가능

**하지만 소셜 로그인을 추가하면:**
- ✅ 사용자 편의성 향상
- ✅ 회원가입 전환율 증가
- ✅ 모바일 사용자 경험 개선

---

**작성일**: 2025-01-18  
**작성자**: Auto (Cursor AI Assistant)  
**프로젝트**: RohaTax homepage1

