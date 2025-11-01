#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 환경 진단 도구
==================

1Tax App 서버 시작 문제를 진단하고 해결 방법을 제시하는 종합 진단 도구입니다.
Python 3.14.0 환경에서 안정적으로 동작하도록 설계되었습니다.
"""

import os
import sys
import subprocess
import platform
import socket
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import logging
from datetime import datetime

class SystemDiagnostic:
    """시스템 환경 진단 도구"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        self.diagnostic_results = {}
        
        self.logger.info("🔍 시스템 진단 도구 초기화 완료")

    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('system_diagnostic.log', encoding='utf-8')
            ]
        )
        return logging.getLogger(__name__)

    def check_python_version(self) -> Dict[str, any]:
        """Python 버전 및 설치 상태 확인"""
        result = {
            'status': 'success',
            'python_version': sys.version,
            'python_executable': sys.executable,
            'python_path': sys.path,
            'available_versions': [],
            'issues': []
        }
        
        try:
            # Python 버전 확인
            version_info = sys.version_info
            result['version_major'] = version_info.major
            result['version_minor'] = version_info.minor
            result['version_micro'] = version_info.micro
            
            # 권장 버전 확인 (Python 3.14.0)
            if version_info.major == 3 and version_info.minor >= 14:
                result['recommended_version'] = True
            else:
                result['recommended_version'] = False
                result['issues'].append(f"권장 버전: Python 3.14.0, 현재: {version_info.major}.{version_info.minor}.{version_info.micro}")
            
            # py launcher로 사용 가능한 버전 확인
            try:
                py_result = subprocess.run(['py', '-0'], capture_output=True, text=True, check=True)
                result['available_versions'] = py_result.stdout.strip().split('\n')
            except subprocess.CalledProcessError:
                result['issues'].append("py launcher를 사용할 수 없습니다")
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result

    def check_installed_packages(self) -> Dict[str, any]:
        """설치된 패키지 확인"""
        result = {
            'status': 'success',
            'installed_packages': {},
            'missing_packages': [],
            'version_conflicts': [],
            'issues': []
        }
        
        try:
            # pip list 실행
            pip_result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, check=True
            )
            
            installed_packages = json.loads(pip_result.stdout)
            result['installed_packages'] = {
                pkg['name'].lower(): pkg['version'] 
                for pkg in installed_packages
            }
            
            # 필수 패키지 확인
            required_packages = {
                'flask': '3.1.2',
                'pandas': '2.3.3',
                'openpyxl': '3.1.5',
                'requests': '2.32.5',
                'psutil': '7.1.1'
            }
            
            for package, expected_version in required_packages.items():
                if package not in result['installed_packages']:
                    result['missing_packages'].append(package)
                else:
                    installed_version = result['installed_packages'][package]
                    if installed_version != expected_version:
                        result['version_conflicts'].append({
                            'package': package,
                            'expected': expected_version,
                            'installed': installed_version
                        })
        
        except subprocess.CalledProcessError as e:
            result['status'] = 'error'
            result['error'] = f"pip list 실행 실패: {e}"
        except json.JSONDecodeError as e:
            result['status'] = 'error'
            result['error'] = f"JSON 파싱 오류: {e}"
        
        return result

    def check_project_structure(self) -> Dict[str, any]:
        """프로젝트 구조 확인"""
        result = {
            'status': 'success',
            'project_files': {},
            'missing_files': [],
            'issues': []
        }
        
        # 필수 파일 목록
        required_files = [
            'app.py',
            'requirements.txt',
            'start_server.bat',
            'check_dependencies.py',
            'diagnose_system.py'
        ]
        
        # 필수 디렉토리 목록
        required_dirs = [
            'core',
            'config',
            'routes',
            'templates',
            'static'
        ]
        
        # 파일 존재 확인
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                result['project_files'][file_name] = {
                    'exists': True,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                }
            else:
                result['missing_files'].append(file_name)
                result['issues'].append(f"필수 파일 누락: {file_name}")
        
        # 디렉토리 존재 확인
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                result['project_files'][dir_name] = {
                    'exists': True,
                    'is_directory': True,
                    'file_count': len(list(dir_path.iterdir()))
                }
            else:
                result['missing_files'].append(dir_name)
                result['issues'].append(f"필수 디렉토리 누락: {dir_name}")
        
        return result

    def check_port_availability(self, port: int = 3000) -> Dict[str, any]:
        """포트 사용 가능성 확인"""
        result = {
            'status': 'success',
            'port': port,
            'available': True,
            'process_info': None,
            'issues': []
        }
        
        try:
            # 소켓으로 포트 확인
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('localhost', port)) == 0:
                    result['available'] = False
                    result['issues'].append(f"포트 {port}이 이미 사용 중입니다")
                    
                    # 사용 중인 프로세스 확인
                    try:
                        netstat_result = subprocess.run(
                            ['netstat', '-ano'], 
                            capture_output=True, text=True, check=True
                        )
                        
                        for line in netstat_result.stdout.split('\n'):
                            if f':{port}' in line and 'LISTENING' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    pid = parts[-1]
                                    result['process_info'] = {'pid': pid}
                                    
                                    # 프로세스 이름 확인
                                    try:
                                        tasklist_result = subprocess.run(
                                            ['tasklist', '/FI', f'PID eq {pid}'],
                                            capture_output=True, text=True, check=True
                                        )
                                        result['process_info']['name'] = tasklist_result.stdout
                                    except:
                                        pass
                                    break
                    except subprocess.CalledProcessError:
                        pass
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result

    def check_path_encoding(self) -> Dict[str, any]:
        """경로 인코딩 문제 확인"""
        result = {
            'status': 'success',
            'current_directory': str(self.project_root),
            'encoding_issues': [],
            'korean_path_detected': False,
            'issues': []
        }
        
        try:
            # 현재 경로에 한국어 포함 여부 확인
            current_path = str(self.project_root)
            korean_chars = any('\uac00' <= char <= '\ud7af' for char in current_path)
            result['korean_path_detected'] = korean_chars
            
            if korean_chars:
                result['issues'].append("한국어 경로가 감지되었습니다. PowerShell에서 문제가 발생할 수 있습니다.")
                result['encoding_issues'].append({
                    'type': 'korean_path',
                    'path': current_path,
                    'recommendation': '영문 경로로 프로젝트 이동 또는 배치 파일 사용 권장'
                })
            
            # 파일 시스템 인코딩 확인
            result['filesystem_encoding'] = sys.getfilesystemencoding()
            result['default_encoding'] = sys.getdefaultencoding()
            
            # 테스트 파일 생성/삭제로 인코딩 테스트
            test_file = self.project_root / 'encoding_test.tmp'
            try:
                test_file.write_text('테스트', encoding='utf-8')
                content = test_file.read_text(encoding='utf-8')
                test_file.unlink()
                
                if content != '테스트':
                    result['encoding_issues'].append({
                        'type': 'file_encoding',
                        'issue': '파일 인코딩 문제 감지'
                    })
            except Exception as e:
                result['encoding_issues'].append({
                    'type': 'file_encoding',
                    'issue': f'파일 인코딩 테스트 실패: {e}'
                })
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result

    def check_system_resources(self) -> Dict[str, any]:
        """시스템 리소스 확인"""
        result = {
            'status': 'success',
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'memory_info': {},
            'disk_info': {},
            'issues': []
        }
        
        try:
            # 메모리 정보
            import psutil
            memory = psutil.virtual_memory()
            result['memory_info'] = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            }
            
            # 디스크 정보
            disk = psutil.disk_usage(str(self.project_root))
            result['disk_info'] = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
            
            # 리소스 부족 경고
            if memory.percent > 90:
                result['issues'].append("메모리 사용률이 90%를 초과했습니다")
            
            if disk.percent > 90:
                result['issues'].append("디스크 사용률이 90%를 초과했습니다")
        
        except ImportError:
            result['issues'].append("psutil이 설치되지 않아 시스템 리소스 정보를 확인할 수 없습니다")
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result

    def run_full_diagnostic(self) -> Dict[str, any]:
        """전체 시스템 진단 실행"""
        self.logger.info("🚀 전체 시스템 진단 시작")
        
        diagnostic_results = {
            'timestamp': datetime.now().isoformat(),
            'python_version': self.check_python_version(),
            'installed_packages': self.check_installed_packages(),
            'project_structure': self.check_project_structure(),
            'port_availability': self.check_port_availability(),
            'path_encoding': self.check_path_encoding(),
            'system_resources': self.check_system_resources()
        }
        
        # 전체 상태 평가
        all_checks_passed = all(
            result.get('status') == 'success' 
            for result in diagnostic_results.values() 
            if isinstance(result, dict) and 'status' in result
        )
        
        diagnostic_results['overall_status'] = 'success' if all_checks_passed else 'warning'
        
        return diagnostic_results

    def print_diagnostic_report(self, results: Dict[str, any]):
        """진단 결과 리포트 출력"""
        print("=" * 60)
        print("🔍 1Tax App 시스템 진단 리포트")
        print("=" * 60)
        print(f"📅 진단 시간: {results['timestamp']}")
        print()
        
        # Python 버전
        py_info = results['python_version']
        print("🐍 Python 환경")
        print(f"  버전: {py_info.get('python_version', 'N/A')}")
        print(f"  실행 파일: {py_info.get('python_executable', 'N/A')}")
        if py_info.get('recommended_version'):
            print("  ✅ 권장 버전 사용 중")
        else:
            print("  ⚠️ 권장 버전이 아닙니다")
        if py_info.get('issues'):
            for issue in py_info['issues']:
                print(f"  ❌ {issue}")
        print()
        
        # 설치된 패키지
        pkg_info = results['installed_packages']
        print("📦 패키지 상태")
        if pkg_info.get('missing_packages'):
            print("  ❌ 누락된 패키지:")
            for pkg in pkg_info['missing_packages']:
                print(f"    - {pkg}")
        else:
            print("  ✅ 모든 필수 패키지가 설치되어 있습니다")
        
        if pkg_info.get('version_conflicts'):
            print("  ⚠️ 버전 불일치:")
            for conflict in pkg_info['version_conflicts']:
                print(f"    - {conflict['package']}: 예상 {conflict['expected']}, 설치됨 {conflict['installed']}")
        print()
        
        # 프로젝트 구조
        proj_info = results['project_structure']
        print("📁 프로젝트 구조")
        if proj_info.get('missing_files'):
            print("  ❌ 누락된 파일/디렉토리:")
            for file in proj_info['missing_files']:
                print(f"    - {file}")
        else:
            print("  ✅ 모든 필수 파일이 존재합니다")
        print()
        
        # 포트 상태
        port_info = results['port_availability']
        print("🌐 포트 상태")
        if port_info.get('available'):
            print(f"  ✅ 포트 {port_info['port']} 사용 가능")
        else:
            print(f"  ❌ 포트 {port_info['port']} 사용 중")
            if port_info.get('process_info'):
                print(f"    프로세스 PID: {port_info['process_info'].get('pid', 'N/A')}")
        print()
        
        # 경로 인코딩
        path_info = results['path_encoding']
        print("📂 경로 인코딩")
        if path_info.get('korean_path_detected'):
            print("  ⚠️ 한국어 경로 감지됨")
            print("    권장: 영문 경로로 이동 또는 배치 파일 사용")
        else:
            print("  ✅ 경로 인코딩 문제 없음")
        print()
        
        # 시스템 리소스
        sys_info = results['system_resources']
        print("💻 시스템 리소스")
        if sys_info.get('memory_info'):
            mem = sys_info['memory_info']
            print(f"  메모리: {mem['percent']:.1f}% 사용 중")
        if sys_info.get('disk_info'):
            disk = sys_info['disk_info']
            print(f"  디스크: {disk['percent']:.1f}% 사용 중")
        print()
        
        # 전체 상태
        overall_status = results['overall_status']
        if overall_status == 'success':
            print("✅ 전체 진단 결과: 정상")
            print("🚀 서버를 시작할 수 있습니다!")
        else:
            print("⚠️ 전체 진단 결과: 문제 발견")
            print("🔧 위의 문제들을 해결한 후 서버를 시작하세요.")
        
        print("=" * 60)

def main():
    """메인 실행 함수"""
    diagnostic = SystemDiagnostic()
    results = diagnostic.run_full_diagnostic()
    diagnostic.print_diagnostic_report(results)
    
    # 결과를 JSON 파일로 저장
    with open('diagnostic_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📋 진단 결과가 'diagnostic_results.json'에 저장되었습니다.")
    
    return 0 if results['overall_status'] == 'success' else 1

if __name__ == "__main__":
    sys.exit(main())
