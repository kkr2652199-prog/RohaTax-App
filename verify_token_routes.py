"""토큰 라우트 검증 스크립트"""
import sys
sys.path.insert(0, '.')

try:
    from routes.conversion_modules.token_routes import token_bp
    print("[SUCCESS] token_bp import 성공")
    
    # Blueprint 등록 확인
    routes = []
    for rule in token_bp.deferred_functions:
        if hasattr(rule, 'rule'):
            routes.append(rule.rule)
    
    print(f"[SUCCESS] token_bp에 {len(routes)}개 라우트 등록됨")
    
    # 주요 라우트 확인
    if any('/api/use-token' in str(r) for r in routes):
        print("[SUCCESS] /api/use-token 라우트 확인됨")
    if any('/api/token-status' in str(r) for r in routes):
        print("[SUCCESS] /api/token-status 라우트 확인됨")
        
    # app.py에서 등록 확인
    from app import app
    if 'token' in app.blueprints:
        print("[SUCCESS] app.py에 token_bp 등록 확인됨")
    else:
        print("[ERROR] app.py에 token_bp가 등록되지 않음")
        
except Exception as e:
    print(f"[ERROR] 검증 실패: {str(e)}")
    import traceback
    traceback.print_exc()


import sys
sys.path.insert(0, '.')

try:
    from routes.conversion_modules.token_routes import token_bp
    print("[SUCCESS] token_bp import 성공")
    
    # Blueprint 등록 확인
    routes = []
    for rule in token_bp.deferred_functions:
        if hasattr(rule, 'rule'):
            routes.append(rule.rule)
    
    print(f"[SUCCESS] token_bp에 {len(routes)}개 라우트 등록됨")
    
    # 주요 라우트 확인
    if any('/api/use-token' in str(r) for r in routes):
        print("[SUCCESS] /api/use-token 라우트 확인됨")
    if any('/api/token-status' in str(r) for r in routes):
        print("[SUCCESS] /api/token-status 라우트 확인됨")
        
    # app.py에서 등록 확인
    from app import app
    if 'token' in app.blueprints:
        print("[SUCCESS] app.py에 token_bp 등록 확인됨")
    else:
        print("[ERROR] app.py에 token_bp가 등록되지 않음")
        
except Exception as e:
    print(f"[ERROR] 검증 실패: {str(e)}")
    import traceback
    traceback.print_exc()


import sys
sys.path.insert(0, '.')

try:
    from routes.conversion_modules.token_routes import token_bp
    print("[SUCCESS] token_bp import 성공")
    
    # Blueprint 등록 확인
    routes = []
    for rule in token_bp.deferred_functions:
        if hasattr(rule, 'rule'):
            routes.append(rule.rule)
    
    print(f"[SUCCESS] token_bp에 {len(routes)}개 라우트 등록됨")
    
    # 주요 라우트 확인
    if any('/api/use-token' in str(r) for r in routes):
        print("[SUCCESS] /api/use-token 라우트 확인됨")
    if any('/api/token-status' in str(r) for r in routes):
        print("[SUCCESS] /api/token-status 라우트 확인됨")
        
    # app.py에서 등록 확인
    from app import app
    if 'token' in app.blueprints:
        print("[SUCCESS] app.py에 token_bp 등록 확인됨")
    else:
        print("[ERROR] app.py에 token_bp가 등록되지 않음")
        
except Exception as e:
    print(f"[ERROR] 검증 실패: {str(e)}")
    import traceback
    traceback.print_exc()


import sys
sys.path.insert(0, '.')

try:
    from routes.conversion_modules.token_routes import token_bp
    print("[SUCCESS] token_bp import 성공")
    
    # Blueprint 등록 확인
    routes = []
    for rule in token_bp.deferred_functions:
        if hasattr(rule, 'rule'):
            routes.append(rule.rule)
    
    print(f"[SUCCESS] token_bp에 {len(routes)}개 라우트 등록됨")
    
    # 주요 라우트 확인
    if any('/api/use-token' in str(r) for r in routes):
        print("[SUCCESS] /api/use-token 라우트 확인됨")
    if any('/api/token-status' in str(r) for r in routes):
        print("[SUCCESS] /api/token-status 라우트 확인됨")
        
    # app.py에서 등록 확인
    from app import app
    if 'token' in app.blueprints:
        print("[SUCCESS] app.py에 token_bp 등록 확인됨")
    else:
        print("[ERROR] app.py에 token_bp가 등록되지 않음")
        
except Exception as e:
    print(f"[ERROR] 검증 실패: {str(e)}")
    import traceback
    traceback.print_exc()


