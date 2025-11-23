import sqlite3
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
db_path = project_root / "database" / "app.db"

def check_activity_logs():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 전체 레코드 수
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        total_count = cursor.fetchone()[0]
        print(f"[확인] activity_logs 테이블 전체 레코드 수: {total_count}")
        
        # USER_LOGIN 활동 로그 수
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE activity_type = ?", ('USER_LOGIN',))
        login_count = cursor.fetchone()[0]
        print(f"[확인] USER_LOGIN 활동 로그 수: {login_count}")
        
        # 최근 USER_LOGIN 로그 5개
        cursor.execute("""
            SELECT id, user_id, activity_type, timestamp, details 
            FROM activity_logs 
            WHERE activity_type = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, ('USER_LOGIN',))
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n[최근 USER_LOGIN 로그 5개]:")
            for row in rows:
                print(f"  ID: {row[0]}, User ID: {row[1]}, Type: {row[2]}, Time: {row[3]}, Details: {row[4]}")
        else:
            print("\n[확인] USER_LOGIN 로그가 없습니다.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[오류] 테이블 확인 중 오류 발생: {str(e)}")
        return False

if __name__ == '__main__':
    check_activity_logs()

