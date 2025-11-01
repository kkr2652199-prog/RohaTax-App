"""
자동 백업 설정 및 모니터링 시작
- 핵심 파일들 자동 백업 설정
- 실시간 모니터링 시작
- 백업 정책 관리
"""

import os
import logging
from pathlib import Path
from core.auto_backup_manager import auto_backup_manager
from core.file_change_monitor import file_change_monitor

class BackupSetup:
    """자동 백업 설정 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def setup_core_files_backup(self):
        """핵심 파일들 자동 백업 설정"""
        try:
            # 핵심 파일 목록
            core_files = [
                "core/conversion_engine.py",
                "core/file_parser.py", 
                "core/hometax_template_generator.py",
                "core/recipient_extractor/main_extractor.py",
                "routes/conversion.py",
                "static/js/conversion.js",
                "static/css/conversion.css",
                "app.py",
                "config/industry_config.json"
            ]
            
            # 각 파일에 대해 모니터링 설정
            for file_path in core_files:
                if os.path.exists(file_path):
                    # 백업 정책 설정
                    backup_policy = {
                        'auto_backup': True,
                        'backup_reason': 'core_file_change',
                        'max_backups': 15  # 핵심 파일은 더 많은 백업 유지
                    }
                    
                    file_change_monitor.add_file(file_path, backup_policy)
                    self.logger.info(f"✅ 핵심 파일 백업 설정: {file_path}")
                else:
                    self.logger.warning(f"⚠️ 파일이 존재하지 않음: {file_path}")
            
            self.logger.info(f"🎯 핵심 파일 {len(core_files)}개 자동 백업 설정 완료")
            
        except Exception as e:
            self.logger.error(f"핵심 파일 백업 설정 오류: {str(e)}")
    
    def setup_guideline_files_backup(self):
        """지침 파일들 자동 백업 설정"""
        try:
            # 지침 파일 목록
            guideline_files = [
                "절대지침/공급받는자정보관리지침/공급받는자_통합관리_절대지침.md",
                "절대지침/업종별절대지침/배달대행사_정산서_절대지침.md",
                "절대지침/검증규칙/데이터검증규칙.md"
            ]
            
            # 각 파일에 대해 모니터링 설정
            for file_path in guideline_files:
                if os.path.exists(file_path):
                    # 백업 정책 설정
                    backup_policy = {
                        'auto_backup': True,
                        'backup_reason': 'guideline_change',
                        'max_backups': 20  # 지침 파일은 더 많은 백업 유지
                    }
                    
                    file_change_monitor.add_file(file_path, backup_policy)
                    self.logger.info(f"✅ 지침 파일 백업 설정: {file_path}")
                else:
                    self.logger.warning(f"⚠️ 파일이 존재하지 않음: {file_path}")
            
            self.logger.info(f"📋 지침 파일 {len(guideline_files)}개 자동 백업 설정 완료")
            
        except Exception as e:
            self.logger.error(f"지침 파일 백업 설정 오류: {str(e)}")
    
    def setup_template_files_backup(self):
        """템플릿 파일들 자동 백업 설정"""
        try:
            # 템플릿 파일 목록
            template_files = [
                "templates/conversion.html",
                "templates/admin.html",
                "templates/base.html"
            ]
            
            # 각 파일에 대해 모니터링 설정
            for file_path in template_files:
                if os.path.exists(file_path):
                    # 백업 정책 설정
                    backup_policy = {
                        'auto_backup': True,
                        'backup_reason': 'template_change',
                        'max_backups': 10
                    }
                    
                    file_change_monitor.add_file(file_path, backup_policy)
                    self.logger.info(f"✅ 템플릿 파일 백업 설정: {file_path}")
                else:
                    self.logger.warning(f"⚠️ 파일이 존재하지 않음: {file_path}")
            
            self.logger.info(f"🎨 템플릿 파일 {len(template_files)}개 자동 백업 설정 완료")
            
        except Exception as e:
            self.logger.error(f"템플릿 파일 백업 설정 오류: {str(e)}")
    
    def setup_all_backups(self):
        """모든 파일 자동 백업 설정"""
        try:
            self.logger.info("🔄 전체 자동 백업 설정 시작")
            
            # 각 카테고리별 백업 설정
            self.setup_core_files_backup()
            self.setup_guideline_files_backup()
            self.setup_template_files_backup()
            
            # 변경 콜백 함수 추가
            file_change_monitor.add_change_callback(self._on_file_changed)
            
            self.logger.info("✅ 전체 자동 백업 설정 완료")
            
        except Exception as e:
            self.logger.error(f"전체 백업 설정 오류: {str(e)}")
    
    def _on_file_changed(self, file_path: str, status: str):
        """파일 변경 시 콜백 함수"""
        try:
            if status == "modified":
                self.logger.info(f"🔄 파일 수정 감지: {file_path}")
            elif status == "deleted":
                self.logger.warning(f"🗑️ 파일 삭제 감지: {file_path}")
                
        except Exception as e:
            self.logger.error(f"파일 변경 콜백 오류: {str(e)}")
    
    def get_backup_status(self) -> dict:
        """백업 상태 반환"""
        try:
            status = file_change_monitor.get_monitoring_status()
            
            # 백업 파일 통계 추가
            backup_files = auto_backup_manager.list_backups()
            status['total_backups'] = len(backup_files)
            status['backup_dir'] = str(auto_backup_manager.backup_dir)
            
            return status
            
        except Exception as e:
            self.logger.error(f"백업 상태 조회 오류: {str(e)}")
            return {}

# 전역 인스턴스
backup_setup = BackupSetup()







