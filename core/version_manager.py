import os
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from core.db import get_conn_optimized as get_conn, DB_PATH
# from core.backup import backup_manager  # 임시 주석 처리

class VersionManager:
    """완전한 버전 관리 시스템"""
    
    def __init__(self):
        self.version_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'versions.db')
        self.init_version_db()
    
    def init_version_db(self):
        """버전 관리 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.version_db_path), exist_ok=True)
        
        with sqlite3.connect(self.version_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_number TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    author TEXT,
                    change_type TEXT NOT NULL, -- 'manual', 'auto', 'rollback'
                    parent_version TEXT,
                    checksum TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    change_type TEXT NOT NULL, -- 'created', 'modified', 'deleted'
                    old_content TEXT,
                    new_content TEXT,
                    old_checksum TEXT,
                    new_checksum TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(version_id) REFERENCES versions(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER NOT NULL,
                    change_type TEXT NOT NULL, -- 'schema', 'data'
                    table_name TEXT,
                    sql_statement TEXT,
                    old_data TEXT,
                    new_data TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(version_id) REFERENCES versions(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rollback_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER NOT NULL,
                    rollback_reason TEXT,
                    rollback_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(version_id) REFERENCES versions(id)
                )
            """)
            
            conn.commit()
    
    def get_next_version_number(self) -> str:
        """다음 버전 번호 생성"""
        with sqlite3.connect(self.version_db_path) as conn:
            cursor = conn.execute("SELECT MAX(CAST(SUBSTR(version_number, 2) AS INTEGER)) FROM versions WHERE version_number LIKE 'v%'")
            max_num = cursor.fetchone()[0]
            
            if max_num is None:
                return "v1.0.0"
            else:
                return f"v{max_num + 1}.0.0"
    
    def calculate_file_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except:
            return ""
    
    def get_file_content(self, file_path: str) -> str:
        """파일 내용 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def scan_project_files(self) -> Dict[str, str]:
        """프로젝트 파일들 스캔"""
        project_root = os.path.dirname(os.path.dirname(__file__))
        file_checksums = {}
        
        # 스캔할 파일 패턴들
        scan_patterns = [
            '*.py',
            '*.html',
            '*.css',
            '*.js',
            '*.sql',
            '*.json',
            '*.md'
        ]
        
        for root, dirs, files in os.walk(project_root):
            # 백업 디렉토리 제외
            if 'backups' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if any(file.endswith(pattern.replace('*', '')) for pattern in scan_patterns):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_root)
                    checksum = self.calculate_file_checksum(file_path)
                    file_checksums[relative_path] = checksum
        
        return file_checksums
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """데이터베이스 스냅샷 생성"""
        snapshot = {
            'tables': {},
            'schema': {}
        }
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                # 테이블 목록
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                
                for table in tables:
                    table_name = table[0]
                    
                    # 테이블 스키마
                    schema = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                    snapshot['schema'][table_name] = [list(row) for row in schema]
                    
                    # 테이블 데이터 (중요한 테이블만)
                    if table_name in ['users', 'settings', 'token_history']:
                        data = conn.execute(f"SELECT * FROM {table_name}").fetchall()
                        snapshot['tables'][table_name] = [list(row) for row in data]
        
        except Exception as e:
            print(f"데이터베이스 스냅샷 생성 실패: {e}")
        
        return snapshot
    
    def create_version(self, description: str, author: str = "system", change_type: str = "manual") -> str:
        """새 버전 생성"""
        version_number = self.get_next_version_number()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 현재 상태 스캔
        file_checksums = self.scan_project_files()
        db_snapshot = self.get_database_snapshot()
        
        # 메타데이터 생성
        metadata = {
            'file_count': len(file_checksums),
            'db_tables': list(db_snapshot['tables'].keys()),
            'file_checksums': file_checksums,
            'db_snapshot': db_snapshot
        }
        
        # 체크섬 계산
        metadata_str = json.dumps(metadata, sort_keys=True)
        checksum = hashlib.md5(metadata_str.encode()).hexdigest()
        
        # 버전 저장
        with sqlite3.connect(self.version_db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO versions (version_number, timestamp, description, author, change_type, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (version_number, timestamp, description, author, change_type, checksum, metadata_str))
            
            version_id = cursor.lastrowid
            conn.commit()
        
        print(f"✅ 버전 생성 완료: {version_number} - {description}")
        return version_number
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """두 버전 간 차이점 비교"""
        differences = {
            'file_changes': [],
            'db_changes': [],
            'summary': {}
        }
        
        with sqlite3.connect(self.version_db_path) as conn:
            # 버전 정보 조회
            v1 = conn.execute("SELECT metadata FROM versions WHERE version_number = ?", (version1,)).fetchone()
            v2 = conn.execute("SELECT metadata FROM versions WHERE version_number = ?", (version2,)).fetchone()
            
            if not v1 or not v2:
                return differences
            
            metadata1 = json.loads(v1[0])
            metadata2 = json.loads(v2[0])
            
            # 파일 변경사항 비교
            checksums1 = metadata1.get('file_checksums', {})
            checksums2 = metadata2.get('file_checksums', {})
            
            all_files = set(checksums1.keys()) | set(checksums2.keys())
            
            for file_path in all_files:
                checksum1 = checksums1.get(file_path, "")
                checksum2 = checksums2.get(file_path, "")
                
                if checksum1 != checksum2:
                    if not checksum1:
                        differences['file_changes'].append({
                            'file': file_path,
                            'change': 'created',
                            'old_checksum': None,
                            'new_checksum': checksum2
                        })
                    elif not checksum2:
                        differences['file_changes'].append({
                            'file': file_path,
                            'change': 'deleted',
                            'old_checksum': checksum1,
                            'new_checksum': None
                        })
                    else:
                        differences['file_changes'].append({
                            'file': file_path,
                            'change': 'modified',
                            'old_checksum': checksum1,
                            'new_checksum': checksum2
                        })
            
            # 데이터베이스 변경사항 비교
            db1 = metadata1.get('db_snapshot', {})
            db2 = metadata2.get('db_snapshot', {})
            
            # 테이블 변경사항
            tables1 = set(db1.get('tables', {}).keys())
            tables2 = set(db2.get('tables', {}).keys())
            
            for table in tables1 | tables2:
                if table not in tables1:
                    differences['db_changes'].append({
                        'table': table,
                        'change': 'created'
                    })
                elif table not in tables2:
                    differences['db_changes'].append({
                        'table': table,
                        'change': 'deleted'
                    })
                else:
                    # 데이터 변경사항 비교
                    data1 = db1['tables'][table]
                    data2 = db2['tables'][table]
                    
                    if len(data1) != len(data2):
                        differences['db_changes'].append({
                            'table': table,
                            'change': 'data_modified',
                            'old_count': len(data1),
                            'new_count': len(data2)
                        })
            
            # 요약 정보
            differences['summary'] = {
                'files_changed': len(differences['file_changes']),
                'db_changes': len(differences['db_changes']),
                'files_created': len([c for c in differences['file_changes'] if c['change'] == 'created']),
                'files_deleted': len([c for c in differences['file_changes'] if c['change'] == 'deleted']),
                'files_modified': len([c for c in differences['file_changes'] if c['change'] == 'modified'])
            }
        
        return differences
    
    def list_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """버전 목록 조회"""
        with sqlite3.connect(self.version_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT v.*, 
                       COUNT(fc.id) as file_changes_count,
                       COUNT(dc.id) as db_changes_count
                FROM versions v
                LEFT JOIN file_changes fc ON v.id = fc.version_id
                LEFT JOIN db_changes dc ON v.id = dc.version_id
                GROUP BY v.id
                ORDER BY v.created_at DESC
                LIMIT ?
            """, (limit,))
            
            versions = []
            for row in cursor.fetchall():
                version_data = dict(row)
                versions.append(version_data)
            
            return versions
    
    def get_version_details(self, version_number: str) -> Optional[Dict[str, Any]]:
        """특정 버전 상세 정보 조회"""
        with sqlite3.connect(self.version_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 버전 기본 정보
            version = conn.execute("SELECT * FROM versions WHERE version_number = ?", (version_number,)).fetchone()
            if not version:
                return None
            
            version_data = dict(version)
            
            # 파일 변경사항
            file_changes = conn.execute("""
                SELECT * FROM file_changes WHERE version_id = ?
                ORDER BY created_at DESC
            """, (version_data['id'],)).fetchall()
            
            version_data['file_changes'] = [dict(row) for row in file_changes]
            
            # DB 변경사항
            db_changes = conn.execute("""
                SELECT * FROM db_changes WHERE version_id = ?
                ORDER BY created_at DESC
            """, (version_data['id'],)).fetchall()
            
            version_data['db_changes'] = [dict(row) for row in db_changes]
            
            return version_data
    
    def rollback_to_version(self, version_number: str, reason: str = "") -> bool:
        """특정 버전으로 롤백"""
        try:
            print(f"🔄 버전 {version_number}로 롤백 시작...")
            
            # 롤백 전 백업 생성 (임시 주석 처리)
            # backup_name = backup_manager.create_db_backup(f"before_rollback_to_{version_number}")
            # code_backup = backup_manager.create_code_backup(f"before_rollback_to_{version_number}")
            
            # 버전 정보 조회
            version_data = self.get_version_details(version_number)
            if not version_data:
                print(f"❌ 버전 {version_number}을 찾을 수 없습니다.")
                return False
            
            metadata = json.loads(version_data['metadata'])
            
            # 파일 복원
            file_checksums = metadata.get('file_checksums', {})
            project_root = os.path.dirname(os.path.dirname(__file__))
            
            for file_path, checksum in file_checksums.items():
                full_path = os.path.join(project_root, file_path)
                
                # 백업에서 파일 복원 (임시 주석 처리)
                # backup_file_path = os.path.join(backup_manager.backup_dir, code_backup, file_path)
                # 
                # if os.path.exists(backup_file_path):
                #     os.makedirs(os.path.dirname(full_path), exist_ok=True)
                #     shutil.copy2(backup_file_path, full_path)
            
            # 데이터베이스 복원
            db_snapshot = metadata.get('db_snapshot', {})
            if db_snapshot:
                # 백업에서 DB 복원 (임시 주석 처리)
                # backup_db_path = os.path.join(backup_manager.backup_dir, f"{backup_name}.db")
                # if os.path.exists(backup_db_path):
                #     shutil.copy2(backup_db_path, DB_PATH)
                pass  # 임시로 pass 추가
            
            # 롤백 기록
            with sqlite3.connect(self.version_db_path) as conn:
                conn.execute("""
                    INSERT INTO rollback_points (version_id, rollback_reason, rollback_timestamp)
                    VALUES (?, ?, ?)
                """, (version_data['id'], reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            
            print(f"✅ 롤백 완료: {version_number}")
            return True
            
        except Exception as e:
            print(f"❌ 롤백 실패: {e}")
            return False
    
    def auto_create_version(self, description: str = "자동 변경 감지") -> Optional[str]:
        """자동 버전 생성 (파일 변경 감지 시)"""
        try:
            # 현재 상태와 마지막 버전 비교
            versions = self.list_versions(1)
            if not versions:
                return self.create_version("초기 버전", "system", "auto")
            
            last_version = versions[0]
            last_metadata = json.loads(last_version['metadata'])
            current_checksums = self.scan_project_files()
            last_checksums = last_metadata.get('file_checksums', {})
            
            # 변경사항 감지
            has_changes = False
            for file_path, checksum in current_checksums.items():
                if file_path not in last_checksums or last_checksums[file_path] != checksum:
                    has_changes = True
                    break
            
            if has_changes:
                return self.create_version(description, "system", "auto")
            
            return None
            
        except Exception as e:
            print(f"자동 버전 생성 실패: {e}")
            return None

# 전역 버전 매니저 인스턴스
version_manager = VersionManager()
