"""
토큰 관리 라우트 모듈
토큰 사용, 상태 조회 등의 토큰 관련 기능
"""

from flask import Blueprint, session, jsonify, request
from functools import wraps
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.security import generate_csrf_token
import time
import os
import json
from datetime import datetime
from core.utils import row_value

token_bp = Blueprint('token', __name__)


def admin_required(func):
    """관리자 전용 접근 가드"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return error("로그인이 필요합니다", 401)
        if not session.get('is_admin'):
            return error("관리자 권한이 필요합니다", 403)
        return func(*args, **kwargs)
    return wrapper

@token_bp.route('/api/use-token', methods=['POST'])
def use_token():
    """변환 작업 시 토큰 사용 API"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        data = request.get_json()
        tokens_to_use = data.get('tokens', 1)
        
        if not isinstance(tokens_to_use, int) or tokens_to_use <= 0:
            return error("유효하지 않은 토큰 수입니다", 400)
        
        with get_conn() as conn:
            # 현재 사용자 정보 조회
            user = conn.execute(
                "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            # 사용 가능한 토큰 계산
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
            
            if available_tokens < tokens_to_use:
                return error(f"토큰이 부족합니다. 사용 가능: {available_tokens}개", 400)
            
            # 토큰 사용 기록
            new_tokens_used = (user['tokens_used'] or 0) + tokens_to_use
            conn.execute(
                "UPDATE users SET tokens_used = ? WHERE id = ?",
                (new_tokens_used, session['user_id'])
            )
            conn.commit()
            
            # 새로운 토큰 상태 반환
            remaining_tokens = available_tokens - tokens_to_use
            
            return success({
                "tokens_used": tokens_to_use,
                "remaining_tokens": remaining_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": new_tokens_used
            })
            
    except Exception as e:
        return error(f"토큰 사용 중 오류가 발생했습니다: {str(e)}", 500)


@token_bp.route('/api/token-status', methods=['GET'])
def token_status():
    """현재 토큰 상태 조회 API (캐싱 적용)"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        with get_conn() as conn:
            user = conn.execute(
                "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
            
            return success({
                "available_tokens": available_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": user['tokens_used'] or 0,
                "timestamp": int(time.time())
            })
            
    except Exception as e:
        return error(f"토큰 상태 조회 중 오류가 발생했습니다: {str(e)}", 500)


@token_bp.route('/api/admin/token-logs', methods=['GET'])
@admin_required
def admin_list_token_logs():
    """간단한 파일 기반 토큰 로그 리스트 (관리자 전용: is_admin=1)
    쿼리: date=YYYY-MM-DD (optional)
    """
    # RBAC는 데코레이터에서 검증됨

    date_q = (request.args.get('date') or '').strip()
    base_dir = os.path.join('logs', 'token_logs')
    if not os.path.isdir(base_dir):
        return success({"logs": [], "count": 0})

    def load_one(path: str):
        items = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass
        return items

    logs = []
    if date_q:
        fp = os.path.join(base_dir, f"{date_q}.log")
        if os.path.exists(fp):
            logs.extend(load_one(fp))
    else:
        for name in sorted(os.listdir(base_dir), reverse=True)[:7]:
            if name.endswith('.log'):
                logs.extend(load_one(os.path.join(base_dir, name)))

    return success({"logs": logs, "count": len(logs)})


@token_bp.route('/api/admin/token-usage-summary', methods=['GET'])
@admin_required
def admin_token_usage_summary():
    """일자/유저별 간단 요약 (파일 로그 기반)"""
    # RBAC는 데코레이터에서 검증됨

    base_dir = os.path.join('logs', 'token_logs')
    if not os.path.isdir(base_dir):
        return success({"by_day": {}, "by_user": {}})

    by_day = {}
    by_user = {}

    def add(d: dict, key: str, field: str, val: int):
        if key not in d:
            d[key] = {"tokens": 0, "success": 0, "fail": 0, "events": 0}
        d[key][field] = d[key].get(field, 0) + val

    for name in os.listdir(base_dir):
        if not name.endswith('.log'):
            continue
        day = name[:-4]
        try:
            with open(os.path.join(base_dir, name), 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    user_id = str(rec.get('user_id', '0'))
                    tokens = int(rec.get('tokens', 0) or 0)
                    action = rec.get('action', '')

                    add(by_day, day, 'tokens', tokens)
                    add(by_day, day, 'events', 1)
                    add(by_user, user_id, 'tokens', tokens)
                    add(by_user, user_id, 'events', 1)
                    if action == 'convert_success':
                        add(by_day, day, 'success', 1)
                        add(by_user, user_id, 'success', 1)
                    if action == 'convert_fail':
                        add(by_day, day, 'fail', 1)
                        add(by_user, user_id, 'fail', 1)
        except Exception:
            continue

    return success({"by_day": by_day, "by_user": by_user})
