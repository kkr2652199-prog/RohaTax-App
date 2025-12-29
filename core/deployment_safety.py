"""
배포 서버 안전장치 시스템
- 서비스 상태 모니터링
- 리소스 사용량 모니터링
- 백업 검증
- 자동 복구
"""

import os
import logging
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DeploymentSafetyMonitor:
    """배포 서버 안전장치 모니터"""
    
    def __init__(self, project_dir: Optional[str] = None):
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backup_dir = os.path.join(self.project_dir, 'database', 'backups')
        self.log_dir = os.path.join(self.project_dir, 'logs')
        
    def check_service_status(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'rohatax'],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_active = result.returncode == 0
            
            return {
                'status': 'active' if is_active else 'inactive',
                'healthy': is_active,
                'message': '서비스 정상' if is_active else '서비스 중지됨'
            }
        except Exception as e:
            logger.error(f"서비스 상태 확인 실패: {e}")
            return {
                'status': 'unknown',
                'healthy': False,
                'message': f'확인 실패: {str(e)}'
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """디스크 공간 확인"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_dir)
            usage_percent = (used / total) * 100
            
            return {
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'usage_percent': round(usage_percent, 2),
                'healthy': usage_percent < 90,
                'warning': usage_percent > 80,
                'message': f'디스크 사용량: {usage_percent:.1f}%'
            }
        except Exception as e:
            logger.error(f"디스크 공간 확인 실패: {e}")
            return {
                'healthy': False,
                'message': f'확인 실패: {str(e)}'
            }
    
    def check_backup_status(self) -> Dict[str, Any]:
        """백업 상태 확인"""
        try:
            if not os.path.exists(self.backup_dir):
                return {
                    'healthy': False,
                    'backup_count': 0,
                    'latest_backup': None,
                    'message': '백업 디렉토리가 없습니다'
                }
            
            # 최근 24시간 내 백업 확인
            backup_files = list(Path(self.backup_dir).glob('*.db'))
            recent_backups = [
                f for f in backup_files
                if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).total_seconds() < 86400
            ]
            
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime) if backup_files else None
            
            return {
                'healthy': len(recent_backups) > 0,
                'backup_count': len(backup_files),
                'recent_backup_count': len(recent_backups),
                'latest_backup': latest_backup.name if latest_backup else None,
                'latest_backup_age_hours': round(
                    (datetime.now() - datetime.fromtimestamp(latest_backup.stat().st_mtime)).total_seconds() / 3600, 1
                ) if latest_backup else None,
                'message': f'최근 백업: {len(recent_backups)}개 (전체: {len(backup_files)}개)'
            }
        except Exception as e:
            logger.error(f"백업 상태 확인 실패: {e}")
            return {
                'healthy': False,
                'message': f'확인 실패: {str(e)}'
            }
    
    def verify_backup_integrity(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """백업 파일 무결성 검증"""
        try:
            if backup_path is None:
                # 최신 백업 파일 찾기
                backup_files = list(Path(self.backup_dir).glob('*.db'))
                if not backup_files:
                    return {
                        'healthy': False,
                        'message': '백업 파일이 없습니다'
                    }
                backup_path = max(backup_files, key=lambda f: f.stat().st_mtime)
            
            # SQLite 무결성 검사
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            
            is_valid = result and result[0] == 'ok'
            
            return {
                'healthy': is_valid,
                'backup_file': os.path.basename(backup_path),
                'message': '백업 파일 무결성 검증 성공' if is_valid else '백업 파일 무결성 검증 실패'
            }
        except Exception as e:
            logger.error(f"백업 무결성 검증 실패: {e}")
            return {
                'healthy': False,
                'message': f'검증 실패: {str(e)}'
            }
    
    def get_safety_report(self) -> Dict[str, Any]:
        """전체 안전장치 상태 리포트"""
        return {
            'timestamp': datetime.now().isoformat(),
            'service': self.check_service_status(),
            'disk': self.check_disk_space(),
            'backup': self.check_backup_status(),
            'backup_integrity': self.verify_backup_integrity()
        }


# 전역 인스턴스
deployment_safety = DeploymentSafetyMonitor()

