import sqlite3
import json
from typing import Dict, Any

def record_conversion_activity(
    cursor: sqlite3.Cursor,
    user_info: Dict[str, Any],
    result_data: Dict[str, Any],
    file_name: str
) -> None:
    """
    파일 변환 활동이 성공했을 때, 관련된 모든 정보를 activity_logs 테이블에 기록하고
    사용자의 토큰 잔액을 업데이트합니다.

    이 함수는 반드시 데이터베이스 트랜잭션 내에서 호출되어야 합니다.

    Args:
        cursor: 데이터베이스 작업을 위한 sqlite3.Cursor 객체.
        user_info: 사용자 정보 딕셔너리. 'id', 'plan_type', 'token_balance' 키를 포함해야 함.
        result_data: 변환 결과 딕셔너리. 'total_recipients' 키를 포함해야 함.
        file_name: 변환된 원본 파일의 이름.
    """
    try:
        # 1. 정보 추출
        user_id = user_info['id']
        plan_type = user_info.get('plan_type', 'free')
        token_balance_before = user_info.get('token_balance', 0)
        total_recipients = result_data.get('total_recipients', 0)

        # 2. '경제 헌법' 적용
        # 참고: 현재 가격 정책이 미정이므로, '잠재적 비용'은 추출 건수 1개당 -1 토큰으로 가정합니다.
        # 이 부분은 나중에 실제 가격 정책 로직으로 교체될 수 있습니다.
        potential_cost = total_recipients * -1
        
        token_change = 0
        # 'unlimited' (골드) 플랜이 아닐 경우에만 토큰을 차감합니다.
        if plan_type != 'unlimited':
            token_change = potential_cost

        token_balance_after = token_balance_before + token_change

        # 3. 로그 데이터 준비
        activity_details = {
            "filename": file_name,
            "extracted_rows": total_recipients,
            "cost_policy": "1_token_per_row(temp)" # 임시 가격 정책 명시
        }

        log_data = {
            "user_id": user_id,
            "performed_by_id": user_id,
            "performed_by_type": "USER",
            "activity_type": "FILE_CONVERT",
            "details": json.dumps(activity_details),
            "token_change": token_change,
            "potential_cost": potential_cost,
            "token_balance_before": token_balance_before,
            "token_balance_after": token_balance_after,
            "user_plan_snapshot": plan_type
        }
        
        # 4. 데이터베이스 기록 (SQL Injection 방지를 위해 플레이스홀더 사용)
        sql_log = """
            INSERT INTO activity_logs (
                user_id, timestamp, performed_by_id, performed_by_type, activity_type,
                details, token_change, potential_cost, token_balance_before,
                token_balance_after, user_plan_snapshot
            ) VALUES (?, strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_log, (
            log_data['user_id'], log_data['performed_by_id'], log_data['performed_by_type'],
            log_data['activity_type'], log_data['details'], log_data['token_change'],
            log_data['potential_cost'], log_data['token_balance_before'],
            log_data['token_balance_after'], log_data['user_plan_snapshot']
        ))
        
        # 5. 사용자 토큰 잔액 업데이트는 TokenDeductionProcessor에서 처리하므로 여기서는 로그만 기록
        # (토큰 차감은 기존 TokenDeductionProcessor가 tokens_used를 증가시키는 방식으로 처리)
        # 주석: token_balance 직접 차감 방식과 tokens_used 증가 방식이 충돌하므로
        #       여기서는 활동 로그만 기록하고, 토큰 업데이트는 TokenDeductionProcessor에 위임
        
        print(f"[Activity Service] {user_id} 사용자의 파일 변환 활동이 성공적으로 기록되었습니다.")

    except KeyError as e:
        print(f"[Activity Service] ERROR: 필요한 키가 user_info 또는 result_data에 없습니다: {e}")
        # 이 함수는 트랜잭션의 일부이므로, 여기서 예외를 발생시켜 상위 호출자가 롤백하도록 합니다.
        raise
    except Exception as e:
        print(f"[Activity Service] ERROR: 활동 기록 중 예기치 않은 오류 발생: {e}")
        raise

