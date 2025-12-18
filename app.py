import os

from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
# override=True: 환경 변수가 .env 파일보다 우선순위를 갖도록 함
load_dotenv(override=True)

import mimetypes
import os
import time
from datetime import datetime

import psutil
from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from config.settings import settings
from core.change_detector import change_detector
from core.content_loader import CONTENT_CACHE, get_text
from core.db import get_conn, init_db, seed_demo
from core.email_sender import init_mail
from core.file_manager import FileManager
from core.file_size_monitor import file_size_monitor
from core.logging_setup import init_logging
from core.security import generate_csrf_token, validate_csrf_token
from core.version_manager import version_manager


# 자동 파일 정리 시스템 초기화
def init_file_management():
    """파일 관리 시스템 초기화"""
    try:
        file_manager = FileManager(".")

        # 즉시 삭제할 파일들
        immediate_delete_files = [
            "check_system.py",
            "analyze_db.py",
            "app_content.py",
            "test_*.py",  # 루트에 있는 테스트 파일들
            "*.tmp",
            "*.temp",
            "*.log",
            "*.cache",
            "__pycache__",
            ".DS_Store",
            "Thumbs.db",
        ]

        deleted_count = 0
        for pattern in immediate_delete_files:
            deleted_count += file_manager._delete_files_by_pattern(pattern)

        if deleted_count > 0:
            # Python 3.14 Template Strings 사용
            print(f"[REPORT-ONLY] Cleanup target: {deleted_count} files")

        # 기능별 폴더 정리
        if file_manager.config.get("folder_management_enabled", True):
            file_manager.organize_files_by_function()

        # 정기 정리 실행
        if file_manager.should_run_cleanup():
            file_manager.auto_cleanup()

    except Exception as e:
        # Python 3.14 Template Strings 사용
        print(f"File management system initialization failed: {e}")


# [워크트리 규칙 준수] 메인 서버 전용 Flask 앱 초기화
# 메인 프로젝트 디렉토리에서만 실행되도록 명시적으로 경로 지정
app_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(app_dir, "templates")
static_dir = os.path.join(app_dir, "static")
db_file_path = os.path.join(app_dir, "database", "app.db")

# [검증] homepage1 디렉토리가 아닌지 확인
# if "homepage1" in app_dir.replace("\\", "/").split("/"):
#    raise RuntimeError(f"[워크트리 규칙 위반] 메인 서버(app.py)는 homepage1 디렉토리에서 실행되면 안 됩니다. 현재 경로: {app_dir}")

print(f"[워크트리 확인] 메인 서버 앱 디렉토리: {app_dir}")
print(f"[워크트리 확인] 템플릿 디렉토리: {template_dir}")
print(f"[워크트리 확인] Static 디렉토리: {static_dir}")


def ensure_database_initialized():
    """
    서버 기동 시 DB를 필요할 때만 초기화하여 기존 데이터를 보존한다.
    """
    if not os.path.exists(db_file_path):
        print("[DB] 데이터베이스가 없어 새로 생성합니다.")
        init_db()
    else:
        print("[DB] 기존 데이터베이스를 유지합니다 (init_db 생략).")


app = Flask(
    __name__,
    template_folder=template_dir,  # 메인 프로젝트의 templates 명시
    static_folder=static_dir,  # 메인 프로젝트의 static 명시
    static_url_path="/static",  # URL 경로 명시
)


# 전역 텍스트 주입
@app.context_processor
def inject_text():
    from datetime import datetime

    return {
        "text": CONTENT_CACHE,
        "t": get_text,
        "csrf_token": generate_csrf_token,
        "timestamp": int(datetime.now().timestamp()),  # 캐시 무력화용 타임스탬프
    }


# 기본 로깅 초기화
init_logging()
ensure_database_initialized()

# 버전 관리 시스템 초기화
try:
    # 초기 버전 생성 (없는 경우에만)
    versions = version_manager.list_versions(1)
    if not versions:
        version_manager.create_version("초기 버전", "system", "auto")
        print("Initial version created")

    # 자동 변경 감지 시작
    change_detector.start_monitoring()
    print("Auto change detection started")

    # 파일 크기 감시 (앱 시작 시 1회 실행)
    print("\n" + "=" * 60)
    file_size_monitor.monitor_and_report()
    print("=" * 60 + "\n")
