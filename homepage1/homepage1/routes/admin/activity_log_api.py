import sqlite3

from flask import Blueprint, jsonify, request

from ..utils.auth import ensure_admin_for_json
from core.db import get_conn


activity_log_bp = Blueprint('activity_log_api', __name__, url_prefix='/admin/api')


@activity_log_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    """
    activity_logs 테이블의 데이터를 필터링 및 페이지네이션하여 조회합니다.
    
    Query Parameters:
        page: 페이지 번호 (기본값: 1)
        limit: 페이지당 항목 수 (기본값: 50)
        start_date: 시작 날짜
        end_date: 종료 날짜
        activity_type: 활동 유형 (단일)
        category: 카테고리 ('FINANCIAL', 'ACTIVITY', 'SECURITY')
        user_search: 사용자명 검색
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    # --- [수정 1] 프론트엔드로부터 검색 파라미터 수신 ---
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    activity_type = request.args.get('activity_type')
    category = request.args.get('category', '').upper()  # 카테고리 파라미터 추가
    user_search = request.args.get('user_search')
    offset = (page - 1) * limit

    # 카테고리별 활동 유형 매핑 (백엔드에서 정의)
    CATEGORY_TYPE_MAP = {
        'FINANCIAL': [
            'TOKEN_CHARGE', 'TOKEN_USE', 'TOKEN_GRANT_BY_ADMIN', 
            'TOKEN_RESET_BY_ADMIN', 'TOKEN_PURCHASE', 'PAYMENT_CANCEL',
            'GRADE_CHANGE', 'GRADE_CHANGE_BY_ADMIN', 'SUBSCRIPTION_UPDATE'
        ],
        'ACTIVITY': [
            'USER_LOGIN', 'USER_LOGOUT', 'FILE_CONVERT', 'PROFILE_UPDATE'
        ],
        'SECURITY': [
            'USER_SOFT_DELETE_BY_ADMIN', 'USER_RESTORE_BY_ADMIN', 
            'USER_PURGE_BY_ADMIN'
        ]
    }

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
            
            # 카테고리 및 활동 유형 필터 처리 (교집합 AND 조건)
            valid_types = None
            
            # 1. 카테고리로 유효한 타입 리스트 구하기
            if category and category in CATEGORY_TYPE_MAP:
                valid_types = CATEGORY_TYPE_MAP[category]
            
            # 2. activity_type이 지정되어 있는 경우
            if activity_type:
                if valid_types is not None:
                    # category와 activity_type이 모두 있는 경우: 교집합 확인
                    if activity_type in valid_types:
                        # activity_type이 category의 타입 리스트에 포함되면 해당 타입만 조회
                        valid_types = [activity_type]
                    else:
                        # activity_type이 category의 타입 리스트에 포함되지 않으면 빈 결과 반환
                        valid_types = []
                else:
                    # category가 없고 activity_type만 있는 경우: 해당 타입만 조회
                    valid_types = [activity_type]
            
            # 3. 최종 valid_types 리스트를 사용하여 SQL 조건 생성
            if valid_types is not None:
                if len(valid_types) == 0:
                    # 빈 리스트인 경우: 결과가 없도록 WHERE 절에 항상 false 조건 추가
                    where_clauses.append("1 = 0")
                elif len(valid_types) == 1:
                    # 단일 타입인 경우: = 조건 사용
                    where_clauses.append("al.activity_type = ?")
                    params.append(valid_types[0])
                else:
                    # 여러 타입인 경우: IN 조건 사용
                    placeholders = ','.join(['?' for _ in valid_types])
                    where_clauses.append(f"al.activity_type IN ({placeholders})")
                    params.extend(valid_types)
            
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


@activity_log_bp.route('/activity-logs/<int:log_id>', methods=['DELETE'])
def delete_activity_log(log_id: int):
    """
    활동 로그 삭제 (Hard Delete - 영구 삭제)
    
    Path Parameters:
        log_id: 삭제할 로그 ID
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        with get_conn() as conn:
            # 로그 존재 확인
            log_row = conn.execute(
                "SELECT id FROM activity_logs WHERE id = ?",
                (log_id,)
            ).fetchone()
            
            if not log_row:
                return jsonify({
                    "success": False,
                    "error": f"활동 로그를 찾을 수 없습니다: ID {log_id}"
                }), 404
            
            # Hard Delete (영구 삭제)
            cursor = conn.execute(
                "DELETE FROM activity_logs WHERE id = ?",
                (log_id,)
            )
            
            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "error": f"활동 로그 삭제에 실패했습니다: ID {log_id}"
                }), 500
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "활동 로그가 성공적으로 삭제되었습니다."
            }), 200
            
    except Exception as e:
        print(f"활동 로그 삭제 중 오류 발생: {e}")
        return jsonify({"success": False, "error": "서버 내부 오류가 발생했습니다."}), 500