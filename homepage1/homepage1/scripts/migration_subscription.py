"""
Gold 등급 기간제 관리 시스템 - DB 마이그레이션
users 테이블에 subscription_end_date 컬럼 추가
"""

import os
import sys
import sqlite3

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 데이터베이스 경로
db_path = os.path.join(project_root, 'database', 'app.db')

def run_migration():
    """subscription_end_date 컬럼 추가 마이그레이션 실행"""
    if not os.path.exists(db_path):
        print(f"[오류] 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기존 컬럼 존재 여부 확인
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'subscription_end_date' in columns:
            print("[OK] subscription_end_date 컬럼이 이미 존재합니다.")
            conn.close()
            return True
        
        # 컬럼 추가
        print("[진행] subscription_end_date 컬럼 추가 중...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN subscription_end_date DATETIME
        """)
        
        conn.commit()
        conn.close()
        
        print("[완료] 마이그레이션 완료: subscription_end_date 컬럼이 추가되었습니다.")
        return True
        
    except sqlite3.Error as e:
        print(f"[오류] 마이그레이션 실패: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"[오류] 예상치 못한 오류: {str(e)}")
        if conn:
            conn.close()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Gold 등급 기간제 관리 시스템 - DB 마이그레이션")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print()
        print("[완료] 마이그레이션이 성공적으로 완료되었습니다.")
        sys.exit(0)
    else:
        print()
        print("[실패] 마이그레이션이 실패했습니다.")
        sys.exit(1)

