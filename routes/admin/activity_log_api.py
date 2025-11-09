import sqlite3

from flask import Blueprint, jsonify, request

from ..utils.auth import ensure_login_for_json
from core.db import get_conn


activity_log_bp = Blueprint('activity_log_api', __name__, url_prefix='/admin/api')


@activity_log_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    """
    activity_logs 테이블의 데이터를 필터링 및 페이지네이션하여 조회합니다.
    """
    user_id, guard_response = ensure_login_for_json()
    if not user_id:
        return guard_response

    # --- [수정 1] 프론트엔드로부터 검색 파라미터 수신 ---
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    activity_type = request.args.get('activity_type')
    user_search = request.args.get('user_search')
    offset = (page - 1) * limit

    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # --- [수정 2] 동적 WHERE 절 및 파라미터 생성 ---
            base_query = """
                SELECT
                    al.*,
                    COALESCE(target_user.username, '삭제된 사용자') as target_username,
                    COALESCE(actor_user.username, 'N/A') as actor_username
                FROM activity_logs al
                LEFT JOIN users target_user ON al.user_id = target_user.id
                LEFT JOIN users actor_user ON al.performed_by_id = actor_user.id
            """
            
            where_clauses = []
            params = []

            if start_date:
                where_clauses.append("al.timestamp >= ?")
                params.append(start_date)
            if end_date:
                # 날짜의 끝까지 포함하도록 + ' 23:59:59' 추가
                where_clauses.append("al.timestamp <= ?")
                params.append(f"{end_date} 23:59:59")
            if activity_type:
                where_clauses.append("al.activity_type = ?")
                params.append(activity_type)
            if user_search:
                where_clauses.append("(target_user.username LIKE ? OR actor_user.username LIKE ?)")
                params.extend([f"%{user_search}%", f"%{user_search}%"])

            # WHERE 절 조합
            if where_clauses:
                query_where = " WHERE " + " AND ".join(where_clauses)
            else:
                query_where = ""

            # 최종 쿼리 생성
            final_query = base_query + query_where + " ORDER BY al.timestamp DESC LIMIT ? OFFSET ?"
            final_params = params + [limit, offset]
            
            cursor.execute(final_query, tuple(final_params))
            logs = cursor.fetchall()
            result_logs = [dict(row) for row in logs]

            # --- [수정 3] 전체 카운트 쿼리도 동적으로 변경 ---
            count_query = "SELECT COUNT(al.id) FROM activity_logs al" + query_where
            # JOIN이 포함되었으므로, user_search를 위한 JOIN 추가
            if user_search:
                 count_query = """
                    SELECT COUNT(al.id)
                    FROM activity_logs al
                    LEFT JOIN users target_user ON al.user_id = target_user.id
                    LEFT JOIN users actor_user ON al.performed_by_id = actor_user.id
                 """ + query_where
            
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            return jsonify({
                "success": True,
                "data": {
                    "logs": result_logs,
                    "pagination": {
                        "total_items": total_count,
                        "current_page": page,
                        "items_per_page": limit,
                        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 0
                    }
                }
            }), 200

    except Exception as e:
        print(f"활동 로그 조회 중 오류 발생: {e}")
        return jsonify({"success": False, "error": "서버 내부 오류가 발생했습니다."}), 500
