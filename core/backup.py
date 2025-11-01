import os
import shutil
import sqlite3
import json
from datetime import datetime
from typing import Optional
from core.db import DB_PATH

class BackupManager:
    """데이터베이스 및 파일 백업 관리자"""
    
    def __init__(self):
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """백업 디렉토리 생성"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_db_backup(self, description: str = "") -> str:
        """데이터베이스 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"db_backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
        
        # 데이터베이스 파일 복사
        shutil.copy2(DB_PATH, backup_path)
        
        # 백업 메타데이터 저장
        metadata = {
            "timestamp": timestamp,
            "description": description,
            "backup_path": backup_path,
            "original_path": DB_PATH,
            "type": "database"
        }
        
        metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 데이터베이스 백업 완료: {backup_name}")
        return backup_name
    
    def create_code_backup(self, description: str = "") -> str:
        """코드 백업 생성 (중요 파일들만)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"code_backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        # 백업할 중요 파일들
        important_files = [
            'app.py',
            'routes/',
            'core/',
            'templates/',
            'database/schema.sql',
            'config/'
        ]
        
        for item in important_files:
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), item)
            dst_path = os.path.join(backup_path, item)
            
            # 대상 디렉토리 생성
            dst_dir = os.path.dirname(dst_path)
            os.makedirs(dst_dir, exist_ok=True)
            
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
            elif os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        
        # 백업 메타데이터 저장
        metadata = {
            "timestamp": timestamp,
            "description": description,
            "backup_path": backup_path,
            "type": "code",
            "files_backed_up": important_files
        }
        
        metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 코드 백업 완료: {backup_name}")
        return backup_name
    
    def list_backups(self) -> list:
        """백업 목록 조회"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('_metadata.json'):
                metadata_path = os.path.join(self.backup_dir, file)
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append(metadata)
                except:
                    continue
        
        # 시간순 정렬 (최신순)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def restore_db_backup(self, backup_name: str) -> bool:
        """데이터베이스 백업 복원"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            
            if not os.path.exists(backup_path):
                print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_name}")
                return False
            
            # 현재 데이터베이스 백업
            current_backup = self.create_db_backup("before_restore")
            
            # 백업 복원
            shutil.copy2(backup_path, DB_PATH)
            
            print(f"✅ 데이터베이스 복원 완료: {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ 데이터베이스 복원 실패: {e}")
            return False
    
    def restore_code_backup(self, backup_name: str) -> bool:
        """코드 백업 복원"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            
            if not os.path.exists(backup_path):
                print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_name}")
                return False
            
            # 현재 코드 백업
            current_backup = self.create_code_backup("before_restore")
            
            # 백업 복원
            project_root = os.path.dirname(os.path.dirname(__file__))
            for item in os.listdir(backup_path):
                src_path = os.path.join(backup_path, item)
                dst_path = os.path.join(project_root, item)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            
            print(f"✅ 코드 복원 완료: {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ 코드 복원 실패: {e}")
            return False

# 전역 백업 매니저 인스턴스
backup_manager = BackupManager()
