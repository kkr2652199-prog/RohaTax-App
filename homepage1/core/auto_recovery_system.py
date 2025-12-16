"""
자동 복구 시스템
- 5분 내 자동 복구
- 백업에서 자동 복원
- 실시간 복구 모니터링
"""

import os
import json
import logging
import shutil
import threading
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import hashlib

class AutoRecoverySystem:
    """자동 복구 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recovery_db_path = "core/auto_recovery_db.json"
        self.recovery_db = self._load_recovery_db()
        
        # 복구 설정
        self.recovery_settings = {
            "auto_recovery_enabled": True,
            "recovery_window_minutes": 5,  # 5분 내 자동 복구
            "monitoring_interval_seconds": 30,  # 30초마다 모니터링
            "max_recovery_attempts": 3,  # 최대 복구 시도 횟수
            "backup_verification": True,  # 백업 검증 활성화
            "notification_enabled": True  # 알림 활성화
        }
        
        # 복구 모니터링 스레드
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # 복구 대기열
        self.recovery_queue = []
        
        self.logger.info("자동 복구 시스템 초기화 완료")
    
    def _load_recovery_db(self) -> Dict[str, Any]:
        """복구 데이터베이스 로드"""
        if os.path.exists(self.recovery_db_path):
            try:
                with open(self.recovery_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"복구 DB 로드 실패: {e}")
        
        return {
            "recovery_history": [],
            "failed_recoveries": [],
            "successful_recoveries": [],
            "monitoring_log": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_recovery_db(self):
        """복구 데이터베이스 저장"""
        try:
            self.recovery_db["last_updated"] = datetime.now().isoformat()
            with open(self.recovery_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.recovery_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"복구 DB 저장 실패: {e}")
    
    def register_file_for_recovery(self, file_path: str, backup_path: str, 
                                 deletion_id: str = "", reason: str = "") -> Dict[str, Any]:
        """복구 대상 파일 등록"""
        recovery_entry = {
            "file_path": file_path,
            "backup_path": backup_path,
            "deletion_id": deletion_id,
            "reason": reason,
            "registered_at": datetime.now().isoformat(),
            "recovery_deadline": (datetime.now() + timedelta(minutes=self.recovery_settings["recovery_window_minutes"])).isoformat(),
            "status": "pending",
            "attempts": 0,
            "last_attempt": None
        }
        
        # 복구 대기열에 추가
        self.recovery_queue.append(recovery_entry)
        
        # 복구 기록 저장
        self.recovery_db["recovery_history"].append(recovery_entry)
        self._save_recovery_db()
        
        self.logger.info(f"복구 대상 등록: {file_path}")
        
        # 자동 복구 모니터링 시작
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            self.start_monitoring()
        
        return {
            "success": True,
            "recovery_id": recovery_entry["deletion_id"],
            "recovery_deadline": recovery_entry["recovery_deadline"],
            "message": "파일이 복구 대기열에 등록되었습니다"
        }
    
    def start_monitoring(self):
        """복구 모니터링 시작"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitor_recovery, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("자동 복구 모니터링 시작")
    
    def stop_monitoring_system(self):
        """복구 모니터링 중지"""
        self.stop_monitoring = True
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("자동 복구 모니터링 중지")
    
    def _monitor_recovery(self):
        """복구 모니터링 메인 루프"""
        while not self.stop_monitoring:
            try:
                current_time = datetime.now()
                
                # 복구 대기열 처리
                for recovery_entry in self.recovery_queue[:]:  # 복사본으로 순회
                    if recovery_entry["status"] == "pending":
                        recovery_deadline = datetime.fromisoformat(recovery_entry["recovery_deadline"])
                        
                        # 복구 시도
                        if current_time >= recovery_deadline:
                            self._attempt_recovery(recovery_entry)
                        else:
                            # 복구 대기 중 로그
                            remaining_time = recovery_deadline - current_time
                            self.logger.debug(f"복구 대기 중: {recovery_entry['file_path']} (남은 시간: {remaining_time})")
                
                # 완료된 항목 정리
                self.recovery_queue = [entry for entry in self.recovery_queue if entry["status"] == "pending"]
                
                # 모니터링 로그 기록
                self._log_monitoring_status()
                
                # 대기
                time.sleep(self.recovery_settings["monitoring_interval_seconds"])
                
            except Exception as e:
                self.logger.error(f"복구 모니터링 오류: {e}")
                time.sleep(5)  # 오류 시 잠시 대기
    
    def _attempt_recovery(self, recovery_entry: Dict[str, Any]) -> bool:
        """복구 시도"""
        try:
            recovery_entry["attempts"] += 1
            recovery_entry["last_attempt"] = datetime.now().isoformat()
            
            file_path = recovery_entry["file_path"]
            backup_path = recovery_entry["backup_path"]
            
            # 백업 파일 존재 확인
            if not os.path.exists(backup_path):
                self.logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
                recovery_entry["status"] = "failed"
                recovery_entry["error"] = "백업 파일 없음"
                self._record_failed_recovery(recovery_entry)
                return False
            
            # 백업 검증
            if self.recovery_settings["backup_verification"]:
                if not self._verify_backup_integrity(backup_path):
                    self.logger.error(f"백업 파일 무결성 검증 실패: {backup_path}")
                    recovery_entry["status"] = "failed"
                    recovery_entry["error"] = "백업 무결성 검증 실패"
                    self._record_failed_recovery(recovery_entry)
                    return False
            
            # 파일 복구
            if os.path.exists(file_path):
                # 파일이 이미 존재하는 경우 백업
                backup_existing = f"{file_path}.recovery_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_existing)
                self.logger.info(f"기존 파일 백업: {backup_existing}")
            
            # 백업에서 복구
            shutil.copy2(backup_path, file_path)
            
            # 복구 검증
            if self._verify_recovery_success(file_path, backup_path):
                recovery_entry["status"] = "completed"
                recovery_entry["completed_at"] = datetime.now().isoformat()
                self._record_successful_recovery(recovery_entry)
                
                self.logger.info(f"자동 복구 성공: {file_path}")
                
                # 알림 전송
                if self.recovery_settings["notification_enabled"]:
                    self._send_recovery_notification(recovery_entry, "success")
                
                return True
            else:
                recovery_entry["status"] = "failed"
                recovery_entry["error"] = "복구 검증 실패"
                self._record_failed_recovery(recovery_entry)
                return False
                
        except Exception as e:
            self.logger.error(f"복구 시도 실패: {e}")
            recovery_entry["status"] = "failed"
            recovery_entry["error"] = str(e)
            self._record_failed_recovery(recovery_entry)
            return False
    
    def _verify_backup_integrity(self, backup_path: str) -> bool:
        """백업 파일 무결성 검증"""
        try:
            # 파일 크기 확인
            if os.path.getsize(backup_path) == 0:
                return False
            
            # 파일 읽기 가능성 확인
            with open(backup_path, 'rb') as f:
                f.read(1024)  # 첫 1KB 읽기 테스트
            
            return True
            
        except Exception as e:
            self.logger.error(f"백업 무결성 검증 실패: {e}")
            return False
    
    def _verify_recovery_success(self, file_path: str, backup_path: str) -> bool:
        """복구 성공 검증"""
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                return False
            
            # 파일 크기 비교
            if os.path.getsize(file_path) != os.path.getsize(backup_path):
                return False
            
            # 파일 해시 비교
            file_hash = self._calculate_file_hash(file_path)
            backup_hash = self._calculate_file_hash(backup_path)
            
            return file_hash == backup_hash
            
        except Exception as e:
            self.logger.error(f"복구 검증 실패: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"파일 해시 계산 실패: {e}")
            return ""
    
    def _record_successful_recovery(self, recovery_entry: Dict[str, Any]):
        """성공한 복구 기록"""
        self.recovery_db["successful_recoveries"].append(recovery_entry)
        self._save_recovery_db()
    
    def _record_failed_recovery(self, recovery_entry: Dict[str, Any]):
        """실패한 복구 기록"""
        self.recovery_db["failed_recoveries"].append(recovery_entry)
        self._save_recovery_db()
        
        # 알림 전송
        if self.recovery_settings["notification_enabled"]:
            self._send_recovery_notification(recovery_entry, "failed")
    
    def _send_recovery_notification(self, recovery_entry: Dict[str, Any], status: str):
        """복구 알림 전송"""
        try:
            message = f"자동 복구 {status}: {recovery_entry['file_path']}"
            if status == "failed":
                message += f" (오류: {recovery_entry.get('error', '알 수 없음')})"
            
            self.logger.info(f"복구 알림: {message}")
            
            # 여기에 실제 알림 시스템 연동 (이메일, 슬랙 등)
            # notification_system.send_notification(message)
            
        except Exception as e:
            self.logger.error(f"알림 전송 실패: {e}")
    
    def _log_monitoring_status(self):
        """모니터링 상태 로그"""
        monitoring_log = {
            "timestamp": datetime.now().isoformat(),
            "queue_size": len(self.recovery_queue),
            "pending_recoveries": len([entry for entry in self.recovery_queue if entry["status"] == "pending"]),
            "monitoring_active": not self.stop_monitoring
        }
        
        self.recovery_db["monitoring_log"].append(monitoring_log)
        
        # 로그 크기 제한 (최근 100개만 유지)
        if len(self.recovery_db["monitoring_log"]) > 100:
            self.recovery_db["monitoring_log"] = self.recovery_db["monitoring_log"][-100:]
        
        self._save_recovery_db()
    
    def manual_recovery(self, file_path: str, backup_path: str, user_id: str = "manual") -> Dict[str, Any]:
        """수동 복구"""
        try:
            if not os.path.exists(backup_path):
                return {
                    "success": False,
                    "reason": "백업 파일이 존재하지 않습니다"
                }
            
            # 백업에서 복구
            shutil.copy2(backup_path, file_path)
            
            # 복구 검증
            if self._verify_recovery_success(file_path, backup_path):
                recovery_entry = {
                    "file_path": file_path,
                    "backup_path": backup_path,
                    "deletion_id": f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "reason": "수동 복구",
                    "registered_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "status": "completed",
                    "attempts": 1,
                    "recovered_by": user_id
                }
                
                self._record_successful_recovery(recovery_entry)
                
                return {
                    "success": True,
                    "reason": "수동 복구가 성공적으로 완료되었습니다",
                    "file_path": file_path
                }
            else:
                return {
                    "success": False,
                    "reason": "복구 검증에 실패했습니다"
                }
                
        except Exception as e:
            self.logger.error(f"수동 복구 실패: {e}")
            return {
                "success": False,
                "reason": f"복구 중 오류 발생: {str(e)}"
            }
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """복구 시스템 상태 조회"""
        return {
            "monitoring_active": not self.stop_monitoring,
            "queue_size": len(self.recovery_queue),
            "pending_recoveries": len([entry for entry in self.recovery_queue if entry["status"] == "pending"]),
            "total_recoveries": len(self.recovery_db["recovery_history"]),
            "successful_recoveries": len(self.recovery_db["successful_recoveries"]),
            "failed_recoveries": len(self.recovery_db["failed_recoveries"]),
            "recovery_settings": self.recovery_settings,
            "last_updated": self.recovery_db["last_updated"]
        }
    
    def get_recovery_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """복구 이력 조회"""
        return self.recovery_db["recovery_history"][-limit:]
    
    def cleanup_old_recovery_data(self, days: int = 30):
        """오래된 복구 데이터 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 오래된 복구 이력 정리
            self.recovery_db["recovery_history"] = [
                entry for entry in self.recovery_db["recovery_history"]
                if datetime.fromisoformat(entry["registered_at"]) > cutoff_date
            ]
            
            # 오래된 모니터링 로그 정리
            self.recovery_db["monitoring_log"] = [
                log for log in self.recovery_db["monitoring_log"]
                if datetime.fromisoformat(log["timestamp"]) > cutoff_date
            ]
            
            self._save_recovery_db()
            self.logger.info(f"{days}일 이상 된 복구 데이터 정리 완료")
            
        except Exception as e:
            self.logger.error(f"복구 데이터 정리 실패: {e}")

# 전역 인스턴스
auto_recovery_system = AutoRecoverySystem()














