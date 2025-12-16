"""
마이그레이션 004 실행: payment_history 테이블에 previous_plan_type 컬럼 추가
"""
import sqlite3
import os

# 현재 스크립트 파일의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (homepage1)
project_root = os.path.join(current_dir, '..')
# 데이터베이스 경로
DATABASE = os.path.join(project_root, 'database', 'app.db')
# 마이그레이션 파일 경로
MIGRATION_FILE = os.path.join(project_root, 'database', 'migrations', '004_add_previous_plan_type.sql')

def run_migration():
    """마이그레이션 실행"""
    print("="*50)
    print("마이그레이션 004: previous_plan_type 컬럼 추가")
    print("="*50)
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 현재 컬럼 확인
        cursor.execute("PRAGMA table_info(payment_history)")
        cols = [row[1] for row in cursor.fetchall()]
        print(f"\n현재 컬럼: {cols}")
        
        has_previous_plan_type = 'previous_plan_type' in cols
        print(f"previous_plan_type 존재: {has_previous_plan_type}")
        
        if not has_previous_plan_type:
            print("\n[수정] previous_plan_type 컬럼 추가 중...")
            
            # 마이그레이션 파일 읽기
            with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # SQL 실행
            cursor.executescript(migration_sql)
            conn.commit()
            print("previous_plan_type 컬럼 추가 완료!")
        else:
            print("\n[확인] previous_plan_type 컬럼이 이미 존재합니다.")
        
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
    run_migration()

