import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable
from core.version_manager import version_manager

class ChangeDetector:
    """파일 변경 감지 및 자동 버전 생성 시스템"""
    
    def __init__(self):
        self.watched_files = set()
        self.file_timestamps = {}
        self.change_callbacks = []
        self.is_running = False
        self.scan_interval = 30  # 30초마다 스캔
        self.scan_thread = None
        
    def add_change_callback(self, callback: Callable):
        """변경 감지 콜백 함수 추가"""
        self.change_callbacks.append(callback)
    
    def scan_project_files(self) -> Dict[str, float]:
        """프로젝트 파일들의 타임스탬프 스캔"""
        project_root = os.path.dirname(os.path.dirname(__file__))
        file_timestamps = {}
        
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
            # 백업 디렉토리, 캐시 디렉토리 제외
            if any(exclude in root for exclude in ['backups', '__pycache__', '.git', 'node_modules']):
                continue
                
            for file in files:
                if any(file.endswith(pattern.replace('*', '')) for pattern in scan_patterns):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_root)
                    
                    try:
                        mtime = os.path.getmtime(file_path)
                        file_timestamps[relative_path] = mtime
                    except:
                        continue
        
        return file_timestamps
    
    def detect_changes(self) -> List[str]:
        """변경된 파일들 감지"""
        current_timestamps = self.scan_project_files()
        changed_files = []
        
        for file_path, current_mtime in current_timestamps.items():
            last_mtime = self.file_timestamps.get(file_path, 0)
            
            if current_mtime > last_mtime:
                changed_files.append(file_path)
                self.file_timestamps[file_path] = current_mtime
        
        return changed_files
    
    def on_files_changed(self, changed_files: List[str]):
        """파일 변경 시 호출되는 함수"""
        if not changed_files:
            return
        
        print(f"변경 감지: {len(changed_files)}개 파일")
        
        # 변경된 파일들 출력
        for file_path in changed_files[:5]:  # 최대 5개만 표시
            print(f"  파일: {file_path}")
        
        if len(changed_files) > 5:
            print(f"  ... 외 {len(changed_files) - 5}개 파일")
        
        # 콜백 함수들 실행
        for callback in self.change_callbacks:
            try:
                callback(changed_files)
            except Exception as e:
                print(f"콜백 실행 오류: {e}")
    
    def auto_version_callback(self, changed_files: List[str]):
        """자동 버전 생성 콜백"""
        # 중요한 파일들만 변경되었을 때 자동 버전 생성
        important_files = [
            'app.py',
            'routes/',
            'core/',
            'templates/',
            'database/schema.sql'
        ]
        
        has_important_changes = any(
            any(important in file_path for important in important_files)
            for file_path in changed_files
        )
        
        if has_important_changes:
            description = f"자동 변경 감지 ({len(changed_files)}개 파일)"
            version_number = version_manager.auto_create_version(description)
            if version_number:
                print(f"자동 버전 생성: {version_number}")
    
    def start_monitoring(self):
        """변경 감지 모니터링 시작"""
        if self.is_running:
            return
        
        print("파일 변경 감지 모니터링 시작...")
        
        # 초기 파일 상태 스캔
        self.file_timestamps = self.scan_project_files()
        print(f"모니터링 파일 수: {len(self.file_timestamps)}개")
        
        # 자동 버전 생성 콜백 등록
        self.add_change_callback(self.auto_version_callback)
        
        self.is_running = True
        self.scan_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.scan_thread.start()
    
    def stop_monitoring(self):
        """변경 감지 모니터링 중지"""
        self.is_running = False
        if self.scan_thread:
            self.scan_thread.join()
        print("파일 변경 감지 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.is_running:
            try:
                changed_files = self.detect_changes()
                if changed_files:
                    self.on_files_changed(changed_files)
                
                time.sleep(self.scan_interval)
                
            except Exception as e:
                print(f"모니터링 오류: {e}")
                time.sleep(self.scan_interval)
    
    def force_scan(self) -> List[str]:
        """강제 스캔 실행"""
        changed_files = self.detect_changes()
        if changed_files:
            self.on_files_changed(changed_files)
        return changed_files

# 전역 변경 감지기 인스턴스
change_detector = ChangeDetector()
