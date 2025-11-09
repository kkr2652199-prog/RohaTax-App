import sqlite3
import os
import sys

# --- 설정 ---
DB_PATH = 'database/app.db'
MIGRATIONS_DIR = 'database/migrations'

def apply_migrations():
    """
    migrations 디렉토리의 .sql 파일들을 데이터베이스에 순차적으로 적용합니다.
    """
    conn = None
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"데이터베이스 연결 성공: {DB_PATH}")

        # 마이그레이션 파일 목록 가져오기 및 정렬
        print(f"마이그레이션 디렉토리 검색: {MIGRATIONS_DIR}")
        sql_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])

        if not sql_files:
            print("적용할 새로운 마이그레이션 파일이 없습니다.")
            return

        print(f"총 {len(sql_files)}개의 마이그레이션 파일을 발견했습니다.")

        # 각 SQL 파일 실행
        for sql_file in sql_files:
            file_path = os.path.join(MIGRATIONS_DIR, sql_file)
            print(f"\n--- 적용 시작: {sql_file} ---")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                # executescript는 여러 SQL 문을 한 번에 실행할 수 있게 해줍니다.
                cursor.executescript(sql_script)
            
            print(f"--- 적용 성공: {sql_file} ---")

        # 모든 변경사항 커밋
        conn.commit()
        print("\n모든 마이그레이션이 성공적으로 적용되었으며, 변경사항이 커밋되었습니다.")

    except sqlite3.Error as e:
        print(f"\n[!!!] 데이터베이스 오류 발생: {e}", file=sys.stderr)
        if conn:
            print("오류 발생으로 모든 변경사항을 롤백합니다.")
            conn.rollback()
        sys.exit(1) # 오류 발생 시 스크립트 종료

    except FileNotFoundError as e:
        print(f"\n[!!!] 파일 또는 디렉토리 오류: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            print("데이터베이스 연결이 종료되었습니다.")

if __name__ == '__main__':
    apply_migrations()



