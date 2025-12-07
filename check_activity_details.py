"""
활동 로그 상세 정보 확인
"""

import sqlite3
import json
from core.db import get_conn

def check_activity_details():
    """활동 로그의 details 필드 직접 확인"""
    print("=" * 80)
    print("활동 로그 상세 정보 (RAW)")
    print("=" * 80)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 최근 FILE_CONVERT 활동
        activities = conn.execute(
            """
            SELECT 
                al.id,
                al.user_id,
                u.username,
                al.activity_type,
                al.details,
                al.token_change,
                al.token_balance_before,
                al.token_balance_after,
                al.timestamp
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            WHERE al.activity_type = 'FILE_CONVERT'
            ORDER BY al.timestamp DESC
            LIMIT 3
            """
        ).fetchall()
        
        for i, act in enumerate(activities, 1):
            print(f"\n[{i}] 활동 ID: {act['id']}")
            print(f"    사용자: {act['username']} (ID: {act['user_id']})")
            print(f"    토큰 변경: {act['token_change']}")
            print(f"    토큰 잔액: {act['token_balance_before']} → {act['token_balance_after']}")
            print(f"    시간: {act['timestamp']}")
            print(f"    Details (RAW): {act['details']}")
            print(f"    Details 타입: {type(act['details'])}")
            
            # JSON 파싱 시도
            if act['details']:
                try:
                    details_dict = json.loads(act['details'])
                    print(f"    ✅ JSON 파싱 성공:")
                    for key, value in details_dict.items():
                        print(f"      - {key}: {value}")
                except json.JSONDecodeError as e:
                    print(f"    ❌ JSON 파싱 실패: {e}")
                except Exception as e:
                    print(f"    ❌ 오류: {e}")
            else:
                print(f"    ⚠️ Details가 비어있습니다!")

if __name__ == "__main__":
    check_activity_details()

