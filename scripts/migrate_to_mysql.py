#!/usr/bin/env python3
"""
SQLite → MySQL 마이그레이션 스크립트

기능:
1. SQLite 데이터베이스에서 모든 테이블과 데이터를 읽어옴
2. MySQL 데이터베이스에 동일한 스키마 생성
3. 모든 데이터를 안전하게 마이그레이션
4. 인덱스 및 제약조건 재생성

사용법:
    python scripts/migrate_to_mysql.py \
        --sqlite-path database/app.db \
        --mysql-host localhost \
        --mysql-user root \
        --mysql-password password \
        --mysql-database rohatax \
        --dry-run
"""

import os
import sys
import argparse
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any

try:
    import pymysql
except ImportError:
    print("❌ pymysql이 설치되지 않았습니다.")
    print("설치: pip install pymysql")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'migration_mysql_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SQLiteToMySQLMigrator:
    """SQLite에서 MySQL로 마이그레이션하는 클래스"""
    
    def __init__(self, sqlite_path: str, mysql_config: Dict, dry_run: bool = False):
        self.sqlite_path = sqlite_path
        self.mysql_config = mysql_config
        self.dry_run = dry_run
        self.sqlite_conn = None
        self.mysql_conn = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            if not os.path.exists(self.sqlite_path):
                raise FileNotFoundError(f"SQLite 파일을 찾을 수 없습니다: {self.sqlite_path}")
            
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✅ SQLite 연결 성공: {self.sqlite_path}")
            
            if not self.dry_run:
                self.mysql_conn = pymysql.connect(
                    host=self.mysql_config['host'],
                    user=self.mysql_config['user'],
                    password=self.mysql_config['password'],
                    database=self.mysql_config['database'],
                    charset='utf8mb4'
                )
                logger.info("✅ MySQL 연결 성공")
            else:
                logger.info("🔍 DRY-RUN 모드")
                
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.mysql_conn:
            self.mysql_conn.close()
    
    def get_sqlite_tables(self) -> List[str]:
        """SQLite의 모든 테이블 목록"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """테이블 스키마 정보"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        schema = {'columns': [], 'primary_key': None}
        
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
        
        return schema
    
    def convert_sqlite_type_to_mysql(self, sqlite_type: str) -> str:
        """SQLite 타입을 MySQL 타입으로 변환"""
        sqlite_type = sqlite_type.upper().split('(')[0]
        
        if sqlite_type in ['INTEGER', 'INT']:
            return 'INT'
        elif sqlite_type in ['TEXT', 'VARCHAR']:
            return 'TEXT'
        elif sqlite_type in ['REAL', 'FLOAT']:
            return 'DOUBLE'
        elif sqlite_type == 'BLOB':
            return 'BLOB'
        elif sqlite_type == 'BOOLEAN':
            return 'TINYINT(1)'
        else:
            return 'TEXT'
    
    def create_mysql_table(self, table_name: str, schema: Dict[str, Any]) -> str:
        """MySQL 테이블 생성 SQL"""
        columns = []
        
        for col in schema['columns']:
            col_def = f"`{col['name']}` {self.convert_sqlite_type_to_mysql(col['type'])}"
            
            if col['primary_key']:
                col_def += ' PRIMARY KEY AUTO_INCREMENT'
            elif col['not_null']:
                col_def += ' NOT NULL'
            
            if col['default']:
                default = col['default']
                if "datetime('now')" in default:
                    default = "CURRENT_TIMESTAMP"
                col_def += f" DEFAULT {default}"
            
            columns.append(col_def)
        
        create_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n    " + ",\n    ".join(columns) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        return create_sql
    
    def migrate_table_data(self, table_name: str) -> int:
        """테이블 데이터 마이그레이션"""
        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_sqlite.execute(f"SELECT * FROM {table_name}")
        rows = cursor_sqlite.fetchall()
        
        if not rows:
            return 0
        
        columns = [desc[0] for desc in cursor_sqlite.description]
        
        if self.dry_run:
            logger.info(f"  🔍 {table_name}: {len(rows)}개 행 (DRY-RUN)")
            return len(rows)
        
        cursor_mysql = self.mysql_conn.cursor()
        
        for row in rows:
            row_dict = dict(row)
            values = [row_dict.get(col) for col in columns]
            placeholders = ', '.join(['%s'] * len(values))
            col_names = ', '.join([f"`{c}`" for c in columns])
            
            insert_sql = f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})"
            cursor_mysql.execute(insert_sql, values)
        
        self.mysql_conn.commit()
        logger.info(f"  ✅ {table_name}: {len(rows)}개 행 마이그레이션 완료")
        return len(rows)
    
    def migrate(self):
        """전체 마이그레이션 실행"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 SQLite → MySQL 마이그레이션 시작")
            logger.info("=" * 60)
            
            tables = self.get_sqlite_tables()
            total_rows = 0
            
            for table_name in tables:
                logger.info(f"\n📦 테이블 처리: {table_name}")
                schema = self.get_table_schema(table_name)
                create_sql = self.create_mysql_table(table_name, schema)
                
                if not self.dry_run:
                    cursor = self.mysql_conn.cursor()
                    cursor.execute(create_sql)
                    self.mysql_conn.commit()
                    logger.info(f"  ✅ 테이블 생성 완료")
                else:
                    logger.info(f"  🔍 테이블 생성 SQL (DRY-RUN):\n{create_sql}")
                
                rows = self.migrate_table_data(table_name)
                total_rows += rows
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ 마이그레이션 완료! (테이블: {len(tables)}개, 행: {total_rows}개)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 실패: {e}", exc_info=True)
            if self.mysql_conn:
                self.mysql_conn.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description='SQLite → MySQL 마이그레이션')
    parser.add_argument('--sqlite-path', required=True, help='SQLite 데이터베이스 파일 경로')
    parser.add_argument('--mysql-host', default='localhost', help='MySQL 호스트')
    parser.add_argument('--mysql-user', required=True, help='MySQL 사용자')
    parser.add_argument('--mysql-password', required=True, help='MySQL 비밀번호')
    parser.add_argument('--mysql-database', required=True, help='MySQL 데이터베이스명')
    parser.add_argument('--dry-run', action='store_true', help='테스트 모드')
    
    args = parser.parse_args()
    
    mysql_config = {
        'host': args.mysql_host,
        'user': args.mysql_user,
        'password': args.mysql_password,
        'database': args.mysql_database
    }
    
    migrator = SQLiteToMySQLMigrator(
        sqlite_path=args.sqlite_path,
        mysql_config=mysql_config,
        dry_run=args.dry_run
    )
    
    try:
        migrator.connect()
        migrator.migrate()
    finally:
        migrator.close()


if __name__ == '__main__':
    main()

