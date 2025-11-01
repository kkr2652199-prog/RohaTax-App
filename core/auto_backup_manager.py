"""
자동 백업 관리 시스템 (개선된 버전)
- 파일 변경 감지 시 자동 백업
- 버전 관리 시스템 (v1, v2, v3...)
- 자동 정리 (5개 백업 유지)
- 중복 감지 및 통합
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
import fnmatch

class AutoBackupManager:
    """자동 백업 관리자 (개선된 버전)"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.backup_db_path = self.backup_dir / "backup_database.json"
        self.backup_db = self._load_backup_db()
        
        # 백업 설정
        self.backup_settings = {
            "max_versions": 5,  # 최대 버전 수
            "auto_cleanup": True,  # 자동 정리
            "duplicate_detection": True,  # 중복 감지
            "version_naming": True,  # 버전 명명 (v1, v2, v3...)
            "compression": False,  # 압축 (향후 구현)
            "encryption": False  # 암호화 (향후 구현)
        }
        
        self.logger.info("자동 백업 관리자 초기화 완료 (개선된 버전)")
    
    def _load_backup_db(self) -> Dict[str, Any]:
        """백업 데이터베이스 로드"""
        if self.backup_db_path.exists():
            try:
                with open(self.backup_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"백업 DB 로드 실패: {e}")
        
        return {
            "backups": {},
            "version_tracking": {},  # 파일별 버전 추적
            "duplicate_registry": {},  # 중복 파일 등록
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_backup_db(self):
        """백업 데이터베이스 저장"""
        try:
            self.backup_db["last_updated"] = datetime.now().isoformat()
            with open(self.backup_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"백업 DB 저장 실패: {e}")
    
    def create_backup(self, file_path: str, max_backups: int = None, description: str = "자동 백업") -> Optional[str]:
        """백업 생성 (개선된 버전)"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"백업할 파일이 존재하지 않습니다: {file_path}")
                return None
            
            # 최대 백업 수 설정
            if max_backups is None:
                max_backups = self.backup_settings["max_versions"]
            
            # 중복 감지
            if self.backup_settings["duplicate_detection"]:
                if self._is_duplicate_backup(file_path):
                    self.logger.info(f"중복 백업 감지, 건너뜀: {file_path}")
                    return None
            
            # 다음 버전 번호 계산
            next_version = self._get_next_version(file_path)
            
            # 백업 파일명 생성 (버전 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            
            if self.backup_settings["version_naming"]:
                backup_name = f"{name}_백업_v{next_version}_{timestamp}{ext}"
            else:
                backup_name = f"{name}_백업_{timestamp}{ext}"
            
            backup_path = self.backup_dir / backup_name
            
            # 파일 복사
            shutil.copy2(file_path, backup_path)
            
            # 백업 정보 저장
            backup_info = {
                "original_path": file_path,
                "backup_path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
                "file_hash": self._calculate_file_hash(file_path),
                "description": description,
                "version": next_version,
                "backup_id": self._generate_backup_id()
            }
            
            # 파일별 백업 그룹 관리
            if file_path not in self.backup_db["backups"]:
                self.backup_db["backups"][file_path] = []
            
            self.backup_db["backups"][file_path].append(backup_info)
            
            # 버전 추적 업데이트
            self.backup_db["version_tracking"][file_path] = next_version
            
            # 자동 정리
            if self.backup_settings["auto_cleanup"]:
                self._cleanup_old_backups(file_path, max_backups)
            
            self._save_backup_db()
            
            self.logger.info(f"백업 생성 완료: {backup_path} (v{next_version})")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"백업 생성 실패: {e}")
            return None
    
    def _get_next_version(self, file_path: str) -> int:
        """다음 버전 번호 계산"""
        if file_path in self.backup_db["version_tracking"]:
            return self.backup_db["version_tracking"][file_path] + 1
        return 1
    
    def _generate_backup_id(self) -> str:
        """백업 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"BACKUP_{timestamp}_{hash(str(datetime.now())) % 10000:04d}"
    
    def _is_duplicate_backup(self, file_path: str) -> bool:
        """중복 백업 감지"""
        try:
            current_hash = self._calculate_file_hash(file_path)
            
            # 최근 백업과 해시 비교
            if file_path in self.backup_db["backups"]:
                recent_backups = self.backup_db["backups"][file_path][-3:]  # 최근 3개 백업 확인
                
                for backup in recent_backups:
                    if backup["file_hash"] == current_hash:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"중복 백업 감지 실패: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"파일 해시 계산 실패: {e}")
            return ""
    
    def _cleanup_old_backups(self, file_path: str, max_backups: int):
        """오래된 백업 정리 (개선된 버전)"""
        try:
            backups = self.backup_db["backups"][file_path]
            
            # 생성 시간 기준으로 정렬 (오래된 것부터)
            backups.sort(key=lambda x: x["created_at"])
            
            # 오래된 백업 삭제 (버전 순서 유지)
            while len(backups) > max_backups:
                old_backup = backups.pop(0)
                old_backup_path = old_backup["backup_path"]
                
                if os.path.exists(old_backup_path):
                    os.remove(old_backup_path)
                    self.logger.info(f"오래된 백업 삭제: {old_backup_path} (v{old_backup['version']})")
                
                # 중복 등록에서도 제거
                if old_backup["backup_id"] in self.backup_db["duplicate_registry"]:
                    del self.backup_db["duplicate_registry"][old_backup["backup_id"]]
                
        except Exception as e:
            self.logger.error(f"백업 정리 실패: {e}")
    
    def restore_backup(self, file_path: str, backup_path: str, create_restore_backup: bool = True) -> bool:
        """백업에서 복구 (개선된 버전)"""
        try:
            if not os.path.exists(backup_path):
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                return False
            
            # 복구 전 백업 생성
            if create_restore_backup and os.path.exists(file_path):
                restore_backup_path = self.create_backup(file_path, description="복구 전 백업")
                if restore_backup_path:
                    self.logger.info(f"복구 전 백업 생성: {restore_backup_path}")
            
            # 백업에서 복구
            shutil.copy2(backup_path, file_path)
            
            # 복구 기록
            restore_record = {
                "file_path": file_path,
                "backup_path": backup_path,
                "restored_at": datetime.now().isoformat(),
                "restore_id": self._generate_backup_id()
            }
            
            if "restore_history" not in self.backup_db:
                self.backup_db["restore_history"] = []
            
            self.backup_db["restore_history"].append(restore_record)
            self._save_backup_db()
            
            self.logger.info(f"백업에서 복구 완료: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"백업 복구 실패: {e}")
            return False
    
    def get_backup_list(self, file_path: str, sort_by: str = "version") -> List[Dict[str, Any]]:
        """파일의 백업 목록 조회 (정렬 옵션 포함)"""
        backups = self.backup_db["backups"].get(file_path, [])
        
        if sort_by == "version":
            backups.sort(key=lambda x: x["version"], reverse=True)
        elif sort_by == "date":
            backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def get_latest_backup(self, file_path: str) -> Optional[Dict[str, Any]]:
        """최신 백업 조회"""
        backups = self.get_backup_list(file_path, sort_by="version")
        return backups[0] if backups else None
    
    def get_backup_by_version(self, file_path: str, version: int) -> Optional[Dict[str, Any]]:
        """특정 버전의 백업 조회"""
        backups = self.backup_db["backups"].get(file_path, [])
        
        for backup in backups:
            if backup["version"] == version:
                return backup
        
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """특정 백업 삭제"""
        try:
            # 모든 파일의 백업에서 해당 ID 찾기
            for file_path, backups in self.backup_db["backups"].items():
                for i, backup in enumerate(backups):
                    if backup["backup_id"] == backup_id:
                        backup_path = backup["backup_path"]
                        
                        # 파일 삭제
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                        
                        # 목록에서 제거
                        backups.pop(i)
                        
                        self._save_backup_db()
                        self.logger.info(f"백업 삭제 완료: {backup_path}")
                        return True
            
            self.logger.warning(f"백업 ID를 찾을 수 없습니다: {backup_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"백업 삭제 실패: {e}")
            return False
    
    def cleanup_duplicate_backups(self) -> int:
        """중복 백업 정리"""
        cleaned_count = 0
        
        try:
            for file_path, backups in self.backup_db["backups"].items():
                # 해시별로 그룹화
                hash_groups = {}
                for backup in backups:
                    file_hash = backup["file_hash"]
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(backup)
                
                # 각 해시 그룹에서 최신 것만 유지
                for file_hash, group_backups in hash_groups.items():
                    if len(group_backups) > 1:
                        # 버전 순으로 정렬하여 최신 것만 유지
                        group_backups.sort(key=lambda x: x["version"], reverse=True)
                        
                        for old_backup in group_backups[1:]:  # 최신 것 제외하고 삭제
                            if os.path.exists(old_backup["backup_path"]):
                                os.remove(old_backup["backup_path"])
                                cleaned_count += 1
                                self.logger.info(f"중복 백업 삭제: {old_backup['backup_path']}")
                        
                        # 목록에서도 제거
                        self.backup_db["backups"][file_path] = [group_backups[0]] + [
                            backup for backup in backups 
                            if backup not in group_backups[1:]
                        ]
            
            self._save_backup_db()
            self.logger.info(f"중복 백업 정리 완료: {cleaned_count}개 삭제")
            
        except Exception as e:
            self.logger.error(f"중복 백업 정리 실패: {e}")
        
        return cleaned_count
    
    def get_backup_status(self) -> Dict[str, Any]:
        """백업 상태 조회 (개선된 버전)"""
        total_backups = sum(len(backups) for backups in self.backup_db["backups"].values())
        total_files = len(self.backup_db["backups"])
        
        # 버전별 통계
        version_stats = {}
        for file_path, backups in self.backup_db["backups"].items():
            max_version = max(backup["version"] for backup in backups) if backups else 0
            version_stats[file_path] = max_version
        
        return {
            "total_files": total_files,
            "total_backups": total_backups,
            "backup_dir": str(self.backup_dir),
            "backup_settings": self.backup_settings,
            "version_stats": version_stats,
            "restore_history_count": len(self.backup_db.get("restore_history", [])),
            "last_updated": self.backup_db["last_updated"]
        }
    
    def export_backup_info(self, file_path: str) -> Dict[str, Any]:
        """백업 정보 내보내기"""
        return {
            "file_path": file_path,
            "backups": self.get_backup_list(file_path),
            "latest_backup": self.get_latest_backup(file_path),
            "version_count": len(self.get_backup_list(file_path)),
            "exported_at": datetime.now().isoformat()
        }

# 전역 인스턴스
auto_backup_manager = AutoBackupManager()