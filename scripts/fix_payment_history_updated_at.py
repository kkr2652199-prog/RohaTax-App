"""
긴급 수정: payment_history 테이블에 updated_at 컬럼 추가
"""
import sqlite3
import os

# 현재 스크립트 파일의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (homepage1)
project_root = os.path.join(current_dir, '..')
# 데이터베이스 경로
DATABASE = os.path.join(project_root, 'database', 'app.db')

def fix_updated_at_column():
    """payment_history 테이블에 updated_at 컬럼이 없으면 추가"""
    print("="*50)
    print("payment_history 테이블 updated_at 컬럼 확인 및 수정")
    print("="*50)
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 현재 컬럼 확인
        cursor.execute("PRAGMA table_info(payment_history)")
        cols = [row[1] for row in cursor.fetchall()]
        print(f"\n현재 컬럼: {cols}")
        
        has_updated_at = 'updated_at' in cols
        print(f"updated_at 존재: {has_updated_at}")
        
        if not has_updated_at:
            print("\n[수정] updated_at 컬럼 추가 중...")
            cursor.execute("""
                ALTER TABLE payment_history 
                ADD COLUMN updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
            """)
            conn.commit()
            print("updated_at 컬럼 추가 완료!")
        else:
            print("\n[확인] updated_at 컬럼이 이미 존재합니다.")
        
        # 최종 확인
        cursor.execute("PRAGMA table_info(payment_history)")
        cols_after = [row[1] for row in cursor.fetchall()]
        print(f"\n최종 컬럼: {cols_after}")
        print("="*50)
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류 발생: {e}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    fix_updated_at_column()