except Exception as e:
    # Python 3.14 Template Strings 사용
    print(f"Version management system initialization failed: {e}")


# 세션 강제 초기화 훅 제거 (로그인 유지 보장)
@app.before_request
def _preserve_session():
    # 정적 파일/ API 요청은 그대로 통과시키고, 세션을 임의로 지우지 않음
    if request.path.startswith("/static") or request.path.startswith("/api/"):
        return None
    return None


# 간단한 요청 로깅
@app.before_request
def _log_request():
    # 성능 최적화: 정적 파일 및 헬스 체크는 로깅 제외
    if (
        request.path.startswith("/static")
        or request.path.startswith("/assets")
        or request.path == "/health"
    ):
        return

    try:
        # Python 3.14 Template Strings 사용
        app.logger.info(f"REQ {request.method} {request.path}")
        adapter = app.url_map.bind_to_environ(request.environ)
        try:
            endpoint, params = adapter.match()
            url_rule = getattr(request, "url_rule", None)
            app.logger.info(
                "MATCH endpoint=%s params=%s rule=%s",
                endpoint,
                params,
                getattr(url_rule, "rule", None),
            )
        except HTTPException as http_exc:
            app.logger.info("MATCH miss: %s", http_exc)
        except Exception as exc:
            app.logger.info("MATCH error: %s", exc)
    except Exception as exc:
        app.logger.warning(f"Request logging failed: {exc}")

    # 간단한 CSRF 가드 (상태 변경 메서드만 검사, 로그인/회원가입은 예외)
    token = None
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.path not in ("/login", "/register"):
            token = (
                request.headers.get("X-CSRF-Token")
                or request.form.get("csrf_token")
                or request.args.get("csrf_token")
            )

    if token:
        try:
            if not validate_csrf_token(token):
                app.logger.warning("CSRF token validation failed: %s", token)
                # 개발 환경에서는 경고만 로그하고 계속 진행
                # return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 403
        except Exception as exc:
            app.logger.warning("CSRF validation error: %s", exc, exc_info=True)
            # 개발 환경에서는 오류를 반환하지 않고 계속 진행
            # return jsonify({'success': False, 'message': 'CSRF validation failed'}), 403


@app.after_request
def _log_response(resp):
    try:
        # Python 3.14 Template Strings 사용
        app.logger.info(
            f"RES {resp.status_code} {request.path} endpoint={getattr(request, 'endpoint', None)}"
        )
    except Exception:
        pass
    return resp


# 성능 최적화: 브라우저 캐싱 헤더 추가
@app.after_request
def _add_cache_headers(resp):
    """정적 파일에 캐시 헤더 추가 (1년)"""
    # 정적 파일 (CSS, JS, 이미지 등)
    if request.path.startswith("/static/"):
        # 1년 캐시 (31536000초)
        resp.cache_control.max_age = 31536000
        resp.cache_control.public = True
    return resp


# 보안 강화 시스템 초기화
from core.security_enhancement import SecurityMiddleware, security_config

# 기본 설정
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DATABASE"] = "database/app.db"

# 세션 보안 강화 설정
app.config["SESSION_COOKIE_HTTPONLY"] = True  # XSS 방지
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF 방지
app.config["SESSION_COOKIE_SECURE"] = (
    security_config.is_secure_cookie_required()
)  # HTTPS 전용
app.config["PERMANENT_SESSION_LIFETIME"] = settings.PERMANENT_SESSION_LIFETIME
app.config["SESSION_COOKIE_NAME"] = "flask_session"
app.config["SESSION_COOKIE_PATH"] = "/"  # 쿠키 경로 제한
app.config["SESSION_COOKIE_DOMAIN"] = None  # 도메인 제한
app.config["SESSION_REFRESH_EACH_REQUEST"] = True  # 매 요청마다 세션 갱신
app.config["SESSION_USE_SIGNER"] = True  # 세션 서명 활성화

# 파일 업로드 보안 설정
app.config["MAX_CONTENT_LENGTH"] = settings.MAX_FILE_SIZE  # 파일 크기 제한
app.config["UPLOAD_FOLDER"] = settings.UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = settings.OUTPUT_FOLDER

