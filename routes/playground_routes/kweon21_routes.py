"""
kweon21 독립 놀이터 라우트 모듈

- 역할: /studio 엔드포인트를 제공하여 kweon21 React 앱을 독립적으로 서빙
- 주의: 기존 변환 앱과 100% 격리된 독립 모듈
- kweon21은 Vite로 빌드된 정적 파일을 Flask에서 서빙합니다.
"""

import os
import re

from flask import (
    Blueprint,
    Response,
    redirect,
    render_template,
    send_file,
    send_from_directory,
    session,
    url_for,
)
import sqlite3
from core.extensions import limiter

# kweon21 전용 Blueprint 생성 (playground와 독립)
kweon21_bp = Blueprint(
    "kweon21",
    __name__,
    url_prefix="/studio",
    static_folder="../../kweon21/dist",
    static_url_path="/static/kweon21",
)

# kweon21 빌드 디렉토리 경로
KWEON21_DIST_DIR = os.path.join(os.path.dirname(__file__), "../../kweon21/dist")


# Route A: 순수한 React 앱 반환 (/studio/app)
@kweon21_bp.route("/app")
@kweon21_bp.route("/app/<path:path>")
@limiter.exempt  # Rate limiting 제외
def kweon21_app(path=""):
    """
    순수한 React 앱을 Iframe에서 로드하기 위한 라우트.
    Flask base.html 상속 없이 kweon21/dist/index.html을 그대로 반환.
    """
    dist_dir = os.path.abspath(KWEON21_DIST_DIR)
    index_path = os.path.join(dist_dir, "index.html")
    
    if not os.path.exists(index_path):
        return (
            f"""
        <html>
            <head><title>kweon21 스튜디오</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>🚧 kweon21 스튜디오 준비 중</h1>
                <p>kweon21 앱을 빌드해야 합니다.</p>
                <p style="color: #666; margin-top: 20px;">
                    <code>cd homepage1/kweon21 && npm install && npm run build</code>
                </p>
            </body>
        </html>
        """,
            503,
        )
    
    # index.html 파일을 읽어서 반환 (base.html 상속 없이)
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # assets 경로를 /studio/app/assets로 변환
    html_content = html_content.replace('/assets/', '/studio/app/assets/')
    html_content = html_content.replace('src="/assets/', 'src="/studio/app/assets/')
    html_content = html_content.replace('href="/assets/', 'href="/studio/app/assets/')
    
    # React 앱 내부 헤더 CSS 제거 (Flask 헤더와 중복 방지)
    html_content = html_content.replace(
        '<link rel="stylesheet" href="/static/css/layout/header.css?v=WHITE_BG_FIX_V2">',
        '<!-- Header CSS removed to prevent duplicate header in iframe -->'
    )
    
    response = Response(html_content, mimetype='text/html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # iframe에서 로드 가능하도록 X-Frame-Options 설정
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


# Route B: 정적 파일 서빙 (assets, static 등)
@kweon21_bp.route("/app/assets/<path:filename>")
@limiter.exempt  # Rate limiting 제외
def kweon21_app_assets(filename):
    """React 앱의 assets 파일 서빙"""
    dist_dir = os.path.abspath(KWEON21_DIST_DIR)
    assets_dir = os.path.join(dist_dir, "assets")
    file_path = os.path.join(assets_dir, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        resp = send_from_directory(assets_dir, filename)
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return resp
    
    return "File not found", 404


# React SPA를 위한 만능 라우터 (Catch-All)
# 루트 경로 ('/studio')와 하위 모든 경로 ('/studio/abc/def...')를 모두 처리
@kweon21_bp.route("/", defaults={"path": ""})
@kweon21_bp.route("/<path:path>")
@limiter.exempt  # Rate limiting 제외
def kweon21_index(path):
    """
    React SPA를 위한 만능 라우터.

    - 정적 파일(js, css, 이미지)이 존재하면 그 파일을 반환
    - 그 외 모든 경우(새로고침, 직접접속, React Router 경로)는 index.html 반환
    - 로그인 체크는 React 앱 내에서 처리합니다 (Navbar 컴포넌트)
    - asset 경로를 /studio/로 변환하여 서빙합니다
    """
    from flask import Response

    dist_dir = os.path.abspath(KWEON21_DIST_DIR)

    # ✅ 캐시 무력화: React 앱은 항상 최신 상태 유지
    no_cache_headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    # A. 실제 파일이 존재하면 그 파일을 반환 (JS, CSS, 이미지 등)
    if (
        path != ""
        and os.path.exists(os.path.join(dist_dir, path))
        and os.path.isfile(os.path.join(dist_dir, path))
    ):
        resp = send_from_directory(dist_dir, path)
        resp.headers.update(no_cache_headers)
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return resp

    # B. assets 폴더 내 파일 처리 (기존 호환성 유지)
    if path.startswith("assets/"):
        assets_dir = os.path.join(dist_dir, "assets")
        filename = path.replace("assets/", "")
        file_path = os.path.join(assets_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            resp = send_from_directory(assets_dir, filename)
            resp.headers.update(no_cache_headers)
            resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
            return resp

    # C. /app 경로는 위의 kweon21_app 라우트로 리다이렉트
    if path == "app" or path.startswith("app/"):
        return redirect(url_for('kweon21.kweon21_app', path=path.replace("app/", "")))

    # D. 그 외 모든 경우(새로고침, 직접접속, React Router 경로 등)는 오버레이 템플릿 반환
    # 사용자 API 키 상태 확인
    has_key = False
    user_id = session.get('user_id')
    
    if user_id:
        from core.db import get_conn_optimized as get_conn
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                user = conn.execute(
                    "SELECT google_api_key FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
                    (user_id,)
                ).fetchone()
                if user and user['google_api_key']:
                    has_key = True
        except Exception:
            pass  # DB 오류 시 False로 유지
    
    # 빌드 파일 존재 확인
    index_path = os.path.join(dist_dir, "index.html")
    if not os.path.exists(index_path):
        return (
            f"""
        <html>
            <head><title>kweon21 스튜디오</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>🚧 kweon21 스튜디오 준비 중</h1>
                <p>kweon21 앱을 빌드해야 합니다.</p>
                <p style="color: #666; margin-top: 20px;">
                    <code>cd homepage1/kweon21 && npm install && npm run build</code>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 40px;">
                    빌드 디렉토리: {dist_dir}
                </p>
            </body>
        </html>
        """,
            503,
        )
    
    # 오버레이 템플릿 렌더링 (Iframe 방식)
    return render_template(
        'studio/studio_overlay.html',
        has_key=has_key
    )
