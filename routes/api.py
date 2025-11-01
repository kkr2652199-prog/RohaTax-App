from flask import Blueprint, jsonify, request, session
from core.db import get_conn
import sqlite3
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/myhome-data')
def myhome_data():
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    limit = request.args.get('limit', 15, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort = (request.args.get('sort') or 'date').strip().lower()
    order = (request.args.get('order') or 'desc').strip().lower()
    order = 'asc' if order == 'asc' else 'desc'

    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            uid = session['user_id']

            # total count
            total_row = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM token_history
                WHERE user_id = ? AND COALESCE(json_extract(meta, '$.deleted'), 0) = 0
                """,
                (uid,)
            ).fetchone()
            total_count = total_row['cnt'] if total_row else 0

            # sort mapping
            # allowed: date(created_at), log_type(change_type), filename(meta.file_name), amount(amount), plan_type(users.plan_type)
            if sort in ('date', 'created_at', 'datetime'):
                order_by = f"th.created_at {order}, th.id {order}"
            elif sort in ('log_type', 'change_type'):
                order_by = f"th.change_type {order}, th.id {order}"
            elif sort in ('filename', 'file', 'file_name'):
                order_by = f"COALESCE(json_extract(th.meta, '$.file_name'), json_extract(th.meta, '$.file')) {order}, th.id {order}"
            elif sort in ('customer_name', 'customer'):
                order_by = f"COALESCE(json_extract(th.meta, '$.customer_name'), '') {order}, th.id {order}"
            elif sort in ('amount', 'change_amount'):
                order_by = f"th.amount {order}, th.id {order}"
            elif sort in ('plan_type',):
                order_by = f"u.plan_type {order}, th.id {order}"
            else:
                order_by = f"th.created_at {order}, th.id {order}"

            # page items with optional join for plan_type
            items = conn.execute(
                f"""
                SELECT th.id, th.change_type, th.amount, th.meta, th.created_at, u.plan_type
                FROM token_history th
                LEFT JOIN users u ON u.id = th.user_id
                WHERE th.user_id = ? AND COALESCE(json_extract(th.meta, '$.deleted'), 0) = 0
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (uid, limit, offset)
            ).fetchall()

            activity = []
            for r in items:
                # balance_after: 누적합 (해당 시점까지)
                bal = conn.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) as bal
                    FROM token_history
                    WHERE user_id = ?
                      AND COALESCE(json_extract(meta, '$.deleted'), 0) = 0
                      AND (created_at < ? OR (created_at = ? AND id <= ?))
                    """,
                    (uid, r['created_at'], r['created_at'], r['id'])
                ).fetchone()
                balance_after = bal['bal'] if bal else 0

                try:
                    meta_obj = json.loads(r['meta']) if r['meta'] else {}
                except Exception:
                    meta_obj = {}

                ct = (r['change_type'] or '').lower()
                if ct == 'use':
                    log_type = 'CONVERSION'
                elif ct == 'grant':
                    log_type = 'GRANT'
                elif ct == 'reset':
                    log_type = 'RESET'
                else:
                    log_type = (r['change_type'] or 'UNKNOWN').upper()

                # KST formatting
                # created_at assumed in UTC or local; we will parse and add +9 hours if it seems naive
                created_raw = r['created_at']
                dt_str = str(created_raw)
                try:
                    from datetime import datetime, timezone, timedelta
                    # try parse common formats
                    try:
                        dt = datetime.fromisoformat(dt_str.replace('Z','+00:00'))
                    except Exception:
                        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                        dt = dt.replace(tzinfo=timezone.utc)
                    kst = dt.astimezone(timezone(timedelta(hours=9)))
                    datetime_kst = kst.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    datetime_kst = dt_str

                amt = int(r['amount'] or 0)
                charge_amount = amt if amt > 0 else 0
                usage_amount = abs(amt) if amt < 0 else 0

                activity.append({
                    'id': int(r['id']),
                    'datetime_kst': datetime_kst,
                    'plan_type': r['plan_type'] or '',
                    'log_type': log_type,
                    'filename': meta_obj.get('file_name') or meta_obj.get('file') or None,
                    'customer_name': meta_obj.get('customer_name'),
                    'charge_amount': int(charge_amount),
                    'usage_amount': int(usage_amount),
                    'balance_after': int(balance_after or 0)
                })

            return jsonify({
                'success': True,
                'total_count': int(total_count),
                'activity_history': activity
            })

    except Exception as e:
        return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500


@api_bp.route('/myhome-data/delete', methods=['POST'])
def myhome_data_delete():
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    if not isinstance(ids, list) or not ids:
        return jsonify({'success': False, 'error': '삭제할 항목이 없습니다'}), 400

    try:
        with get_conn() as conn:
            for raw in ids:
                try:
                    th_id = int(raw)
                except Exception:
                    continue
                row = conn.execute(
                    "SELECT id, meta FROM token_history WHERE id = ? AND user_id = ?",
                    (th_id, session['user_id'])
                ).fetchone()
                if not row:
                    continue
                try:
                    m = json.loads(row['meta']) if row['meta'] else {}
                except Exception:
                    m = {}
                m['deleted'] = 1
                conn.execute(
                    "UPDATE token_history SET meta = ? WHERE id = ? AND user_id = ?",
                    (json.dumps(m, ensure_ascii=False), th_id, session['user_id'])
                )
            conn.commit()
        return jsonify({'success': True, 'deleted': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'삭제 중 오류: {str(e)}'}), 500

from flask import Blueprint, jsonify, request, session
from core.db import get_conn
import sqlite3
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/user/token-status')
def get_token_status():
    """실시간 토큰 상태 조회 API"""
    if not session.get('user_id'):
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                """
                SELECT 
                    id, username, token_balance, COALESCE(tokens_used, 0) as tokens_used,
                    created_at, plan_type, is_admin
                FROM users 
                WHERE id = ? AND COALESCE(is_deleted, 0) = 0
                """,
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return jsonify({'error': '사용자 정보를 찾을 수 없습니다'}), 404
            
            # 사용 가능한 토큰 계산
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
            
            # 토큰 사용률 계산
            total_tokens = user['token_balance'] or 0
            usage_percentage = (user['tokens_used'] / total_tokens * 100) if total_tokens > 0 else 0
            
            # 최근 사용 내역 조회
            recent_usage = conn.execute(
                """
                SELECT action, meta, created_at 
                FROM usage_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 5
                """,
                (session['user_id'],)
            ).fetchall()
            
            # 변환 로그 조회
            conversion_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_conversions,
                    AVG(conversion_time) as avg_conversion_time,
                    SUM(file_size) as total_file_size,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_conversions
                FROM conversion_logs 
                WHERE user_id = ?
                """,
                (session['user_id'],)
            ).fetchone()
            
            return jsonify({
                'success': True,
                'data': {
                    'user_info': {
                        'id': user['id'],
                        'username': user['username'],
                        'plan_type': user['plan_type'],
                        'is_admin': bool(user['is_admin']),
                        'created_at': user['created_at']
                    },
                    'token_status': {
                        'total_tokens': total_tokens,
                        'used_tokens': user['tokens_used'],
                        'available_tokens': available_tokens,
                        'usage_percentage': round(usage_percentage, 1)
                    },
                    'service_stats': {
                        'total_conversions': conversion_stats['total_conversions'] or 0,
                        'successful_conversions': conversion_stats['successful_conversions'] or 0,
                        'avg_conversion_time': round(conversion_stats['avg_conversion_time'] or 0, 2),
                        'total_file_size': conversion_stats['total_file_size'] or 0,
                        'success_rate': round(
                            (conversion_stats['successful_conversions'] / conversion_stats['total_conversions'] * 100) 
                            if conversion_stats['total_conversions'] > 0 else 0, 1
                        )
                    },
                    'recent_usage': [
                        {
                            'action': row['action'],
                            'meta': json.loads(row['meta']) if row['meta'] else {},
                            'created_at': row['created_at']
                        } for row in recent_usage
                    ],
                    'last_updated': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@api_bp.route('/user/usage-history')
def get_usage_history():
    """사용 내역 조회 API"""
    if not session.get('user_id'):
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 기간별 사용 통계
            period_stats = conn.execute(
                """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as daily_conversions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as daily_success,
                    AVG(conversion_time) as avg_time,
                    SUM(file_size) as daily_file_size
                FROM conversion_logs 
                WHERE user_id = ? AND created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                """,
                (session['user_id'],)
            ).fetchall()
            
            # 월별 토큰 사용량
            monthly_usage = conn.execute(
                """
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as conversions,
                    SUM(CASE WHEN meta LIKE '%token%' THEN 1 ELSE 0 END) as token_usage
                FROM usage_logs 
                WHERE user_id = ? AND created_at >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
                """,
                (session['user_id'],)
            ).fetchall()
            
            return jsonify({
                'success': True,
                'data': {
                    'daily_stats': [
                        {
                            'date': row['date'],
                            'conversions': row['daily_conversions'],
                            'success_rate': round(
                                (row['daily_success'] / row['daily_conversions'] * 100) 
                                if row['daily_conversions'] > 0 else 0, 1
                            ),
                            'avg_time': round(row['avg_time'] or 0, 2),
                            'file_size': row['daily_file_size'] or 0
                        } for row in period_stats
                    ],
                    'monthly_usage': [
                        {
                            'month': row['month'],
                            'conversions': row['conversions'],
                            'token_usage': row['token_usage']
                        } for row in monthly_usage
                    ]
                }
            })
            
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@api_bp.route('/admin/dashboard')
def admin_dashboard():
    """관리자 대시보드 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return jsonify({'error': '관리자 권한이 필요합니다'}), 403
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 전체 사용자 통계
            user_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
                    COUNT(CASE WHEN plan_type = 'vip' THEN 1 END) as vip_users,
                    COUNT(CASE WHEN created_at >= date('now', '-30 days') THEN 1 END) as new_users_30d
                FROM users 
                WHERE COALESCE(is_deleted, 0) = 0
                """
            ).fetchone()
            
            # 토큰 사용 통계
            token_stats = conn.execute(
                """
                SELECT 
                    SUM(token_balance) as total_tokens_issued,
                    SUM(COALESCE(tokens_used, 0)) as total_tokens_used,
                    AVG(token_balance - COALESCE(tokens_used, 0)) as avg_available_tokens
                FROM users 
                WHERE COALESCE(is_deleted, 0) = 0
                """
            ).fetchone()
            
            # 변환 통계
            conversion_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_conversions,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_conversions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_conversions,
                    AVG(conversion_time) as avg_conversion_time,
                    SUM(file_size) as total_file_size
                FROM conversion_logs 
                WHERE created_at >= date('now', '-30 days')
                """
            ).fetchone()
            
            # 최근 활동
            recent_activity = conn.execute(
                """
                SELECT 
                    u.username,
                    cl.original_filename,
                    cl.status,
                    cl.conversion_time,
                    cl.created_at
                FROM conversion_logs cl
                JOIN users u ON cl.user_id = u.id
                WHERE cl.created_at >= date('now', '-7 days')
                ORDER BY cl.created_at DESC
                LIMIT 20
                """
            ).fetchall()
            
            return jsonify({
                'success': True,
                'data': {
                    'user_stats': {
                        'total_users': user_stats['total_users'],
                        'active_users': user_stats['active_users'],
                        'vip_users': user_stats['vip_users'],
                        'new_users_30d': user_stats['new_users_30d']
                    },
                    'token_stats': {
                        'total_issued': token_stats['total_tokens_issued'] or 0,
                        'total_used': token_stats['total_tokens_used'] or 0,
                        'avg_available': round(token_stats['avg_available_tokens'] or 0, 1),
                        'usage_rate': round(
                            (token_stats['total_tokens_used'] / token_stats['total_tokens_issued'] * 100)
                            if token_stats['total_tokens_issued'] > 0 else 0, 1
                        )
                    },
                    'conversion_stats': {
                        'total_conversions': conversion_stats['total_conversions'],
                        'successful_conversions': conversion_stats['successful_conversions'],
                        'failed_conversions': conversion_stats['failed_conversions'],
                        'success_rate': round(
                            (conversion_stats['successful_conversions'] / conversion_stats['total_conversions'] * 100)
                            if conversion_stats['total_conversions'] > 0 else 0, 1
                        ),
                        'avg_conversion_time': round(conversion_stats['avg_conversion_time'] or 0, 2),
                        'total_file_size': conversion_stats['total_file_size'] or 0
                    },
                    'recent_activity': [
                        {
                            'username': row['username'],
                            'filename': row['original_filename'],
                            'status': row['status'],
                            'conversion_time': round(row['conversion_time'] or 0, 2),
                            'created_at': row['created_at']
                        } for row in recent_activity
                    ],
                    'last_updated': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

@api_bp.route('/user/refresh-tokens', methods=['POST'])
def refresh_tokens():
    """토큰 새로고침 API (관리자용)"""
    if not session.get('user_id') or not session.get('is_admin'):
        return jsonify({'error': '관리자 권한이 필요합니다'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        token_amount = data.get('token_amount', 100)
        
        if not user_id or not isinstance(token_amount, int) or token_amount <= 0:
            return jsonify({'error': '유효하지 않은 요청입니다'}), 400
        
        with get_conn() as conn:
            # 사용자 존재 확인
            user = conn.execute(
                "SELECT username FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
                (user_id,)
            ).fetchone()
            
            if not user:
                return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404
            
            # 토큰 추가
            conn.execute(
                "UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?",
                (token_amount, user_id)
            )
            
            # 사용 로그 기록
            conn.execute(
                "INSERT INTO usage_logs (user_id, action, meta) VALUES (?, ?, ?)",
                (user_id, 'token_refresh', json.dumps({
                    'amount': token_amount,
                    'admin_id': session['user_id'],
                    'timestamp': datetime.now().isoformat()
                }))
            )
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'{user["username"]}님에게 {token_amount}토큰이 추가되었습니다',
                'data': {
                    'user_id': user_id,
                    'token_amount': token_amount,
                    'admin_id': session['user_id'],
                    'timestamp': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500


@api_bp.route('/myhome-data')
def myhome_data():
    """마이홈 페이지용 요약/활동 데이터 제공 API
    반환:
    {
      success: true,
      token_summary: { total_granted, total_used, current_balance },
      activity_history: [ { date, log_type, filename, customer_name, change_amount, balance_after } ... ]
    }
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            uid = session['user_id']

            # 토큰 요약 (grant는 양수, use는 음수 가정; 없으면 부호 기준)
            sum_row = conn.execute(
                """
                SELECT 
                  COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS total_granted,
                  COALESCE(ABS(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END)), 0) AS total_used
                FROM token_history
                WHERE user_id = ?
                  AND (meta IS NULL OR meta NOT LIKE '%"deleted":1%')
                """,
                (uid,)
            ).fetchone()

            total_granted = sum_row['total_granted'] if sum_row else 0
            total_used = sum_row['total_used'] if sum_row else 0
            current_balance = total_granted - total_used

            # 최근 활동 내역 (최신 30건 예시)
            rows = conn.execute(
                """
                SELECT id, change_type, amount, meta, created_at
                FROM token_history
                WHERE user_id = ?
                  AND (meta IS NULL OR meta NOT LIKE '%"deleted":1%')
                ORDER BY created_at DESC, id DESC
                LIMIT 30
                """,
                (uid,)
            ).fetchall()

            activity = []
            for r in rows:
                # 해당 시점까지 누적 잔액 계산
                bal_row = conn.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS bal
                    FROM token_history
                    WHERE user_id = ?
                      AND (meta IS NULL OR meta NOT LIKE '%"deleted":1%')
                      AND (created_at < ? OR (created_at = ? AND id <= ?))
                    """,
                    (uid, r['created_at'], r['created_at'], r['id'])
                ).fetchone()

                balance_after = bal_row['bal'] if bal_row else 0

                # 메타 파싱
                meta_obj = {}
                try:
                    meta_obj = json.loads(r['meta']) if r['meta'] else {}
                except Exception:
                    meta_obj = {}

                # 표시용 매핑
                change_type = r['change_type'] or ''
                if change_type == 'use':
                    log_type = 'CONVERSION'
                elif change_type == 'grant':
                    log_type = 'GRANT'
                elif change_type == 'reset':
                    log_type = 'RESET'
                else:
                    log_type = change_type.upper() if change_type else 'UNKNOWN'

                activity.append({
                    'id': int(r['id']),
                    'date': r['created_at'],
                    'log_type': log_type,
                    'filename': meta_obj.get('file_name') or meta_obj.get('file') or None,
                    'customer_name': meta_obj.get('customer_name'),
                    'change_amount': int(r['amount'] or 0),
                    'balance_after': int(balance_after or 0)
                })

            return jsonify({
                'success': True,
                'token_summary': {
                    'total_granted': int(total_granted),
                    'total_used': int(total_used),
                    'current_balance': int(current_balance)
                },
                'activity_history': activity
            })

    except Exception as e:
        return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500


@api_bp.route('/myhome-data/delete', methods=['POST'])
def myhome_data_delete():
    """마이홈 활동 내역 일괄 삭제(소프트 삭제)
    body: { ids: [..] }
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    if not isinstance(ids, list) or not ids:
        return jsonify({'success': False, 'error': '삭제할 항목이 없습니다'}), 400

    try:
        with get_conn() as conn:
            for raw in ids:
                try:
                    th_id = int(raw)
                except Exception:
                    continue
                row = conn.execute(
                    "SELECT id, meta FROM token_history WHERE id = ? AND user_id = ?",
                    (th_id, session['user_id'])
                ).fetchone()
                if not row:
                    continue
                try:
                    m = json.loads(row['meta']) if row['meta'] else {}
                except Exception:
                    m = {}
                m['deleted'] = 1
                conn.execute(
                    "UPDATE token_history SET meta = ? WHERE id = ? AND user_id = ?",
                    (json.dumps(m, ensure_ascii=False), th_id, session['user_id'])
                )
            conn.commit()
        return jsonify({'success': True, 'deleted': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'삭제 중 오류: {str(e)}'}), 500