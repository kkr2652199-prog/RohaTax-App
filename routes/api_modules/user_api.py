from flask import Blueprint, jsonify, request, session
from core.db import get_conn_optimized as get_conn
from core.token_service import get_token_status_from_activity_log
import sqlite3
import json
from datetime import datetime

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api')


@user_api_bp.route('/myhome-data')
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

            # 사용자 plan_type 조회 (중복 제거: 한 번만 조회)
            user_row = conn.execute(
                "SELECT plan_type FROM users WHERE id = ?",
                (uid,)
            ).fetchone()
            base_plan_type = (user_row['plan_type'] or '').upper() if user_row else ''

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

            # page items with optional join for plan_type and balance_after (윈도우 함수로 N+1 문제 해결)
            # 윈도우 함수를 사용하여 각 행의 balance_after를 한 번의 쿼리로 계산
            # balance_after는 시간 순서(created_at, id)로 계산되어야 하므로, 윈도우 함수의 정렬은 항상 시간 순서로 고정
            # 최종 결과는 사용자가 요청한 정렬 순서(order_by)로 정렬됨
            items = conn.execute(
                f"""
                SELECT 
                    th.id, 
                    th.change_type, 
                    th.amount, 
                    th.meta, 
                    th.created_at, 
                    u.plan_type,
                    COALESCE(SUM(th.amount) OVER (
                        PARTITION BY th.user_id 
                        ORDER BY th.created_at, th.id 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ), 0) as balance_after
                FROM token_history th
                LEFT JOIN users u ON u.id = th.user_id
                WHERE th.user_id = ? 
                  AND COALESCE(json_extract(th.meta, '$.deleted'), 0) = 0
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (uid, limit, offset)
            ).fetchall()

            activity = []
            for r in items:
                # balance_after는 이미 쿼리에서 계산되어 있음 (N+1 문제 해결)
                balance_after = r['balance_after'] if r['balance_after'] is not None else 0

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


@user_api_bp.route('/myhome-data/delete', methods=['POST'])
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

@user_api_bp.route('/user/token-status')
def get_token_status():
    """실시간 토큰 상태 조회 API (표준 법률: activity_logs 기반)"""
    if not session.get('user_id'):
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    try:
        from datetime import datetime
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user_id = session.get('user_id')
            
            # 사용자 기본 정보 조회
            user = conn.execute(
                """
                SELECT 
                    id, username, created_at, plan_type, is_admin
                FROM users 
                WHERE id = ? AND COALESCE(is_deleted, 0) = 0
                """,
                (user_id,)
            ).fetchone()
            
            if not user:
                return jsonify({'error': '사용자 정보를 찾을 수 없습니다'}), 404
            
            # 표준 법률: activity_logs 기반 토큰 계산 (중앙은행 함수 사용)
            token_status = get_token_status_from_activity_log(user_id)
            if not token_status:
                return jsonify({'error': '토큰 상태를 확인할 수 없습니다'}), 500
            
            # 중앙은행 함수로부터 계산된 토큰 값
            total_tokens = token_status['token_balance']
            used_tokens = token_status['tokens_used']
            available_tokens = token_status['available_tokens']
            
            # 토큰 사용률 계산
            usage_percentage = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0
            
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

@user_api_bp.route('/user/usage-history')
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

@user_api_bp.route('/user/refresh-tokens', methods=['POST'])
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


@user_api_bp.route('/v2/user/token-summary')
def get_token_summary_v2():
    """
    '가장 최근 리셋' 이후의 activity_logs를 기준으로
    '누적 충전량', '누적 사용량', '현재 잔량'을 정확하게 계산하여 제공하는 최종 API
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    user_id = session.get('user_id')

    try:
        from datetime import datetime
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 이 쿼리가 이 작전의 핵심이다.
            # WITH 구문을 사용하여 가장 최근의 리셋 시간을 먼저 찾고,
            # 그 시간을 기준으로 데이터를 필터링하여 집계한다.
            summary = conn.execute(
                """
                WITH last_reset AS (
                    -- 1. 가장 최근의 TOKEN_RESET_BY_ADMIN 이벤트의 timestamp를 찾는다.
                    SELECT MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0  -- [버그 수정] 삭제된 레코드 제외
                )
                SELECT
                    -- 2. 해당 리셋 시간 이후의 모든 로그만을 대상으로 집계한다.
                    -- 단, TOKEN_RESET_BY_ADMIN의 token_change는 사용량 계산에서 제외한다.
                    COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
                    COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
                FROM activity_logs al, last_reset lr
                WHERE al.user_id = ?
                  AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
                  AND COALESCE(al.is_deleted, 0) = 0;  -- [버그 수정] 삭제된 레코드 제외
                -- 만약 리셋 기록이 없다면 (lr.reset_time IS NULL), 모든 로그를 포함한다.
                """,
                (user_id, user_id)
            ).fetchone()

            total_tokens = summary['total_charged']
            used_tokens = summary['total_used']
            available_tokens = total_tokens - used_tokens

            return jsonify({
                'success': True,
                'data': {
                    'total_tokens': int(total_tokens),
                    'used_tokens': int(used_tokens),
                    'available_tokens': int(available_tokens)
                },
                'last_updated': datetime.now().isoformat()
            })

    except Exception as e:
        print(f"Error in get_token_summary_v2: {e}")
        return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500


@user_api_bp.route('/v2/user/activity-logs')
def get_user_activity_logs_v2():
    """
    '가장 최근 리셋' 이후의 모든 activity_logs를 시간순(ASC)으로 제공하는 API
    데이터 번역 시스템을 포함하여 사용자 친화적인 형태로 변환
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401

    user_id = session.get('user_id')

    # 활동 유형 번역 사전
    ACTIVITY_TYPE_MAP = {
        "TOKEN_GRANT_BY_ADMIN": "토큰 지급 (관리자)",
        "TOKEN_RESET_BY_ADMIN": "토큰 초기화 (관리자)",
        "FILE_CONVERT": "파일 변환",
        "GRADE_CHANGE_BY_ADMIN": "등급 변경 (관리자)",
        "TOKEN_USE": "토큰 사용",
        "TOKEN_CHARGE": "토큰 충전",
        "LOGIN": "로그인",
        "LOGOUT": "로그아웃",
        "PROFILE_UPDATE": "프로필 수정"
    }

    def translate_activity_type(activity_type):
        """활동 유형을 한글로 번역"""
        return ACTIVITY_TYPE_MAP.get(activity_type, activity_type)

    def summarize_details(activity_type, details_str):
        """상세 정보를 요약 문장으로 변환"""
        if not details_str:
            return '세부 정보 없음'
        
        try:
            details = json.loads(details_str) if isinstance(details_str, str) else details_str
            
            if activity_type == 'TOKEN_GRANT_BY_ADMIN':
                amount = details.get('granted_amount', 0)
                return f"{amount} 토큰 지급"
            
            elif activity_type == 'TOKEN_RESET_BY_ADMIN':
                return "토큰 잔액 초기화"
            
            elif activity_type == 'FILE_CONVERT':
                filename = details.get('filename', '파일')
                rows = details.get('extracted_rows', 0)
                return f"{filename} ({rows}건)"
            
            elif activity_type == 'GRADE_CHANGE_BY_ADMIN':
                old_plan = details.get('old_plan', '')
                new_plan = details.get('new_plan', '')
                return f"{old_plan} → {new_plan}"
            
            elif activity_type == 'TOKEN_USE':
                amount = details.get('amount', 0)
                return f"{amount} 토큰 사용"
            
            elif activity_type == 'TOKEN_CHARGE':
                amount = details.get('amount', 0)
                return f"{amount} 토큰 충전"
            
            elif activity_type == 'PROFILE_UPDATE':
                fields = details.get('updated_fields', [])
                if fields:
                    return f"{', '.join(fields)} 수정"
                return "프로필 정보 수정"
            
            else:
                # 기본적으로 JSON을 문자열로 반환하되, 주요 필드만 추출
                if isinstance(details, dict):
                    # 주요 필드가 있으면 표시
                    if 'amount' in details:
                        return f"금액: {details['amount']}"
                    elif 'filename' in details:
                        return f"파일: {details['filename']}"
                    return str(details)
                return str(details)
                
        except (json.JSONDecodeError, TypeError, AttributeError):
            # JSON 파싱 실패 시 원본 문자열 반환 (너무 길면 잘라서)
            if isinstance(details_str, str) and len(details_str) > 50:
                return details_str[:50] + "..."
            return str(details_str) if details_str else '세부 정보 없음'

    try:
        from datetime import datetime
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # WITH 구문을 사용하여 가장 최근의 리셋 시간을 먼저 찾고,
            # 그 시간을 기준으로 데이터를 필터링하여 시간순으로 정렬한다.
            logs = conn.execute(
                """
                WITH last_reset AS (
                    SELECT MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0  -- [버그 수정] 삭제된 레코드 제외
                )
                SELECT
                    al.id,  -- [추가] 프론트엔드 삭제 기능에 필요
                    al.timestamp,
                    al.user_plan_snapshot,
                    al.activity_type,
                    al.details,
                    al.token_change,
                    al.token_balance_before,
                    al.token_balance_after
                FROM activity_logs al, last_reset lr
                WHERE al.user_id = ?
                  AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
                  AND COALESCE(al.is_deleted, 0) = 0  -- [버그 수정] 삭제되지 않은 레코드만 조회
                ORDER BY al.timestamp ASC;
                """,
                (user_id, user_id)
            ).fetchall()

            # 결과를 Python dict 리스트로 변환하고 번역 적용
            result_logs = []
            for log in logs:
                log_dict = dict(log)
                # 활동 유형 번역
                log_dict['activity_type_korean'] = translate_activity_type(log_dict['activity_type'])
                # 상세 정보 요약
                log_dict['details_summary'] = summarize_details(log_dict['activity_type'], log_dict['details'])
                result_logs.append(log_dict)

            return jsonify({
                'success': True,
                'data': result_logs
            })

    except Exception as e:
        print(f"Error in get_user_activity_logs_v2: {e}")
        return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500


