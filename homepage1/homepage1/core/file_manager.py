"""
파일 관리 시스템
- 불필요한 파일 자동 삭제
- 기능별 폴더 관리
- 업데이트 효율성 향상
- 파일 이동 검증 및 자동 복구
"""

import os
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set
import json
from core.file_validator import file_validator
from core.notification_system import notification_system

class FileManager:
    """체계적인 파일 관리 시스템"""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.config_file = os.path.join(root_path, 'file_manager_config.json')
        self.config = self._load_config()
        self.report_only = self.config.get('report_only', True)
        
        # 기능별 폴더 구조
        self.folder_structure = {
            'core': '핵심 기능 (db, responses, etc)',
            'routes': '라우팅 (home, admin, conversion)',
            'templates': '템플릿 파일들',
            'static': '정적 파일들 (CSS, JS)',
            'database': '데이터베이스 관련',
            'tests': '테스트 파일들',
            'docs': '문서화 파일들',
            'backup': '백업 파일들',
            'temp': '임시 파일들',
            'logs': '로그 파일들'
        }
        
        # 자동 삭제 대상 파일 패턴
        self.auto_delete_patterns = [
            '*.tmp',
            '*.temp',
            '*.cache',
            '*.pyc',
            '__pycache__',
            '.DS_Store',
            'Thumbs.db',
            '*.bak',
            '*.old'
        ]
        
        # 로그 파일 패턴 (사용 중인 파일 제외)
        self.log_patterns = [
            '*.log'
        ]
        
        # 보호할 파일 패턴
        self.protected_patterns = [
            '*.py',
            '*.html',
            '*.css',
            '*.js',
            '*.json',
            '*.md',
            '*.sql',
            '*.txt'
        ]
        
        # 절대 건드리면 안 되는 파일 패턴 (DB, 백업 등)
        self.critical_protected_patterns = [
            '*.db',
            '*.sqlite',
            '*.sqlite3',
            '*.log',
            '*backup*',
            '*.bak'
        ]
    
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_cleanup': None,
            'auto_delete_enabled': True,  # 자동 정리 활성화
            'folder_management_enabled': False,
            'cleanup_interval_hours': 24,
            'report_only': False,
            # output 보관 정책
            'output_keep_last_n': 5,
            'output_patterns': ['output/*.xlsx', 'output/*.csv']
        }
    
    def _save_config(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def organize_files_by_function(self):
        """기능별로 파일 정리 (검증 및 복구 포함)"""
        print("📁 기능별 파일 정리 시작...")
        
        for folder_name, description in self.folder_structure.items():
            folder_path = os.path.join(self.root_path, folder_name)
            
            # 폴더가 없으면 생성
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"✅ {folder_name} 폴더 생성: {description}")
            
            # 보고 전용: 실제 이동은 하지 않고 대상만 로그로 표시
            self._safe_move_files_to_folder(folder_name, folder_path)
        
        print("📁 기능별 파일 정리 완료!")
    
    def _is_critically_protected(self, file_path: str) -> bool:
        """중요 파일 보호 여부 확인 (DB, 백업 등)"""
        filename = os.path.basename(file_path).lower()
        
        # 데이터베이스 파일들 절대 보호
        if filename.endswith(('.db', '.sqlite', '.sqlite3')):
            return True
        
        # 로그 파일들 보호
        if filename.endswith('.log'):
            return True
        
        # 백업 파일들 보호
        if 'backup' in filename or filename.endswith('.bak'):
            return True
            
        return False

    def _is_file_in_use(self, file_path: str) -> bool:
        """파일이 사용 중인지 확인"""
        try:
            # 중요 파일들은 무조건 건너뜀
            if self._is_critically_protected(file_path):
                return True
                
            # 파일을 열어서 사용 중인지 확인
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (PermissionError, OSError):
            return True
        except:
            return False

    def _safe_move_files_to_folder(self, folder_name: str, folder_path: str):
        """기능 폴더 대상 파일 스캔 및 보고 (보고 전용: 실제 이동 안 함)"""
        file_patterns = {
            'core': ['core/*.py', 'core/*.json'],
            'routes': ['routes/*.py'],
            'templates': ['templates/*.html'],
            'static': ['*.css', '*.js', '*.png', '*.jpg', '*.gif', '*.ico'],
            'database': ['database/*.sql', 'database/*.db'],
            'tests': ['test_*.py', 'tests/*.py'],
            'docs': ['*.md', 'README*.txt', 'VERSION*.md', 'UPDATE*.md'],
            'backup': ['backup/*', '*.bak'],
            'temp': ['*.tmp', '*.temp'],
            'logs': ['*.log']
        }

        patterns = file_patterns.get(folder_name, [])
        for pattern in patterns:
            import glob
            files = glob.glob(os.path.join(self.root_path, pattern))
            for file_path in files:
                if not os.path.isfile(file_path):
                    continue
                
                # 중요 파일들은 절대 건드리지 않음
                if self._is_critically_protected(file_path):
                    print(f"중요 파일 보호: {os.path.basename(file_path)}")
                    continue
                    
                if self._is_file_in_use(file_path):
                    print(f"파일 사용 중으로 건너뜀: {os.path.basename(file_path)}")
                    continue
                filename = os.path.basename(file_path)
                target_path = os.path.join(folder_path, filename)
                # 보고 전용: 실제 이동 금지
                print(f"[REPORT-ONLY] 이동 대상: {filename} → {target_path}")
    
    def _safe_move_file(self, file_path: str, target_path: str, target_folder: str):
        """안전한 파일 이동 (검증 및 복구 포함)"""
        filename = os.path.basename(file_path)
        
        try:
            # 보고 전용 모드에서는 이동하지 않음
            if self.report_only:
                print(f"ℹ️ [REPORT-ONLY] 이동 생략: {filename} → {target_path}")
                return True
            # 1. 목적지 경로 검증
            is_valid, validation_message = file_validator.validate_destination_path(file_path, target_folder)
            
            if not is_valid:
                notification_system.send_validation_notification(file_path, False, validation_message)
                print(f"❌ {filename} 이동 검증 실패: {validation_message}")
                return False
            
            # 2. 파일 이동
            shutil.move(file_path, target_path)
            print(f"📁 {filename} → .\\{target_folder}")
            
            # 3. 웹 접근성 검증 (웹 파일인 경우)
            is_web_accessible, web_message = file_validator.validate_web_accessibility(file_path, target_path)
            
            if not is_web_accessible:
                notification_system.send_web_access_failure_notification(file_path, "", web_message)
                print(f"⚠️ 웹 접근 실패: {web_message}")
                
                # 4. 자동 복구 시도
                recovery_success, recovery_message = file_validator.auto_recover_file(file_path, target_path)
                
                if recovery_success:
                    notification_system.send_auto_recovery_notification(file_path, target_path, True)
                    print(f"✅ 자동 복구 성공: {recovery_message}")
                else:
                    notification_system.send_auto_recovery_notification(file_path, target_path, False)
                    print(f"❌ 자동 복구 실패: {recovery_message}")
                    return False
            else:
                notification_system.send_file_move_notification(file_path, target_path, True)
                print(f"✅ 웹 접근 확인: {web_message}")
            
            # 5. 검증 로그 기록
            file_validator.log_validation(file_path, target_path, True, f"성공적으로 이동됨: {target_folder}")
            
            return True
            
        except Exception as e:
            error_message = f"파일 이동 중 오류 발생: {str(e)}"
            notification_system.send_file_move_notification(file_path, target_path, False)
            notification_system.send_validation_notification(file_path, False, error_message)
            file_validator.log_validation(file_path, target_path, False, error_message)
            print(f"❌ {filename} 이동 실패: {e}")
            return False
    
    def _move_files_to_folder(self, folder_name: str, folder_path: str):
        """특정 폴더로 파일 이동"""
        file_patterns = {
            'core': ['core/*.py', 'core/*.json'],
            'routes': ['routes/*.py'],
            'templates': ['templates/*.html'],
            'static': ['*.css', '*.js', '*.png', '*.jpg', '*.gif', '*.ico'],
            'database': ['database/*.sql', 'database/*.db'],
            'tests': ['test_*.py', 'tests/*.py'],
            'docs': ['*.md', 'README*', 'VERSION*'],
            'backup': ['backup_*', '*_backup*'],
            'temp': ['temp_*', '*_temp*'],
            'logs': ['*.log', 'logs/*']
        }
        
        if folder_name in file_patterns:
            patterns = file_patterns[folder_name]
            for pattern in patterns:
                self._move_files_by_pattern(pattern, folder_path)
    
    def _move_files_by_pattern(self, pattern: str, target_folder: str):
        """패턴에 맞는 파일들을 대상 폴더로 이동"""
        import glob
        
        # 패턴에서 폴더 부분 제거
        if '/' in pattern:
            folder_part, file_part = pattern.split('/', 1)
            search_path = os.path.join(self.root_path, pattern)
        else:
            search_path = os.path.join(self.root_path, pattern)
        
        files = glob.glob(search_path)
        
        for file_path in files:
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                
                # CSS 파일은 static/css 폴더로 이동
                if filename.endswith('.css'):
                    css_folder = os.path.join(target_folder, 'css')
                    if not os.path.exists(css_folder):
                        os.makedirs(css_folder)
                    target_path = os.path.join(css_folder, filename)
                else:
                    target_path = os.path.join(target_folder, filename)
                
                # 대상 폴더에 같은 이름의 파일이 없을 때만 이동
                if not os.path.exists(target_path):
                    try:
                        shutil.move(file_path, target_path)
                        print(f"📁 {filename} → {os.path.dirname(target_path)}")
                    except Exception as e:
                        print(f"❌ {filename} 이동 실패: {e}")
    
    def auto_cleanup(self):
        """자동 정리 실행"""
        print("🧹 자동 정리 시작...")
        if self.report_only:
            print("ℹ️ [REPORT-ONLY] 자동 정리 생략 (삭제/이동 없음)")
            self.config['last_cleanup'] = datetime.now().isoformat()
            self._save_config()
            return
        
        deleted_count = 0
        for pattern in self.auto_delete_patterns:
            deleted_count += self._delete_files_by_pattern(pattern)
        
        # 로그 파일 정리 (사용 중인 파일 제외)
        log_deleted_count = self._cleanup_log_files()
        deleted_count += log_deleted_count

        # output 보관 정책: 최신 N개만 유지
        deleted_count += self._prune_output_keep_last_n()
        
        if deleted_count > 0:
            print(f"ℹ️ [REPORT-ONLY] 정리 대상: {deleted_count}개 파일")
        
        # 설정 업데이트
        self.config['last_cleanup'] = datetime.now().isoformat()
        self._save_config()
    
    def _cleanup_log_files(self) -> int:
        """로그 파일 정리 (사용 중인 파일 제외)"""
        import glob
        
        deleted_count = 0
        if self.report_only:
            # 보고 전용: 삭제 대신 보고만
            for pattern in self.log_patterns:
                search_path = os.path.join(self.root_path, '**', pattern)
                files = glob.glob(search_path, recursive=True)
                for file_path in files:
                    if os.path.isfile(file_path):
                        print(f"ℹ️ [REPORT-ONLY] 로그 삭제 대상: {os.path.basename(file_path)}")
            return 0
        for pattern in self.log_patterns:
            search_path = os.path.join(self.root_path, '**', pattern)
            files = glob.glob(search_path, recursive=True)
            
            for file_path in files:
                if os.path.isfile(file_path):
                    try:
                        # 파일이 사용 중인지 확인
                        with open(file_path, 'a'):
                            pass
                        # 사용 중이 아니면 삭제
                        os.remove(file_path)
                        print(f"ℹ️ [REPORT-ONLY] 로그 정리 대상: {os.path.basename(file_path)}")
                        deleted_count += 1
                    except (OSError, IOError):
                        # 파일이 사용 중이면 건너뛰기
                        print(f"⏭️ 로그 파일 사용 중: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"❌ 로그 삭제 실패: {file_path} - {e}")
        
        return deleted_count

    def _prune_output_keep_last_n(self) -> int:
        """output 폴더 산출물: 최근 N개만 보관하고 나머지 삭제"""
        import glob
        keep_n = int(self.config.get('output_keep_last_n', 5))
        patterns = self.config.get('output_patterns', ['output/*.xlsx'])
        total_deleted = 0
        for pattern in patterns:
            files = glob.glob(os.path.join(self.root_path, pattern))
            files = [f for f in files if os.path.isfile(f)]
            # 최근 수정 순으로 정렬
            files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            to_delete = files[keep_n:]
            for f in to_delete:
                try:
                    os.remove(f)
                    print(f"🗑️ output 정리: {os.path.basename(f)}")
                    total_deleted += 1
                except Exception as e:
                    print(f"❌ output 삭제 실패: {f} - {e}")
        return total_deleted
    
    def _delete_files_by_pattern(self, pattern: str) -> int:
        """패턴에 맞는 파일들 삭제"""
        import glob
        
        deleted_count = 0
        if self.report_only:
            # 보고 전용: 삭제 대상만 로그
            search_path = os.path.join(self.root_path, '**', pattern)
            files = glob.glob(search_path, recursive=True)
            for file_path in files:
                # 중요 파일들은 삭제 대상에서도 제외
                if self._is_critically_protected(file_path):
                    print(f"중요 파일 보호 (삭제 대상 제외): {os.path.basename(file_path)}")
                    continue
                print(f"[REPORT-ONLY] 삭제 대상: {file_path}")
            return 0
        search_path = os.path.join(self.root_path, '**', pattern)
        files = glob.glob(search_path, recursive=True)
        
        for file_path in files:
            if os.path.isfile(file_path):
                # 중요 파일들은 절대 삭제하지 않음
                if self._is_critically_protected(file_path):
                    print(f"중요 파일 보호 (삭제 금지): {os.path.basename(file_path)}")
                    continue
                    
                try:
                    os.remove(file_path)
                    print(f"삭제: {os.path.basename(file_path)}")
                    deleted_count += 1
                except Exception as e:
                    print(f"삭제 실패: {file_path} - {e}")
            elif os.path.isdir(file_path):
                # 백업 폴더는 절대 삭제하지 않음
                if 'backup' in file_path.lower():
                    print(f"백업 폴더 보호 (삭제 금지): {os.path.basename(file_path)}")
                    continue
                    
                try:
                    shutil.rmtree(file_path)
                    print(f"폴더 삭제: {os.path.basename(file_path)}")
                    deleted_count += 1
                except Exception as e:
                    print(f"폴더 삭제 실패: {file_path} - {e}")
        
        return deleted_count
    
    def should_run_cleanup(self) -> bool:
        """정리 실행 여부 확인"""
        if not self.config.get('auto_delete_enabled', True):
            return False
        
        last_cleanup = self.config.get('last_cleanup')
        if not last_cleanup:
            return True
        
        try:
            last_cleanup_time = datetime.fromisoformat(last_cleanup)
            interval_hours = self.config.get('cleanup_interval_hours', 24)
            
            return datetime.now() - last_cleanup_time > timedelta(hours=interval_hours)
        except:
            return True
    
    def get_file_statistics(self) -> Dict:
        """파일 통계 정보"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_folder': {},
            'by_type': {}
        }
        
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    
                    # 폴더별 통계
                    folder_name = os.path.basename(root)
                    if folder_name not in stats['by_folder']:
                        stats['by_folder'][folder_name] = {'count': 0, 'size': 0}
                    stats['by_folder'][folder_name]['count'] += 1
                    stats['by_folder'][folder_name]['size'] += file_size
                    
                    # 파일 타입별 통계
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext not in stats['by_type']:
                        stats['by_type'][file_ext] = {'count': 0, 'size': 0}
                    stats['by_type'][file_ext]['count'] += 1
                    stats['by_type'][file_ext]['size'] += file_size
                    
                except Exception:
                    pass
        
        return stats
    
    def create_backup(self, backup_name: str = None):
        """백업 생성"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.root_path, 'backup', backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        # 중요한 파일들만 백업
        important_files = [
            'app.py',
            'core/',
            'routes/',
            'templates/',
            'database/',
            'static/',
            '절대지침/'
        ]
        
        for item in important_files:
            source_path = os.path.join(self.root_path, item)
            target_path = os.path.join(backup_path, item)
            
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.copytree(source_path, target_path)
        
        print(f"💾 백업 생성 완료: {backup_name}")
        return backup_path
    
    def restore_from_backup(self, backup_name: str):
        """백업에서 복원"""
        backup_path = os.path.join(self.root_path, 'backup', backup_name)
        
        if not os.path.exists(backup_path):
            print(f"❌ 백업을 찾을 수 없습니다: {backup_name}")
            return False
        
        # 현재 파일들을 임시 폴더로 이동
        temp_path = os.path.join(self.root_path, 'temp', f"restore_temp_{int(time.time())}")
        os.makedirs(temp_path, exist_ok=True)
        
        # 백업에서 복원
        for item in os.listdir(backup_path):
            source_path = os.path.join(backup_path, item)
            target_path = os.path.join(self.root_path, item)
            
            if os.path.exists(target_path):
                shutil.move(target_path, os.path.join(temp_path, item))
            
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
            else:
                shutil.copytree(source_path, target_path)
        
        print(f"🔄 백업에서 복원 완료: {backup_name}")
        return True


# 사용 예시
if __name__ == "__main__":
    # 파일 관리자 초기화
    file_manager = FileManager(".")
    
    # 파일 통계 확인
    stats = file_manager.get_file_statistics()
    print("📊 파일 통계:")
    print(f"  총 파일 수: {stats['total_files']}")
    print(f"  총 크기: {stats['total_size'] / 1024 / 1024:.2f} MB")
    
    # 기능별 파일 정리
    if file_manager.config.get('folder_management_enabled', True):
        file_manager.organize_files_by_function()
    
    # 자동 정리 실행
    if file_manager.should_run_cleanup():
        file_manager.auto_cleanup()
    
    # 백업 생성
    backup_path = file_manager.create_backup()
    print(f"💾 백업 경로: {backup_path}")
