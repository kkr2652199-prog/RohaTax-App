from dotenv import load_dotenv
import os

# .env 파일 로드 (프로젝트 루트에서)
load_dotenv()

from flask import Flask, request, jsonify, render_template, session
from werkzeug.exceptions import HTTPException
from core.content_loader import CONTENT_CACHE, get_text
from config.settings import settings
from core.logging_setup import init_logging
from core.db import init_db, seed_demo, get_conn
from core.security import generate_csrf_token, validate_csrf_token
from core.version_manager import version_manager
from core.change_detector import change_detector
from core.file_manager import FileManager
from core.file_size_monitor import file_size_monitor
from core.email_sender import init_mail
import os
import time
import psutil
from datetime import datetime
import mimetypes

# 자동 파일 정리 시스템 초기화
def init_file_management():
    """파일 관리 시스템 초기화"""
    try:
        file_manager = FileManager(".")
        
        # 즉시 삭제할 파일들
        immediate_delete_files = [
            'check_system.py',
            'analyze_db.py', 
            'app_content.py',
            'test_*.py',  # 루트에 있는 테스트 파일들
            '*.tmp',
            '*.temp',
            '*.log',
            '*.cache',
            '__pycache__',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        deleted_count = 0
        for pattern in immediate_delete_files:
            deleted_count += file_manager._delete_files_by_pattern(pattern)
        
        if deleted_count > 0:
            # Python 3.14 Template Strings 사용
            print(f"[REPORT-ONLY] Cleanup target: {deleted_count} files")
        
        # 기능별 폴더 정리
        if file_manager.config.get('folder_management_enabled', True):
            file_manager.organize_files_by_function()
        
        # 정기 정리 실행
        if file_manager.should_run_cleanup():
            file_manager.auto_cleanup()
            
    except Exception as e:
        # Python 3.14 Template Strings 사용
        print(f"File management system initialization failed: {e}")

app = Flask(__name__)
# 전역 텍스트 주입
@app.context_processor
def inject_text():
    return {
        'text': CONTENT_CACHE,
        't': get_text,
        'csrf_token': generate_csrf_token
    }

# 기본 로깅 초기화
init_logging()
init_db()
seed_demo()

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
    print("\n" + "="*60)
    file_size_monitor.monitor_and_report()
    print("="*60 + "\n")
except Exception as e:
    # Python 3.14 Template Strings 사용
    print(f"Version management system initialization failed: {e}")

# 세션 강제 초기화 훅 제거 (로그인 유지 보장)
@app.before_request
def _preserve_session():
    # 정적 파일/ API 요청은 그대로 통과시키고, 세션을 임의로 지우지 않음
    if request.path.startswith('/static') or request.path.startswith('/api/'):
        return None
    return None

# 간단한 요청 로깅
@app.before_request
def _log_request():
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
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.path not in ('/login', '/register'):
            token = (
                request.headers.get('X-CSRF-Token')
                or request.form.get('csrf_token')
                or request.args.get('csrf_token')
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
        app.logger.info(f"RES {resp.status_code} {request.path} endpoint={getattr(request, 'endpoint', None)}")
    except Exception:
        pass
    return resp

# 성능 최적화: 브라우저 캐싱 헤더 추가
@app.after_request
def _add_cache_headers(resp):
    """정적 파일에 캐시 헤더 추가 (1년)"""
    # 정적 파일 (CSS, JS, 이미지 등)
    if request.path.startswith('/static/'):
        # 1년 캐시 (31536000초)
        resp.cache_control.max_age = 31536000
        resp.cache_control.public = True
    return resp

# 보안 강화 시스템 초기화
from core.security_enhancement import SecurityMiddleware, security_config

# 기본 설정
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['DATABASE'] = 'database/app.db'

# 세션 보안 강화 설정
app.config['SESSION_COOKIE_HTTPONLY'] = True  # XSS 방지
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF 방지
app.config['SESSION_COOKIE_SECURE'] = security_config.is_secure_cookie_required()  # HTTPS 전용
app.config['PERMANENT_SESSION_LIFETIME'] = settings.PERMANENT_SESSION_LIFETIME
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['SESSION_COOKIE_PATH'] = '/'  # 쿠키 경로 제한
app.config['SESSION_COOKIE_DOMAIN'] = None  # 도메인 제한
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # 매 요청마다 세션 갱신
app.config['SESSION_USE_SIGNER'] = True  # 세션 서명 활성화

# 파일 업로드 보안 설정
app.config['MAX_CONTENT_LENGTH'] = settings.MAX_FILE_SIZE  # 파일 크기 제한
app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = settings.OUTPUT_FOLDER

# 이메일 발송 설정 (Flask-Mail)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'RohaTax <noreply@rohatax.com>')

# Flask-Mail 초기화
init_mail(app)

# 보안 미들웨어 활성화
security_middleware = SecurityMiddleware(app, security_config)

# 블루프린트 등록
from routes.home import home_bp
# from routes.conversion import conversion_bp  # 제거됨 - conversion_engine_routes로 이동
from routes.conversion_modules.conversion_engine_routes import conversion_engine_bp
from routes.admin import admin_bp
from routes.admin.activity_log_api import activity_log_bp
from routes.ops import ops_bp
from routes.api import api_bp
from routes.conversion_modules.gold_customers_routes import gold_customers_bp  # noop-reload
from routes.conversion_modules.security_routes import security_bp
from routes.conversion_modules.guideline_routes import guideline_bp
from routes.conversion_modules.page_routes import page_bp
from routes.conversion_modules.user_routes import user_bp
from routes.conversion_modules.token_routes import token_bp

if 'home' not in app.blueprints:
    app.register_blueprint(home_bp)
# if 'conversion' not in app.blueprints:  # 제거됨
#     app.register_blueprint(conversion_bp)  # 제거됨
if 'conversion_engine' not in app.blueprints:
    app.register_blueprint(conversion_engine_bp)
if 'admin' not in app.blueprints:
    app.register_blueprint(admin_bp)
if 'activity_log_api' not in app.blueprints:
    app.register_blueprint(activity_log_bp)
if 'ops' not in app.blueprints:
    app.register_blueprint(ops_bp)
if 'api' not in app.blueprints:
    app.register_blueprint(api_bp)
if 'gold_customers' not in app.blueprints:
    app.register_blueprint(gold_customers_bp)
if 'security' not in app.blueprints:
    app.register_blueprint(security_bp)
if 'guideline' not in app.blueprints:
    app.register_blueprint(guideline_bp)
if 'page' not in app.blueprints:
    app.register_blueprint(page_bp)
if 'user' not in app.blueprints:
    app.register_blueprint(user_bp)
if 'token' not in app.blueprints:
    app.register_blueprint(token_bp)


@app.route('/')
def homepage():
    return render_template('homepage.html')

# API 엔드포인트
@app.route('/api/test')
def api_test():
    """API 테스트 엔드포인트"""
    return jsonify({
        'status': 'success',
        'message': '뼈대 서버가 정상 작동합니다!',
        'port': 8080
    })

# 에러 핸들러
@app.errorhandler(404)
def not_found(_):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(_):
    return render_template('errors/500.html'), 500

# 헬스체크 엔드포인트 추가
@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    try:
        # 기본 상태 확인
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'uptime': time.time() - start_time if 'start_time' in globals() else 0
        }
        
        # 데이터베이스 연결 확인
        try:
            with get_conn() as conn:
                conn.execute("SELECT 1").fetchone()
            health_status['database'] = 'connected'
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # 메모리 사용량 확인
        try:
            memory = psutil.virtual_memory()
            health_status['memory_usage'] = f"{memory.percent:.1f}%"
            if memory.percent > 90:
                health_status['status'] = 'warning'
        except:
            health_status['memory_usage'] = 'unknown'
        
        # CPU 사용량 확인
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            health_status['cpu_usage'] = f"{cpu_percent:.1f}%"
            if cpu_percent > 90:
                health_status['status'] = 'warning'
        except:
            health_status['cpu_usage'] = 'unknown'
        
        # 디스크 사용량 확인
        try:
            disk = psutil.disk_usage('/')
            health_status['disk_usage'] = f"{disk.percent:.1f}%"
            if disk.percent > 90:
                health_status['status'] = 'warning'
        except:
            health_status['disk_usage'] = 'unknown'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

# 시작 시간 기록
start_time = time.time()

if __name__ == '__main__':
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
        pass
    app.run(host='127.0.0.1', port=settings.PORT, debug=settings.DEBUG)