# 이메일 발송 설정 (Flask-Mail)
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() in (
    "true",
    "1",
    "yes",
)
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
    "MAIL_DEFAULT_SENDER", "RohaTax <noreply@rohatax.com>"
)

# Flask-Mail 초기화
init_mail(app)

# 보안 미들웨어 활성화
security_middleware = SecurityMiddleware(app, security_config)

from routes.admin import admin_bp
from routes.admin.activity_log_api import activity_log_bp
from routes.admin.tax_api import admin_tax_bp
from routes.api_modules.admin_api import admin_api_bp
# 기존 user_api (비상시 롤백용으로 보존)
# from routes.api_modules.user_api import user_api_bp
# 신형 엔진 (user_api_v2)
from routes.api_modules.user_api_v2 import user_api_v2_bp
# from routes.conversion import conversion_bp  # 제거됨 - conversion_engine_routes로 이동
from routes.conversion_modules.conversion_engine_routes import \
    conversion_engine_bp
from routes.conversion_modules.gold_customers_routes import \
    gold_customers_bp  # noop-reload
from routes.conversion_modules.guideline_routes import guideline_bp
from routes.conversion_modules.page_routes import page_bp
from routes.conversion_modules.security_routes import security_bp
from routes.conversion_modules.token_routes import token_bp
from routes.conversion_modules.user_routes import user_bp
# 블루프린트 등록
from routes.home import home_bp
from routes.home_modules.api_routes import home_api_bp
from routes.home_modules.auth_routes import auth_bp
from routes.home_modules.email_routes import email_bp
from routes.home_modules.password_routes import password_bp
from routes.home_modules.profile_routes import profile_bp
from routes.home_modules.registration_routes import registration_bp
from routes.ops import ops_bp

if "home" not in app.blueprints:
    app.register_blueprint(home_bp)
if "home_api" not in app.blueprints:
    app.register_blueprint(home_api_bp)
    if "auth" not in app.blueprints:
        app.register_blueprint(auth_bp)
if "registration" not in app.blueprints:
    app.register_blueprint(registration_bp)
if "profile" not in app.blueprints:
    app.register_blueprint(profile_bp)
if "password" not in app.blueprints:
    app.register_blueprint(password_bp)
if "email" not in app.blueprints:
    app.register_blueprint(email_bp)
# if 'conversion' not in app.blueprints:  # 제거됨
#     app.register_blueprint(conversion_bp)  # 제거됨
if "conversion_engine" not in app.blueprints:
    app.register_blueprint(conversion_engine_bp)
if "admin" not in app.blueprints:
    app.register_blueprint(admin_bp)
if "activity_log_api" not in app.blueprints:
    app.register_blueprint(activity_log_bp)
if "admin_tax" not in app.blueprints:
    app.register_blueprint(admin_tax_bp)
if "ops" not in app.blueprints:
    app.register_blueprint(ops_bp)
if "admin_api" not in app.blueprints:
    app.register_blueprint(admin_api_bp)
# 기존 user_api (비상시 롤백용으로 보존)
# if 'user_api' not in app.blueprints:
#     app.register_blueprint(user_api_bp)
# 신형 엔진 (user_api_v2)
if "user_api_v2" not in app.blueprints:
    app.register_blueprint(user_api_v2_bp)
if "gold_customers" not in app.blueprints:
    app.register_blueprint(gold_customers_bp)
if "security" not in app.blueprints:
    app.register_blueprint(security_bp)
if "guideline" not in app.blueprints:
    app.register_blueprint(guideline_bp)
if "page" not in app.blueprints:
    app.register_blueprint(page_bp)
if "user" not in app.blueprints:
    app.register_blueprint(user_bp)
if "token" not in app.blueprints:
    app.register_blueprint(token_bp)

# Payment routes 등록
from routes.payment_routes import payment_bp, _build_shop_context

if "payment_routes" not in app.blueprints:
    app.register_blueprint(payment_bp)

# Order API 등록
from routes.api_modules.order_api import order_bp

if "order_api" not in app.blueprints:
    app.register_blueprint(order_bp)

# Payment Complete API 등록
from routes.api_modules.payment_complete_api import payment_complete_bp

if "payment_complete_api" not in app.blueprints:
    app.register_blueprint(payment_complete_bp)

# kweon21 (AI Blog Studio) 등록
from routes.playground_routes.kweon21_routes import kweon21_bp

