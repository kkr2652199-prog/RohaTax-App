#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 의존성 체크 및 설치 시스템
=============================

app.py의 모든 import 문을 파싱하여 누락된 패키지를 자동으로 감지하고 설치합니다.
Python 3.14.0 환경에서 안정적으로 동작하도록 설계되었습니다.
"""

import os
import sys
import ast
import subprocess
import importlib.util
from pathlib import Path
from typing import Set, List, Dict, Tuple
import logging

class DependencyChecker:
    """의존성 체크 및 자동 설치 시스템"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = self._setup_logging()
        
        # 표준 라이브러리 목록 (설치하지 않아도 되는 패키지들)
        self.stdlib_modules = {
            'os', 'sys', 'time', 'datetime', 'json', 'logging', 'pathlib',
            'typing', 'collections', 'itertools', 'functools', 'operator',
            're', 'math', 'random', 'string', 'io', 'csv', 'sqlite3',
            'threading', 'multiprocessing', 'subprocess', 'shutil',
            'tempfile', 'glob', 'fnmatch', 'stat', 'hashlib', 'base64',
            'urllib', 'http', 'email', 'html', 'xml', 'zipfile', 'tarfile',
            'gzip', 'bz2', 'lzma', 'pickle', 'copy', 'weakref', 'gc',
            'traceback', 'warnings', 'contextlib', 'abc', 'enum'
        }
        
        # 내부 모듈 (프로젝트 내부 파일들)
        self.internal_modules = {
            'core', 'config', 'routes', 'templates', 'static'
        }
        
        self.logger.info("🔍 의존성 체크 시스템 초기화 완료")

    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('dependency_check.log', encoding='utf-8')
            ]
        )
        return logging.getLogger(__name__)

    def parse_imports_from_file(self, file_path: Path) -> Set[str]:
        """파일에서 import 문을 파싱하여 패키지 목록 추출"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        imports.add(module_name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        imports.add(module_name)
        
        except Exception as e:
            self.logger.error(f"파일 파싱 오류 {file_path}: {e}")
        
        return imports

    def scan_project_imports(self) -> Set[str]:
        """프로젝트 전체에서 사용되는 모든 import 문 스캔"""
        all_imports = set()
        
        # Python 파일들 스캔
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith('check_') or py_file.name.startswith('test_'):
                continue  # 체크 스크립트와 테스트 파일 제외
            
            file_imports = self.parse_imports_from_file(py_file)
            all_imports.update(file_imports)
            self.logger.debug(f"📄 {py_file.name}: {len(file_imports)}개 import")
        
        return all_imports

    def filter_external_packages(self, imports: Set[str]) -> Set[str]:
        """외부 패키지만 필터링 (표준 라이브러리와 내부 모듈 제외)"""
        external_packages = set()
        
        for module in imports:
            # 표준 라이브러리 제외
            if module in self.stdlib_modules:
                continue
            
            # 내부 모듈 제외
            if any(module.startswith(internal) for internal in self.internal_modules):
                continue
            
            # 특수 모듈 제외
            if module.startswith('_') or module in {'main', '__main__'}:
                continue
            
            external_packages.add(module)
        
        return external_packages

    def check_installed_packages(self) -> Dict[str, bool]:
        """설치된 패키지 확인"""
        installed_packages = {}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True, text=True, check=True
            )
            
            installed_list = set()
            for line in result.stdout.strip().split('\n'):
                if line and '==' in line:
                    package_name = line.split('==')[0].lower()
                    installed_list.add(package_name)
            
            # 외부 패키지들의 설치 상태 확인
            for package in self.filter_external_packages(self.scan_project_imports()):
                package_lower = package.lower().replace('_', '-')
                installed_packages[package] = (
                    package_lower in installed_list or 
                    package in installed_list
                )
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"패키지 목록 확인 실패: {e}")
        
        return installed_packages

    def install_missing_packages(self, missing_packages: List[str]) -> bool:
        """누락된 패키지 자동 설치"""
        if not missing_packages:
            self.logger.info("✅ 모든 패키지가 설치되어 있습니다")
            return True
        
        self.logger.info(f"📦 누락된 패키지 설치 시작: {', '.join(missing_packages)}")
        
        try:
            # requirements.txt에서 버전 정보와 함께 설치 시도
            if (self.project_root / 'requirements.txt').exists():
                self.logger.info("📋 requirements.txt를 사용하여 설치")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                    capture_output=True, text=True, check=True
                )
                self.logger.info("✅ requirements.txt 기반 설치 완료")
                return True
        
        except subprocess.CalledProcessError:
            self.logger.warning("⚠️ requirements.txt 설치 실패, 개별 패키지 설치 시도")
        
        # 개별 패키지 설치
        success_count = 0
        for package in missing_packages:
            try:
                self.logger.info(f"📦 {package} 설치 중...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True, text=True, check=True
                )
                success_count += 1
                self.logger.info(f"✅ {package} 설치 완료")
            
            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ {package} 설치 실패: {e}")
        
        return success_count == len(missing_packages)

    def check_package_versions(self) -> Dict[str, str]:
        """패키지 버전 확인"""
        package_versions = {}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, check=True
            )
            
            import json
            installed_packages = json.loads(result.stdout)
            
            for pkg in installed_packages:
                package_versions[pkg['name']] = pkg['version']
        
        except Exception as e:
            self.logger.error(f"버전 확인 실패: {e}")
        
        return package_versions

    def run_full_check(self) -> bool:
        """전체 의존성 체크 및 설치 실행"""
        self.logger.info("🚀 전체 의존성 체크 시작")
        
        # 1. 프로젝트에서 사용되는 모든 import 스캔
        all_imports = self.scan_project_imports()
        self.logger.info(f"📊 총 {len(all_imports)}개 모듈 발견")
        
        # 2. 외부 패키지만 필터링
        external_packages = self.filter_external_packages(all_imports)
        self.logger.info(f"📦 외부 패키지 {len(external_packages)}개: {', '.join(external_packages)}")
        
        # 3. 설치된 패키지 확인
        installed_status = self.check_installed_packages()
        
        # 4. 누락된 패키지 식별
        missing_packages = [
            pkg for pkg, installed in installed_status.items() 
            if not installed
        ]
        
        if missing_packages:
            self.logger.warning(f"⚠️ 누락된 패키지 {len(missing_packages)}개: {', '.join(missing_packages)}")
            
            # 5. 누락된 패키지 자동 설치
            install_success = self.install_missing_packages(missing_packages)
            
            if not install_success:
                self.logger.error("❌ 일부 패키지 설치 실패")
                return False
        
        # 6. 버전 정보 출력
        versions = self.check_package_versions()
        self.logger.info("📋 설치된 패키지 버전:")
        for pkg in external_packages:
            if pkg.lower() in versions:
                self.logger.info(f"  {pkg}: {versions[pkg.lower()]}")
        
        self.logger.info("✅ 의존성 체크 완료")
        return True

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🔍 1Tax App 의존성 체크 시스템")
    print("=" * 50)
    
    checker = DependencyChecker()
    success = checker.run_full_check()
    
    if success:
        print("\n✅ 모든 의존성이 정상적으로 설치되었습니다!")
        print("🚀 이제 서버를 시작할 수 있습니다.")
    else:
        print("\n❌ 일부 의존성 설치에 실패했습니다.")
        print("📋 수동으로 설치해주세요:")
        print("   py -3.14 -m pip install -r requirements.txt")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
