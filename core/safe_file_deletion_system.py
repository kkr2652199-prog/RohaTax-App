"""
파일 삭제 보호 시스템
- 백업 필수 시스템
- 사용자 승인 시스템
- 안전한 파일 삭제 관리
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import hashlib

class SafeFileDeletionSystem:
    """안전한 파일 삭제 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.deletion_db_path = "core/safe_deletion_db.json"
        self.deletion_db = self._load_deletion_db()
        
        # 삭제 보호 설정
        self.protection_settings = {
            "mandatory_backup": True,  # 필수 백업
            "user_confirmation_required": True,  # 사용자 승인 필수
            "recovery_window_hours": 24,  # 복구 가능 시간 (시간)
            "max_backup_versions": 5,  # 최대 백업 버전 수
            "auto_cleanup_days": 30  # 자동 정리 기간 (일)
        }
        
        # 삭제 금지 패턴
        self.deletion_prohibited_patterns = [
            "app.py", "main.py", "run.py",
            "core/", "routes/", "templates/",
            "static/", "config/", "database/",
            "절대지침/", "*.db", "*.sqlite",
            "requirements.txt", "README.md"
        ]
        
        self.logger.info("안전한 파일 삭제 시스템 초기화 완료")
    
    def _load_deletion_db(self) -> Dict[str, Any]:
        """삭제 데이터베이스 로드"""
        if os.path.exists(self.deletion_db_path):
            try:
                with open(self.deletion_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"삭제 DB 로드 실패: {e}")
        
        return {
            "deletion_requests": [],
            "completed_deletions": [],
            "recovered_files": [],
            "backup_registry": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_deletion_db(self):
        """삭제 데이터베이스 저장"""
        try:
            self.deletion_db["last_updated"] = datetime.now().isoformat()
            with open(self.deletion_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.deletion_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"삭제 DB 저장 실패: {e}")
    
    def request_file_deletion(self, file_path: str, ai_judgment: str = "", ai_confidence: float = 0.0, 
                            user_id: str = "system") -> Dict[str, Any]:
        """파일 삭제 요청"""
        # 삭제 금지 패턴 확인
        if self._is_deletion_prohibited(file_path):
            return {
                "success": False,
                "reason": "삭제 금지 파일입니다",
                "requires_backup": False,
                "requires_confirmation": False,
                "deletion_id": None
            }
        
        # 백업 생성
        backup_path = self._create_mandatory_backup(file_path)
        if not backup_path:
            return {
                "success": False,
                "reason": "백업 생성 실패",
                "requires_backup": True,
                "requires_confirmation": False,
                "deletion_id": None
            }
        
        # 삭제 요청 기록
        deletion_request = {
            "deletion_id": self._generate_deletion_id(),
            "file_path": file_path,
            "backup_path": backup_path,
            "ai_judgment": ai_judgment,
            "ai_confidence": ai_confidence,
            "user_id": user_id,
            "requested_at": datetime.now().isoformat(),
            "status": "pending_confirmation",
            "requires_confirmation": self.protection_settings["user_confirmation_required"]
        }
        
        self.deletion_db["deletion_requests"].append(deletion_request)
        self._save_deletion_db()
        
        self.logger.info(f"파일 삭제 요청: {file_path} (ID: {deletion_request['deletion_id']})")
        
        return {
            "success": True,
            "reason": "삭제 요청이 생성되었습니다",
            "requires_backup": True,
            "requires_confirmation": self.protection_settings["user_confirmation_required"],
            "deletion_id": deletion_request["deletion_id"],
            "backup_path": backup_path
        }
    
    def _is_deletion_prohibited(self, file_path: str) -> bool:
        """삭제 금지 패턴 확인"""
        import fnmatch
        
        for pattern in self.deletion_prohibited_patterns:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        return False
    
    def _create_mandatory_backup(self, file_path: str) -> Optional[str]:
        """필수 백업 생성"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"백업할 파일이 존재하지 않습니다: {file_path}")
                return None
            
            # 백업 디렉토리 생성
            backup_dir = Path("backups/safe_deletion")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 백업 파일명 생성 (버전 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            backup_name = f"{name}_백업_v1_{timestamp}{ext}"
            backup_path = backup_dir / backup_name
            
            # 파일 복사
            shutil.copy2(file_path, backup_path)
            
            # 백업 등록
            backup_info = {
                "original_path": file_path,
                "backup_path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
                "file_hash": self._calculate_file_hash(file_path),
                "version": 1
            }
            
            self.deletion_db["backup_registry"][str(backup_path)] = backup_info
            self._save_deletion_db()
            
            self.logger.info(f"필수 백업 생성: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"백업 생성 실패: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"파일 해시 계산 실패: {e}")
            return ""
    
    def _generate_deletion_id(self) -> str:
        """삭제 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"DEL_{timestamp}_{hash(str(datetime.now())) % 10000:04d}"
    
    def confirm_deletion(self, deletion_id: str, user_confirmed: bool = False, 
                        confirmation_reason: str = "") -> Dict[str, Any]:
        """삭제 승인 처리"""
        # 삭제 요청 찾기
        deletion_request = None
        for req in self.deletion_db["deletion_requests"]:
            if req["deletion_id"] == deletion_id:
                deletion_request = req
                break
        
        if not deletion_request:
            return {
                "success": False,
                "reason": "삭제 요청을 찾을 수 없습니다"
            }
        
        if not user_confirmed:
            # 사용자가 거부한 경우
            deletion_request["status"] = "rejected"
            deletion_request["rejected_at"] = datetime.now().isoformat()
            deletion_request["rejection_reason"] = confirmation_reason
            
            self._save_deletion_db()
            
            return {
                "success": False,
                "reason": "사용자가 삭제를 거부했습니다",
                "backup_path": deletion_request["backup_path"]
            }
        
        # 삭제 실행
        try:
            file_path = deletion_request["file_path"]
            
            if os.path.exists(file_path):
                # 파일 삭제
                os.remove(file_path)
                
                # 완료 기록
                completed_deletion = {
                    "deletion_id": deletion_id,
                    "file_path": file_path,
                    "backup_path": deletion_request["backup_path"],
                    "deleted_at": datetime.now().isoformat(),
                    "user_confirmed": True,
                    "confirmation_reason": confirmation_reason,
                    "recovery_deadline": (datetime.now() + timedelta(hours=self.protection_settings["recovery_window_hours"])).isoformat()
                }
                
                self.deletion_db["completed_deletions"].append(completed_deletion)
                
                # 요청 상태 업데이트
                deletion_request["status"] = "completed"
                deletion_request["completed_at"] = datetime.now().isoformat()
                
                self._save_deletion_db()
                
                self.logger.info(f"파일 삭제 완료: {file_path}")
                
                return {
                    "success": True,
                    "reason": "파일이 성공적으로 삭제되었습니다",
                    "backup_path": deletion_request["backup_path"],
                    "recovery_deadline": completed_deletion["recovery_deadline"]
                }
            else:
                return {
                    "success": False,
                    "reason": "파일이 이미 존재하지 않습니다"
                }
                
        except Exception as e:
            self.logger.error(f"파일 삭제 실패: {e}")
            return {
                "success": False,
                "reason": f"파일 삭제 중 오류 발생: {str(e)}"
            }
    
    def recover_file(self, deletion_id: str, user_id: str = "system") -> Dict[str, Any]:
        """파일 복구"""
        # 완료된 삭제 기록 찾기
        completed_deletion = None
        for deletion in self.deletion_db["completed_deletions"]:
            if deletion["deletion_id"] == deletion_id:
                completed_deletion = deletion
                break
        
        if not completed_deletion:
            return {
                "success": False,
                "reason": "삭제 기록을 찾을 수 없습니다"
            }
        
        # 복구 가능 시간 확인
        recovery_deadline = datetime.fromisoformat(completed_deletion["recovery_deadline"])
        if datetime.now() > recovery_deadline:
            return {
                "success": False,
                "reason": "복구 가능 시간이 지났습니다"
            }
        
        # 백업에서 복구
        backup_path = completed_deletion["backup_path"]
        original_path = completed_deletion["file_path"]
        
        try:
            if os.path.exists(backup_path):
                # 백업에서 원본 위치로 복구
                shutil.copy2(backup_path, original_path)
                
                # 복구 기록
                recovery_record = {
                    "deletion_id": deletion_id,
                    "file_path": original_path,
                    "backup_path": backup_path,
                    "recovered_at": datetime.now().isoformat(),
                    "recovered_by": user_id
                }
                
                self.deletion_db["recovered_files"].append(recovery_record)
                self._save_deletion_db()
                
                self.logger.info(f"파일 복구 완료: {original_path}")
                
                return {
                    "success": True,
                    "reason": "파일이 성공적으로 복구되었습니다",
                    "file_path": original_path
                }
            else:
                return {
                    "success": False,
                    "reason": "백업 파일이 존재하지 않습니다"
                }
                
        except Exception as e:
            self.logger.error(f"파일 복구 실패: {e}")
            return {
                "success": False,
                "reason": f"파일 복구 중 오류 발생: {str(e)}"
            }
    
    def get_pending_deletions(self) -> List[Dict[str, Any]]:
        """대기 중인 삭제 요청 조회"""
        return [req for req in self.deletion_db["deletion_requests"] if req["status"] == "pending_confirmation"]
    
    def get_deletion_status(self, deletion_id: str) -> Optional[Dict[str, Any]]:
        """삭제 상태 조회"""
        # 대기 중인 요청에서 찾기
        for req in self.deletion_db["deletion_requests"]:
            if req["deletion_id"] == deletion_id:
                return req
        
        # 완료된 삭제에서 찾기
        for deletion in self.deletion_db["completed_deletions"]:
            if deletion["deletion_id"] == deletion_id:
                return deletion
        
        return None
    
    def cleanup_old_backups(self):
        """오래된 백업 정리"""
        try:
            cleanup_date = datetime.now() - timedelta(days=self.protection_settings["auto_cleanup_days"])
            
            backups_to_remove = []
            for backup_path, backup_info in self.deletion_db["backup_registry"].items():
                created_at = datetime.fromisoformat(backup_info["created_at"])
                if created_at < cleanup_date:
                    backups_to_remove.append(backup_path)
            
            for backup_path in backups_to_remove:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    del self.deletion_db["backup_registry"][backup_path]
                    self.logger.info(f"오래된 백업 삭제: {backup_path}")
            
            self._save_deletion_db()
            
        except Exception as e:
            self.logger.error(f"백업 정리 실패: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            "pending_deletions": len(self.get_pending_deletions()),
            "completed_deletions": len(self.deletion_db["completed_deletions"]),
            "recovered_files": len(self.deletion_db["recovered_files"]),
            "total_backups": len(self.deletion_db["backup_registry"]),
            "protection_settings": self.protection_settings,
            "last_updated": self.deletion_db["last_updated"]
        }

# 전역 인스턴스
safe_file_deletion_system = SafeFileDeletionSystem()







