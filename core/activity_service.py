# core/activity_service.py

import sqlite3
import json
from typing import Dict, Any

def record_activity(cursor: sqlite3.Cursor, activity_data: Dict[str, Any]) -> None:
    """
    모든 종류의 사용자 활동을 activity_logs 테이블에 기록하고,
    필요한 경우 사용자의 토큰 잔액을 업데이트합니다.
    이 함수는 반드시 데이터베이스 트랜잭션 내에서 호출되어야 합니다.

    Args:
        cursor: 데이터베이스 작업을 위한 sqlite3.Cursor 객체.
        activity_data: 기록에 필요한 모든 정보를 담은 딕셔너리.
    """
    try:
        # 1. 로그 데이터 준비
        sql_log = """
            INSERT INTO activity_logs (
                user_id, timestamp, performed_by_id, performed_by_type, activity_type,
                details, token_change, potential_cost, token_balance_before,
                token_balance_after, user_plan_snapshot
            ) VALUES (?, strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_log, (
            activity_data.get('user_id'),
            activity_data.get('performed_by_id'),
            activity_data.get('performed_by_type'),
            activity_data.get('activity_type'),
            json.dumps(activity_data.get('details', {})),
            activity_data.get('token_change', 0),
            activity_data.get('potential_cost', 0),
            activity_data.get('token_balance_before'),
            activity_data.get('token_balance_after'),
            activity_data.get('user_plan_snapshot')
        ))
        
        # 2. 사용자 토큰 잔액 업데이트 (필요한 경우)
        token_change = activity_data.get('token_change', 0)
        activity_type = activity_data.get('activity_type', '')
        
        # 토큰 초기화의 경우 이미 reset_tokens()에서 모든 업데이트를 완료했으므로 여기서는 업데이트하지 않음
        if token_change != 0 and activity_type != 'TOKEN_RESET_BY_ADMIN':
            user_id = activity_data.get('user_id')
            token_balance_after = activity_data.get('token_balance_after')
            
            # 토큰 지급(양수)의 경우 tokens_used는 변경하지 않음
            # 토큰 사용(음수)의 경우만 tokens_used를 증가시킴
            if token_change < 0:
                # 토큰 사용: tokens_used 증가
                sql_update_user = "UPDATE users SET token_balance = ?, tokens_used = tokens_used + ? WHERE id = ?"
                cursor.execute(sql_update_user, (token_balance_after, abs(token_change), user_id))
            else:
                # 토큰 지급: token_balance만 업데이트
                sql_update_user = "UPDATE users SET token_balance = ? WHERE id = ?"
                cursor.execute(sql_update_user, (token_balance_after, user_id))
        
        print(f"[{activity_data.get('activity_type')}] 활동이 성공적으로 기록되었습니다.")

    except Exception as e:
        print(f"[Activity Service] ERROR: 활동 기록 중 예기치 않은 오류 발생: {e}")
        # 예외를 다시 발생시켜 상위 호출자가 트랜잭션을 롤백하도록 함
        raise
