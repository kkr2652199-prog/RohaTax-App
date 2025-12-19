#!/usr/bin/env python3
"""
SQLite → PostgreSQL 마이그레이션 스크립트

기능:
1. SQLite 데이터베이스에서 모든 테이블과 데이터를 읽어옴
2. PostgreSQL 데이터베이스에 동일한 스키마 생성
3. 모든 데이터를 안전하게 마이그레이션
4. 인덱스 및 제약조건 재생성
5. 마이그레이션 로그 기록

사용법:
    python scripts/migrate_to_postgresql.py \
        --sqlite-path database/app.db \
        --postgres-url postgresql://user:pass@host:5432/dbname \
        --dry-run  # 테스트 모드 (실제 마이그레이션 안 함)
"""

import os
import sys
import argparse
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# PostgreSQL 드라이버 (psycopg2 또는 psycopg2-binary)
try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2가 설치되지 않았습니다.")
    print("설치: pip install psycopg2-binary")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SQLiteToPostgreSQLMigrator:
    """SQLite에서 PostgreSQL로 마이그레이션하는 클래스"""
    
    def __init__(self, sqlite_path: str, postgres_url: str, dry_run: bool = False):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.dry_run = dry_run
        self.sqlite_conn = None
        self.postgres_conn = None
        
        # SQLite와 PostgreSQL 타입 매핑
        self.type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BLOB': 'BYTEA',
            'NUMERIC': 'NUMERIC',
            'BOOLEAN': 'BOOLEAN',
        }
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            # SQLite 연결
            if not os.path.exists(self.sqlite_path):
                raise FileNotFoundError(f"SQLite 파일을 찾을 수 없습니다: {self.sqlite_path}")
            
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✅ SQLite 연결 성공: {self.sqlite_path}")
            
            # PostgreSQL 연결
            if not self.dry_run:
                self.postgres_conn = psycopg2.connect(self.postgres_url)
                self.postgres_conn.autocommit = False
                logger.info("✅ PostgreSQL 연결 성공")
            else:
                logger.info("🔍 DRY-RUN 모드: 실제 마이그레이션은 수행하지 않습니다")
                
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
    
    def get_sqlite_tables(self) -> List[str]:
        """SQLite의 모든 테이블 목록 가져오기"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 발견된 테이블: {', '.join(tables)}")
        return tables
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """테이블 스키마 정보 가져오기"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        schema = {
            'columns': [],
            'primary_key': None,
            'foreign_keys': [],
            'indexes': []
        }
        
        for col in columns:
            col_info = {
                'name': col[1],
                'type': col[2],
                'not_null': col[3] == 1,
                'default': col[4],
                'primary_key': col[5] == 1
            }
            schema['columns'].append(col_info)
            
            if col_info['primary_key']:
                schema['primary_key'] = col_info['name']
        
        # 외래키 정보
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()
        for fk in fks:
            schema['foreign_keys'].append({
                'from': fk[3],  # column name
                'to_table': fk[2],  # referenced table
                'to_column': fk[4]  # referenced column
            })
        
        # 인덱스 정보
        cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = cursor.fetchall()
        for idx in indexes:
            if idx[0] and not idx[0].startswith('sqlite_'):
                schema['indexes'].append(idx[0])
        
        return schema
    
    def convert_sqlite_type_to_postgres(self, sqlite_type: str) -> str:
        """SQLite 타입을 PostgreSQL 타입으로 변환"""
        sqlite_type = sqlite_type.upper().split('(')[0]  # INTEGER(10) -> INTEGER
        
        # AUTOINCREMENT는 SERIAL로 변환
        if 'AUTOINCREMENT' in sqlite_type:
            return 'SERIAL'
        
        # 타입 매핑
        if sqlite_type in ['INTEGER', 'INT']:
            return 'INTEGER'
        elif sqlite_type in ['TEXT', 'VARCHAR', 'CHAR']:
            return 'TEXT'
        elif sqlite_type in ['REAL', 'FLOAT', 'DOUBLE']:
            return 'REAL'
        elif sqlite_type == 'BLOB':
            return 'BYTEA'
        elif sqlite_type == 'BOOLEAN':
            return 'BOOLEAN'
        else:
            return 'TEXT'  # 기본값
    
    def create_postgres_table(self, table_name: str, schema: Dict[str, Any]) -> str:
        """PostgreSQL 테이블 생성 SQL 생성"""
        columns = []
        
        for col in schema['columns']:
            col_def = f'"{col["name"]}" {self.convert_sqlite_type_to_postgres(col["type"])}'
            
            if col['primary_key']:
                col_def += ' PRIMARY KEY'
            elif col['not_null']:
                col_def += ' NOT NULL'
            
            if col['default']:
                # SQLite의 datetime('now')를 PostgreSQL의 CURRENT_TIMESTAMP로 변환
                default = col['default']
                if "datetime('now')" in default:
                    default = "CURRENT_TIMESTAMP"
                elif default == "'now'":
                    default = "CURRENT_TIMESTAMP"
                col_def += f" DEFAULT {default}"
            
            columns.append(col_def)
        
        # 외래키 제약조건 추가
        for fk in schema['foreign_keys']:
            fk_constraint = (
                f'CONSTRAINT fk_{table_name}_{fk["from"]} '
                f'FOREIGN KEY ("{fk["from"]}") '
                f'REFERENCES "{fk["to_table"]}"("{fk["to_column"]})'
            )
            columns.append(fk_constraint)
        
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    ' + ',\n    '.join(columns) + '\n);'
        return create_sql
    
    def migrate_table_data(self, table_name: str) -> int:
        """테이블 데이터 마이그레이션"""
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_sqlite.execute(f"SELECT * FROM {table_name}")
        rows = cursor_sqlite.fetchall()
        
        if not rows:
            logger.info(f"  ⚠️  {table_name}: 데이터 없음")
            return 0
        
        # 컬럼명 가져오기
        columns = [desc[0] for desc in cursor_sqlite.description]
        
        if self.dry_run:
            logger.info(f"  🔍 {table_name}: {len(rows)}개 행 (DRY-RUN)")
            return len(rows)
        
        # PostgreSQL에 데이터 삽입
        cursor_postgres = self.postgres_conn.cursor()
        
        # 배치 삽입 (성능 최적화)
        values = []
        for row in rows:
            row_dict = dict(row)
            values.append([row_dict.get(col) for col in columns])
        
        insert_sql = f'INSERT INTO "{table_name}" ({", ".join([f\'"{c}"\' for c in columns])}) VALUES %s'
        execute_values(cursor_postgres, insert_sql, values)
        
        self.postgres_conn.commit()
        logger.info(f"  ✅ {table_name}: {len(rows)}개 행 마이그레이션 완료")
        return len(rows)
    
    def create_indexes(self, table_name: str, indexes: List[str]):
        """인덱스 생성"""
        if not indexes:
            return
        
        if self.dry_run:
            logger.info(f"  🔍 {table_name}: 인덱스 {len(indexes)}개 (DRY-RUN)")
            return
        
        cursor = self.postgres_conn.cursor()
        
        for idx_name in indexes:
            try:
                # SQLite에서 인덱스 정의 가져오기
                cursor_sqlite = self.sqlite_conn.cursor()
                cursor_sqlite.execute(
                    f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{idx_name}'"
                )
                idx_sql = cursor_sqlite.fetchone()
                
                if idx_sql and idx_sql[0]:
                    # SQLite 인덱스 SQL을 PostgreSQL 형식으로 변환
                    idx_sql_postgres = idx_sql[0].replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                    idx_sql_postgres = idx_sql_postgres.replace(f'ON {table_name}', f'ON "{table_name}"')
                    # SQLite 특수 구문 제거
                    idx_sql_postgres = idx_sql_postgres.replace('IF NOT EXISTS idx_', 'idx_')
                    
                    cursor.execute(idx_sql_postgres)
                    logger.info(f"  ✅ 인덱스 생성: {idx_name}")
            except Exception as e:
                logger.warning(f"  ⚠️  인덱스 생성 실패 ({idx_name}): {e}")
        
        self.postgres_conn.commit()
    
    def migrate(self):
        """전체 마이그레이션 실행"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 SQLite → PostgreSQL 마이그레이션 시작")
            logger.info("=" * 60)
            
            # 1. 테이블 목록 가져오기
            tables = self.get_sqlite_tables()
            
            if not tables:
                logger.warning("⚠️  마이그레이션할 테이블이 없습니다")
                return
            
            total_rows = 0
            
            # 2. 각 테이블 마이그레이션
            for table_name in tables:
                logger.info(f"\n📦 테이블 처리: {table_name}")
                
                # 스키마 가져오기
                schema = self.get_table_schema(table_name)
                
                # PostgreSQL 테이블 생성
                create_sql = self.create_postgres_table(table_name, schema)
                
                if not self.dry_run:
                    cursor = self.postgres_conn.cursor()
                    cursor.execute(create_sql)
                    self.postgres_conn.commit()
                    logger.info(f"  ✅ 테이블 생성 완료: {table_name}")
                else:
                    logger.info(f"  🔍 테이블 생성 SQL (DRY-RUN):\n{create_sql}")
                
                # 데이터 마이그레이션
                rows = self.migrate_table_data(table_name)
                total_rows += rows
                
                # 인덱스 생성
                self.create_indexes(table_name, schema['indexes'])
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ 마이그레이션 완료!")
            logger.info(f"   - 테이블: {len(tables)}개")
            logger.info(f"   - 총 행: {total_rows}개")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 실패: {e}", exc_info=True)
            if self.postgres_conn:
                self.postgres_conn.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description='SQLite → PostgreSQL 마이그레이션')
    parser.add_argument('--sqlite-path', required=True, help='SQLite 데이터베이스 파일 경로')
    parser.add_argument('--postgres-url', required=True, help='PostgreSQL 연결 URL (postgresql://user:pass@host:5432/dbname)')
    parser.add_argument('--dry-run', action='store_true', help='테스트 모드 (실제 마이그레이션 안 함)')
    
    args = parser.parse_args()
    
    migrator = SQLiteToPostgreSQLMigrator(
        sqlite_path=args.sqlite_path,
        postgres_url=args.postgres_url,
        dry_run=args.dry_run
    )
    
    try:
        migrator.connect()
        migrator.migrate()
    finally:
        migrator.close()


if __name__ == '__main__':
    main()

