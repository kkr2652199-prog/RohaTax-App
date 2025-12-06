"""
kweon21 독립 놀이터 라우트 모듈

- 역할: /studio 엔드포인트를 제공하여 kweon21 React 앱을 독립적으로 서빙
- 주의: 기존 변환 앱과 100% 격리된 독립 모듈
- kweon21은 Vite로 빌드된 정적 파일을 Flask에서 서빙합니다.
"""

import os
import re
from flask import Blueprint, send_from_directory, send_file, Response, session, redirect, url_for

# kweon21 전용 Blueprint 생성 (playground와 독립)
kweon21_bp = Blueprint(
    'kweon21',
    __name__,
    url_prefix='/studio',
    static_folder='../../kweon21/dist',
    static_url_path='/static/kweon21'
)

# kweon21 빌드 디렉토리 경로
KWEON21_DIST_DIR = os.path.join(
    os.path.dirname(__file__),
    '../../kweon21/dist'
)


# React SPA를 위한 만능 라우터 (Catch-All)
# 루트 경로 ('/studio')와 하위 모든 경로 ('/studio/abc/def...')를 모두 처리
@kweon21_bp.route('/', defaults={'path': ''})
@kweon21_bp.route('/<path:path>')
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
    
    # A. 실제 파일이 존재하면 그 파일을 반환 (JS, CSS, 이미지 등)
    if path != "" and os.path.exists(os.path.join(dist_dir, path)) and os.path.isfile(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    
    # B. assets 폴더 내 파일 처리
    if path.startswith('assets/'):
        assets_dir = os.path.join(dist_dir, 'assets')
        filename = path.replace('assets/', '')
        file_path = os.path.join(assets_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(assets_dir, filename)
    
    # C. 그 외 모든 경우(새로고침, 직접접속, React Router 경로 등)는 index.html 반환
    index_path = os.path.join(dist_dir, 'index.html')
    if os.path.exists(index_path):
        # index.html을 읽어서 asset 경로를 /studio/로 변환
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 절대 경로를 /studio/로 변환
        # /assets/... -> /studio/assets/...
        html_content = re.sub(r'src="/assets/', 'src="/studio/assets/', html_content)
        html_content = re.sub(r'href="/assets/', 'href="/studio/assets/', html_content)
        html_content = re.sub(r'href="/index\.css', 'href="/studio/index.css', html_content)
        
        return Response(html_content, mimetype='text/html')
    else:
        # 빌드 파일이 없는 경우 안내 페이지
        return f"""
        <html>
            <head><title>kweon21 스튜디오</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>🚧 kweon21 스튜디오 준비 중</h1>
                <p>kweon21 앱을 빌드해야 합니다.</p>
                <p style="color: #666; margin-top: 20px;">
                    <code>cd kweon21 && npm install && npm run build</code>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 40px;">
                    빌드 디렉토리: {dist_dir}
                </p>
            </body>
        </html>
        """, 503

