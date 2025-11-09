import sqlite3

from flask import Blueprint, jsonify, request

from ..utils.auth import ensure_login_for_json
from core.db import get_conn


# --- 새로운 Blueprint 생성 ---
# 이 API와 관련된 모든 경로는 '/admin/api' 로 시작됩니다.
activity_log_bp = Blueprint('activity_log_api', __name__, url_prefix='/admin/api')


@activity_log_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    """
    activity_logs 테이블의 데이터를 페이지네이션하여 조회합니다.
    users 테이블과 JOIN하여 사용자 이름도 함께 반환합니다.
    """
    # 관리자 로그인 여부 확인
    user_id, guard_response = ensure_login_for_json()
    if not user_id:
        return guard_response

    # 페이지네이션 파라미터 처리
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    offset = (page - 1) * limit

    conn = None
    try:
        with get_conn() as conn:
            # 컬럼 이름으로 결과에 접근할 수 있도록 row_factory 설정
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # --- 핵심 SQL 쿼리 ---
            # activity_logs(al)를 기준으로, users 테이블과 두 번 LEFT JOIN 합니다.
            # 1. 대상 사용자 (target_user): al.user_id -> users.id
            # 2. 활동 주체 (actor_user): al.performed_by_id -> users.id
            # COALESCE 함수는 사용자가 삭제되었을 경우(NULL)를 대비한 안전장치입니다.
            query = """
                SELECT
                    al.*,
                    COALESCE(target_user.username, '삭제된 사용자') as target_username,
                    COALESCE(actor_user.username, 'N/A') as actor_username
                FROM
                    activity_logs al
                LEFT JOIN
                    users target_user ON al.user_id = target_user.id
                LEFT JOIN
                    users actor_user ON al.performed_by_id = actor_user.id
                ORDER BY
                    al.timestamp DESC
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, (limit, offset))
            logs = cursor.fetchall()
            
            # sqlite3.Row 객체를 JSON으로 변환하기 쉬운 딕셔너리 리스트로 변환
            result_logs = [dict(row) for row in logs]

            # 전체 로그 수량도 함께 조회하여 프론트엔드에서 페이지네이션 구현을 돕습니다.
            total_count_query = "SELECT COUNT(*) FROM activity_logs"
            cursor.execute(total_count_query)
            total_count = cursor.fetchone()[0]

            return jsonify({
                "success": True,
                "data": {
                    "logs": result_logs,
                    "pagination": {
                        "total_items": total_count,
                        "current_page": page,
                        "items_per_page": limit,
                        "total_pages": (total_count + limit - 1) // limit
                    }
                }
            }), 200

    except sqlite3.Error as e:
        # 데이터베이스 오류 발생 시
        print(f"데이터베이스 오류: {e}")
        return jsonify({"success": False, "error": "데이터베이스 오류가 발생했습니다."}), 500
    except Exception as e:
        # 기타 서버 오류 발생 시
        print(f"서버 오류: {e}")
        return jsonify({"success": False, "error": "서버 내부 오류가 발생했습니다."}), 500



