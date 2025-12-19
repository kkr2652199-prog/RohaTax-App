import sqlite3
import os
import shutil
from datetime import datetime
from typing import Iterator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'backups')


def _ensure_backup_dir():
    """백업 디렉토리 생성"""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def _check_db_integrity() -> bool:
    """데이터베이스 무결성 검사"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        return result[0] == "ok"
    except Exception as e:
        print(f"❌ DB 무결성 검사 실패: {e}")
        return False


def _backup_corrupted_db():
    """손상된 DB 백업"""
    if not os.path.exists(DB_PATH):
        return
    
    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"corrupted_db_{timestamp}.db")
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"💾 손상된 DB 백업 완료: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ DB 백업 실패: {e}")
        return None


def _recreate_db():
    """DB 재생성"""
    try:
        # 기존 DB 파일 제거
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("🗑️ 손상된 DB 파일 제거")
        
        # 새 DB 생성 및 초기화
        init_db()
        print("✅ DB 재생성 완료")
        return True
    except Exception as e:
        print(f"❌ DB 재생성 실패: {e}")
        return False


def get_conn() -> sqlite3.Connection:
    """데이터베이스 연결 (무결성 검사 포함) - 레거시 함수"""
    # DB 파일이 없으면 생성
    if not os.path.exists(DB_PATH):
        logger.info("📁 DB 파일이 없어 초기화합니다")
        init_db()
        return sqlite3.connect(DB_PATH, check_same_thread=False)
    
    # 무결성 검사
    if not _check_db_integrity():
        logger.warning("⚠️ DB 무결성 검사 실패 - 복구를 시도합니다")
        
        # 백업 생성
        backup_path = _backup_corrupted_db()
        
        # DB 재생성
        if _recreate_db():
            logger.info("✅ DB 복구 완료")
        else:
            logger.error("❌ DB 복구 실패 - 서버를 재시작해주세요")
            raise sqlite3.DatabaseError("Database corruption detected and recovery failed")
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # 성능 최적화 설정 적용
    _apply_performance_settings(conn)
    
    return conn

@contextmanager
def get_conn_optimized():
    """최적화된 데이터베이스 연결 컨텍스트 매니저"""
    conn = None
    try:
        # DB 파일이 없으면 생성
        if not os.path.exists(DB_PATH):
            logger.info("📁 DB 파일이 없어 초기화합니다")
            init_db()
        
        # 무결성 검사
        if not _check_db_integrity():
            logger.warning("⚠️ DB 무결성 검사 실패 - 복구를 시도합니다")
            
            # 백업 생성
            backup_path = _backup_corrupted_db()
            
            # DB 재생성
            if _recreate_db():
                logger.info("✅ DB 복구 완료")
            else:
                logger.error("❌ DB 복구 실패 - 서버를 재시작해주세요")
                raise sqlite3.DatabaseError("Database corruption detected and recovery failed")
        
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # 성능 최적화 설정 적용
        _apply_performance_settings(conn)
        
        yield conn
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise
    finally:
        if conn:
            conn.close()

def _apply_performance_settings(conn: sqlite3.Connection):
    """데이터베이스 성능 최적화 설정 적용"""
    try:
        # WAL 모드로 성능 향상
        conn.execute("PRAGMA journal_mode=WAL")
        
        # 동기화 최적화
        conn.execute("PRAGMA synchronous=NORMAL")
        
        # 캐시 크기 증가
        conn.execute("PRAGMA cache_size=10000")
        
        # 임시 테이블을 메모리에 저장
        conn.execute("PRAGMA temp_store=MEMORY")
        
        # 메모리 맵 크기 설정 (256MB)
        conn.execute("PRAGMA mmap_size=268435456")
        
        # 외래키 제약 조건 활성화
        conn.execute("PRAGMA foreign_keys = ON")
        
        logger.debug("데이터베이스 성능 최적화 설정 적용 완료")
        
    except sqlite3.Error as e:
        logger.warning(f"성능 최적화 설정 적용 실패: {e}")


def init_db() -> None:
    """데이터베이스 초기화 및 성능 최적화"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        conn.executescript(schema)
        
        # 성능 최적화 인덱스 생성
        _create_performance_indexes(conn)
        
        # 마이그레이션 자동 적용
        _apply_migrations(conn)
        
        conn.commit()
        logger.info("데이터베이스 초기화 및 성능 최적화 완료")
        # Add soft-delete columns if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN deleted_at TEXT")
        except Exception:
            pass
        # Add token_balance column if it doesn't exist
        try:
            conn.execute("ALTER TABLE users ADD COLUMN token_balance INTEGER DEFAULT 0")
        except Exception:
            pass
        # Add password column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN password TEXT")
        except Exception:
            pass
        # Add is_admin column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        # Add tokens_used column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN tokens_used INTEGER DEFAULT 0")
        except Exception:
            pass
        # Add business_number column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN business_number TEXT UNIQUE")
        except Exception:
            pass
        # Add representative_name column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN representative_name TEXT")
        except Exception:
            pass
        # Add phone column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        except Exception:
            pass
        # Add terms agreement columns if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN terms_agreed INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN privacy_agreed INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN terms_agreed_at TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN privacy_agreed_at TEXT")
        except Exception:
            pass
        # Add address column if missing (replace referral_code)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN address TEXT")
        except Exception:
            pass
        # Add approval_status column if missing
        try:
            conn.execute("ALTER TABLE users ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'pending'")
        except Exception:
            pass
        # Add validation_logs table if missing
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS validation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                validation_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                errors TEXT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")
        except Exception:
            pass

        # Add token_history table if missing
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS token_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    changed_by INTEGER,
                    amount INTEGER NOT NULL,
                    change_type TEXT NOT NULL, -- grant, use, reset, revoke
                    meta TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(changed_by) REFERENCES users(id)
                )
                """
            )
        except Exception:
            pass


def seed_demo() -> None:
    with get_conn() as conn:
        # Ensure admin user exists with all required fields
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("kweon4309",)).fetchone()
        if not admin:
            conn.execute(
                "INSERT INTO users (username, email, password, company_name, plan_type, monthly_limit, used_count, is_active, is_admin, token_balance, approval_status, business_number, representative_name, address, phone, business_type, business_category) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("kweon4309", "admin@example.com", "1234", "관리자", "unlimited", 0, 0, 1, 1, 999999, "approved", "9999999999", "관리자", "서울시 강남구", "02-1234-5678", "정보통신업", "소프트웨어개발")
            )
        else:
            # 기존 관리자 계정의 필수 필드 업데이트
            conn.execute("""
                UPDATE users SET 
                    business_number = COALESCE(business_number, '9999999999'),
                    representative_name = COALESCE(representative_name, '관리자'),
                    address = COALESCE(address, '서울시 강남구'),
                    phone = COALESCE(phone, '02-1234-5678'),
                    business_type = COALESCE(business_type, '정보통신업'),
                    business_category = COALESCE(business_category, '소프트웨어개발'),
                    company_name = COALESCE(company_name, '관리자')
                WHERE username = 'kweon4309' AND (
                    business_number IS NULL OR 
                    representative_name IS NULL OR 
                    address IS NULL
                )
            """)
        conn.commit()

def _apply_migrations(conn: sqlite3.Connection):
    """마이그레이션 파일들을 자동으로 적용"""
    migrations_dir = os.path.join(os.path.dirname(DB_PATH), 'migrations')
    
    # migrations 디렉토리가 없으면 생성
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir, exist_ok=True)
        logger.info(f"마이그레이션 디렉토리 생성: {migrations_dir}")
        return
    
    # 마이그레이션 파일 목록 가져오기 및 정렬
    try:
        sql_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        if not sql_files:
            logger.debug("적용할 마이그레이션 파일이 없습니다.")
            return
        
        logger.info(f"마이그레이션 파일 {len(sql_files)}개 발견: {', '.join(sql_files)}")
        
        # 각 SQL 파일 실행
        for sql_file in sql_files:
            file_path = os.path.join(migrations_dir, sql_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    # executescript는 여러 SQL 문을 한 번에 실행할 수 있게 해줍니다.
                    conn.executescript(sql_script)
                logger.info(f"마이그레이션 적용 완료: {sql_file}")
            except sqlite3.Error as e:
                # 테이블이 이미 존재하는 경우는 무시 (CREATE TABLE IF NOT EXISTS)
                if "already exists" not in str(e).lower():
                    logger.warning(f"마이그레이션 적용 중 오류 ({sql_file}): {e}")
            except Exception as e:
                logger.warning(f"마이그레이션 파일 읽기 실패 ({sql_file}): {e}")
                
    except Exception as e:
        logger.warning(f"마이그레이션 적용 중 오류: {e}")


def _create_performance_indexes(conn: sqlite3.Connection):
    """성능 최적화를 위한 인덱스 생성"""
    try:
        # 사용자 테이블 인덱스
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_business_number ON users(business_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_plan_type ON users(plan_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_token_balance ON users(token_balance)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_tokens_used ON users(tokens_used)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
        
        # 사용 로그 테이블 인덱스
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_action ON usage_logs(action)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)")
        
        # 변환 로그 테이블 인덱스
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_id ON conversion_logs(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversion_logs_status ON conversion_logs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversion_logs_created_at ON conversion_logs(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversion_logs_file_size ON conversion_logs(file_size)")
        
        # 복합 인덱스 (자주 함께 사용되는 컬럼들)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_active_plan ON users(is_active, plan_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_token_status ON users(token_balance, tokens_used)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_user_action ON usage_logs(user_id, action)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_status ON conversion_logs(user_id, status)")
        
        logger.info("성능 최적화 인덱스 생성 완료")
        
    except sqlite3.Error as e:
        logger.warning(f"인덱스 생성 실패: {e}")

def optimize_database():
    """데이터베이스 최적화 실행"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            # 통계 정보 업데이트
            conn.execute("ANALYZE")
            
            # 데이터베이스 압축
            conn.execute("VACUUM")
            
            logger.info("데이터베이스 최적화 완료")
            
    except sqlite3.Error as e:
        logger.error(f"데이터베이스 최적화 실패: {e}")

def get_query_performance_stats():
    """쿼리 성능 통계 조회"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            # 테이블별 통계 정보 조회
            stats = conn.execute("""
                SELECT 
                    name as table_name,
                    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=name) as index_count,
                    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=name) as row_count
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            
            return [dict(row) for row in stats]
            
    except sqlite3.Error as e:
        logger.error(f"성능 통계 조회 실패: {e}")
        return []