if "kweon21" not in app.blueprints:
    app.register_blueprint(kweon21_bp)
    print(
        f"[kweon21] AI 블로그 스튜디오 가동 완료! (URL Prefix: {kweon21_bp.url_prefix})"
    )

# Studio API (보안 프록시) 등록
from routes.playground_routes.studio_api import studio_api_bp

if "studio_api" not in app.blueprints:
    app.register_blueprint(studio_api_bp)
    print(
        f"[studio_api] AI 블로그 스튜디오 보안 프록시 API 가동 완료! (URL Prefix: {studio_api_bp.url_prefix})"
    )

# Playground 대시보드 등록
from routes.playground_routes import playground_bp

if "playground" not in app.blueprints:
    app.register_blueprint(playground_bp)
    print(
        f"[playground] 블로그 연구소 대시보드 가동 완료! (URL Prefix: {playground_bp.url_prefix})"
    )


@app.route("/")
def homepage():
    """
    메인 랜딩 페이지
    - 하단 멤버십 5종(무료 2 + 유료 3)이 상점 상품 관리 데이터에 맞춰 자동 갱신되도록
      payment_routes._build_shop_context()에서 생성한 컨텍스트를 함께 주입
    - 결제/구매 로직은 포함하지 않고, 텍스트/금액/토큰/기간 정보만 공유
    """
    context = {}
    try:
        context = _build_shop_context()
    except Exception:
        # 상점 컨텍스트 로딩 실패 시에도 홈페이지는 열리도록 방어
        context = {}
    return render_template("homepage.html", **context)


@app.route("/new")
def homepage_new():
    """신규 디자인 실험용 벙커 (완전 격리)"""
    return render_template("homepage_new.html")


@app.route("/terms")
def terms():
    """서비스 이용약관 페이지"""
    terms_content = """
<h3>제 1 조 (목적)</h3>
<p>본 약관은 1Tax(이하 "회사")가 제공하는 로하택스 및 관련 제반 서비스(이하 "서비스")의 이용과 관련하여 회사와 회원 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.</p>

<h3>제 2 조 (용어의 정의)</h3>
<p>1. "토큰"이라 함은 서비스 내에서 파일 변환 등 유료 기능을 이용하기 위해 사용되는 가상의 데이터를 말합니다.<br>
2. "변환"이라 함은 회원이 업로드한 엑셀 파일을 국세청 양식에 맞게 가공하는 과정을 말합니다.</p>

<h3>제 3 조 (데이터의 보관 및 삭제)</h3>
<p>1. 회사는 회원이 업로드한 파일(정산서 등)을 변환 처리를 위해 <strong>임시 저장</strong>하며, <strong>24시간이 경과하면 서버에서 영구적으로 자동 삭제</strong>합니다.<br>
2. 회원은 변환된 파일을 즉시 다운로드하여 별도 보관해야 하며, 자동 삭제된 데이터에 대한 복구 책임은 회원에게 있습니다.</p>

<h3>제 4 조 (환불 및 취소)</h3>
<p>1. 유상으로 충전한 토큰은 구매 후 7일 이내에 사용하지 않은 경우 전액 환불이 가능합니다.<br>
2. 이미 사용된 토큰이나, 이벤트로 무상 지급된 토큰은 환불 대상에서 제외됩니다.</p>

<h3>제 5 조 (면책)</h3>
<p>회사는 회원이 업로드한 파일 자체의 오류나, 국세청 홈택스 시스템의 변경으로 인한 변환 결과의 불일치에 대해서는 책임을 지지 않습니다.</p>
"""
    return render_template("legal.html", title="서비스 이용약관", content=terms_content)


