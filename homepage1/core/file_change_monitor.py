"""
파일 수정 감지 및 자동 백업 시스템
- 파일 변경 감지 시 자동 백업
- 실시간 모니터링
- 백업 정책 관리
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Set, Callable, Any
from core.auto_backup_manager import auto_backup_manager

class FileChangeMonitor:
    """파일 변경 감지 및 자동 백업 모니터"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitored_files: Dict[str, float] = {}  # 파일 경로: 마지막 수정 시간
        self.backup_policies: Dict[str, Dict] = {}  # 백업 정책
        self.change_callbacks: Set[Callable] = set()  # 변경 콜백 함수들
        
    def add_file(self, file_path: str, backup_policy: Dict = None):
        """모니터링할 파일 추가"""
        try:
            file_path = str(Path(file_path).resolve())
            
            if os.path.exists(file_path):
                # 현재 수정 시간 기록
                self.monitored_files[file_path] = os.path.getmtime(file_path)
                
                # 백업 정책 설정
                if backup_policy is None:
                    backup_policy = {
                        'auto_backup': True,
                        'backup_reason': 'monitored_change',
                        'max_backups': 10
                    }
                
                self.backup_policies[file_path] = backup_policy
                
                self.logger.info(f"📁 파일 모니터링 시작: {file_path}")
                
            else:
                self.logger.warning(f"모니터링할 파일이 존재하지 않음: {file_path}")
                
        except Exception as e:
            self.logger.error(f"파일 추가 오류: {str(e)}")
    
    def remove_file(self, file_path: str):
        """모니터링에서 파일 제거"""
        try:
            file_path = str(Path(file_path).resolve())
            
            if file_path in self.monitored_files:
                del self.monitored_files[file_path]
                del self.backup_policies[file_path]
                self.logger.info(f"📁 파일 모니터링 중단: {file_path}")
                
        except Exception as e:
            self.logger.error(f"파일 제거 오류: {str(e)}")
    
    def add_change_callback(self, callback: Callable):
        """파일 변경 콜백 함수 추가"""
        self.change_callbacks.add(callback)
        self.logger.info(f"🔄 변경 콜백 추가: {callback.__name__}")
    
    def remove_change_callback(self, callback: Callable):
        """파일 변경 콜백 함수 제거"""
        self.change_callbacks.discard(callback)
        self.logger.info(f"🔄 변경 콜백 제거: {callback.__name__}")
    
    def check_changes(self) -> Dict[str, str]:
        """파일 변경 확인 및 자동 백업"""
        changed_files = {}
        
        try:
            for file_path, last_mtime in self.monitored_files.items():
                if os.path.exists(file_path):
                    current_mtime = os.path.getmtime(file_path)
                    
                    if current_mtime > last_mtime:
                        # 파일이 변경됨
                        changed_files[file_path] = "modified"
                        
                        # 자동 백업 실행
                        policy = self.backup_policies.get(file_path, {})
                        if policy.get('auto_backup', True):
                            backup_reason = policy.get('backup_reason', 'monitored_change')
                            backup_path = auto_backup_manager.create_backup(file_path, backup_reason)
                            
                            if backup_path:
                                self.logger.info(f"🔄 자동 백업 완료: {file_path}")
                        
                        # 마지막 수정 시간 업데이트
                        self.monitored_files[file_path] = current_mtime
                        
                        # 콜백 함수 실행
                        for callback in self.change_callbacks:
                            try:
                                callback(file_path, "modified")
                            except Exception as e:
                                self.logger.error(f"콜백 실행 오류: {str(e)}")
                
                else:
                    # 파일이 삭제됨
                    changed_files[file_path] = "deleted"
                    self.logger.warning(f"📁 모니터링 파일 삭제됨: {file_path}")
                    
                    # 콜백 함수 실행
                    for callback in self.change_callbacks:
                        try:
                            callback(file_path, "deleted")
                        except Exception as e:
                            self.logger.error(f"콜백 실행 오류: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"변경 확인 오류: {str(e)}")
        
        return changed_files
    
    def start_monitoring(self, interval: float = 1.0):
        """실시간 모니터링 시작"""
        self.logger.info(f"🔄 파일 모니터링 시작 (간격: {interval}초)")
        
        try:
            while True:
                changed_files = self.check_changes()
                
                if changed_files:
                    self.logger.info(f"📁 변경된 파일: {len(changed_files)}개")
                    for file_path, status in changed_files.items():
                        self.logger.info(f"  - {file_path}: {status}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("🔄 파일 모니터링 중단")
        except Exception as e:
            self.logger.error(f"모니터링 오류: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """모니터링 상태 반환"""
        return {
            'monitored_files': len(self.monitored_files),
            'backup_policies': len(self.backup_policies),
            'callbacks': len(self.change_callbacks),
            'files': list(self.monitored_files.keys())
        }

# 전역 인스턴스
file_change_monitor = FileChangeMonitor()