@app.route("/privacy")
def privacy():
    """개인정보 처리방침 페이지"""
    privacy_content = """
<h3>1. 수집하는 개인정보 항목</h3>
<p>회사는 회원가입 및 서비스 제공을 위해 아래와 같은 정보를 수집합니다.<br>
- 필수항목: 아이디, 비밀번호, 회사명, 사업자등록번호, 대표자명, 휴대전화번호, 이메일, 주소</p>

<h3>2. 개인정보의 수집 및 이용 목적</h3>
<p>- 서비스 이용에 따른 본인 식별 및 불량 회원의 부정이용 방지<br>
- 세금계산서 변환 서비스 제공 및 요금 정산<br>
- 고지사항 전달 및 불만 처리</p>

<h3>3. 개인정보의 처리 위탁 및 파일 관리</h3>
<p>회사는 서비스 제공을 위해 회원이 업로드한 파일(제3자의 개인정보 포함 가능)을 처리합니다.<br>
- 보관 기간: 파일 업로드 후 <strong>24시간</strong><br>
- 파기 방법: 서버 내 자동 삭제 스크립트를 통한 영구 삭제<br>
- 안전성 확보 조치: 업로드된 파일은 외부에서 접근 불가능한 내부 경로에 저장되며, 정해진 목적 외에는 열람되지 않습니다.</p>

<h3>4. 개인정보 보호책임자</h3>
<p>이름: (관리자 권강록)<br>
이메일: kweon4309@naver.com</p>
"""
    return render_template(
        "legal.html", title="개인정보 처리방침", content=privacy_content
    )


# API 엔드포인트
@app.route("/api/test")
def api_test():
    """API 테스트 엔드포인트"""
    return jsonify(
        {"status": "success", "message": "뼈대 서버가 정상 작동합니다!", "port": 8080}
    )


# 에러 핸들러
@app.errorhandler(404)
def not_found(_):
    # /studio 경로는 kweon21_bp에서 처리하므로 404 핸들러에서 완전히 제외
    # Flask의 라우팅 시스템이 먼저 매칭을 시도하므로, 여기 도달했다는 것은 실제 404
    if request.path.startswith("/studio"):
        # kweon21_bp가 처리해야 하는 경로인데 여기 도달했다면
        # 실제로는 kweon21_bp의 라우트가 매칭되어야 함
        # Flask의 라우팅 시스템이 먼저 매칭을 시도하므로, 여기 도달했다는 것은 실제 404
        # 따라서 빈 응답을 반환하여 kweon21_bp가 처리하도록 함
        return "", 200  # 200을 반환하여 kweon21_bp가 처리하도록 함
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(_):
    return render_template("errors/500.html"), 500


# 헬스체크 엔드포인트 추가
@app.route("/health")
def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 기본 상태 확인
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": time.time() - start_time if "start_time" in globals() else 0,
        }

        # 데이터베이스 연결 확인
        try:
            with get_conn() as conn:
                conn.execute("SELECT 1").fetchone()
            health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"

        # 메모리 사용량 확인
        try:
            memory = psutil.virtual_memory()
            health_status["memory_usage"] = f"{memory.percent:.1f}%"
            if memory.percent > 90:
                health_status["status"] = "warning"
        except:
            health_status["memory_usage"] = "unknown"

        # CPU 사용량 확인
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            health_status["cpu_usage"] = f"{cpu_percent:.1f}%"
            if cpu_percent > 90:
                health_status["status"] = "warning"
        except:
            health_status["cpu_usage"] = "unknown"

        # 디스크 사용량 확인
        try:
            disk = psutil.disk_usage("/")
            health_status["disk_usage"] = f"{disk.percent:.1f}%"
            if disk.percent > 90:
                health_status["status"] = "warning"
        except:
            health_status["disk_usage"] = "unknown"

        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )


# 시작 시간 기록
start_time = time.time()


# 관리자 전용 가구 디자인 스튜디오
@app.route("/admin/studio")
def admin_furniture_studio():
    """관리자 전용 가구 디자인 스튜디오"""
    # 추후 로그인 체크 로직이 들어갈 자리
    return render_template("admin/furniture_studio.html")


if __name__ == "__main__":
    try:
        # 파일 관리 시스템 초기화 (가장 먼저 실행)
        init_file_management()

        # 기존 초기화
        init_logging()
        init_db()
        seed_demo()
        version_manager.create_initial_version()
        change_detector.start_monitoring()

        print(f"SERVER START PORT {settings.PORT}")
        print(f"OPEN http://localhost:{settings.PORT}")
        print(f"LOCAL ACCESS ONLY: http://127.0.0.1:{settings.PORT}")
    except Exception:
        # 초기화 중 오류가 발생해도 서버 기동 자체는 시도
        pass

    app.run(host="127.0.0.1", port=settings.PORT, debug=settings.DEBUG)
