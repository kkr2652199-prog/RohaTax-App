#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 자동 정리 시스템
- 500줄 초과 파일 자동 분할
- 중복 파일 정리
- 백업 파일 관리
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import logging

class AutoCleanupSystem:
    """자동 정리 시스템"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # 파일 크기 제한
        self.MAX_LINES = 500
        self.MAX_SIZE_KB = 20
        
        # 정리 대상 확장자
        self.TARGET_EXTENSIONS = ['.py', '.js', '.css', '.md']
        
        # 보호할 파일들
        self.PROTECTED_FILES = [
            'app.py', 'main.py', '__init__.py',
            'auto_cleanup_system.py',  # 자기 자신
            'file_size_manager.py', 'file_change_monitor.py'
        ]
        
        # 백업 디렉토리
        self.BACKUP_DIR = self.project_root / "backup_files"
        self.BACKUP_DIR.mkdir(exist_ok=True)
    
    def analyze_project_structure(self) -> Dict[str, any]:
        """프로젝트 구조 분석"""
        analysis = {
            'total_files': 0,
            'large_files': [],
            'duplicate_files': [],
            'backup_files': [],
            'total_size_mb': 0
        }
        
        for root, dirs, files in os.walk(self.project_root):
            # 특정 디렉토리 제외
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.TARGET_EXTENSIONS):
                    file_path = Path(root) / file
                    analysis['total_files'] += 1
                    analysis['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
                    
                    # 대용량 파일 체크
                    if self._is_large_file(file_path):
                        analysis['large_files'].append({
                            'path': str(file_path),
                            'size_kb': file_path.stat().st_size / 1024,
                            'lines': self._count_lines(file_path)
                        })
                    
                    # 중복 파일 체크
                    if self._is_duplicate_file(file):
                        analysis['duplicate_files'].append(str(file_path))
                    
                    # 백업 파일 체크
                    if self._is_backup_file(file):
                        analysis['backup_files'].append(str(file_path))
        
        return analysis
    
    def _is_large_file(self, file_path: Path) -> bool:
        """대용량 파일 여부 확인"""
        if file_path.name in self.PROTECTED_FILES:
            return False
        
        # 크기 체크
        size_kb = file_path.stat().st_size / 1024
        if size_kb > self.MAX_SIZE_KB:
            return True
        
        # 줄 수 체크
        lines = self._count_lines(file_path)
        if lines > self.MAX_LINES:
            return True
        
        return False
    
    def _count_lines(self, file_path: Path) -> int:
        """파일 줄 수 계산"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0
    
    def _is_duplicate_file(self, filename: str) -> bool:
        """중복 파일 여부 확인"""
        duplicate_patterns = [
            '_original.py', '_part01.py', '_part02.py',
            '_backup.py', '_old.py', '_temp.py',
            '_linker.py', '_copy.py'
        ]
        return any(pattern in filename for pattern in duplicate_patterns)
    
    def _is_backup_file(self, filename: str) -> bool:
        """백업 파일 여부 확인"""
        backup_patterns = [
            '.bak', '.backup', '.old', '.orig',
            '_backup', '_old', '_orig'
        ]
        return any(pattern in filename for pattern in backup_patterns)
    
    def cleanup_duplicate_files(self, dry_run: bool = True) -> List[str]:
        """중복 파일 정리"""
        cleaned_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if self._is_duplicate_file(file) or self._is_backup_file(file):
                    file_path = Path(root) / file
                    
                    if dry_run:
                        cleaned_files.append(f"[DRY RUN] {file_path}")
                    else:
                        # 백업 디렉토리로 이동
                        backup_path = self.BACKUP_DIR / file
                        shutil.move(str(file_path), str(backup_path))
                        cleaned_files.append(f"Moved: {file_path} → {backup_path}")
        
        return cleaned_files
    
    def split_large_file(self, file_path: Path, dry_run: bool = True) -> List[str]:
        """대용량 파일 분할"""
        if not self._is_large_file(file_path):
            return []
        
        lines = self._count_lines(file_path)
        if lines <= self.MAX_LINES:
            return []
        
        # 분할 계획
        parts_needed = (lines + self.MAX_LINES - 1) // self.MAX_LINES
        split_plan = []
        
        for i in range(parts_needed):
            start_line = i * self.MAX_LINES
            end_line = min((i + 1) * self.MAX_LINES, lines)
            
            part_name = f"{file_path.stem}_part{i+1:02d}{file_path.suffix}"
            part_path = file_path.parent / part_name
            
            split_plan.append({
                'part': i + 1,
                'start_line': start_line,
                'end_line': end_line,
                'path': str(part_path),
                'lines': end_line - start_line
            })
        
        if dry_run:
            return [f"[DRY RUN] Split plan for {file_path}: {parts_needed} parts"]
        
        # 실제 분할 실행
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            for plan in split_plan:
                part_lines = all_lines[plan['start_line']:plan['end_line']]
                
                with open(plan['path'], 'w', encoding='utf-8') as f:
                    f.writelines(part_lines)
            
            # 원본 파일을 백업으로 이동
            backup_path = self.BACKUP_DIR / file_path.name
            shutil.move(str(file_path), str(backup_path))
            
            return [f"Split: {file_path} → {parts_needed} parts + backup"]
            
        except Exception as e:
            return [f"Error splitting {file_path}: {str(e)}"]
    
    def generate_cleanup_report(self) -> str:
        """정리 보고서 생성"""
        analysis = self.analyze_project_structure()
        
        report = f"""
📊 프로젝트 정리 보고서
=====================================
📁 총 파일 수: {analysis['total_files']}개
💾 총 크기: {analysis['total_size_mb']:.2f}MB
🚨 대용량 파일: {len(analysis['large_files'])}개
🔄 중복 파일: {len(analysis['duplicate_files'])}개
📦 백업 파일: {len(analysis['backup_files'])}개

🚨 대용량 파일 목록:
"""
        
        for file_info in analysis['large_files']:
            report += f"  - {file_info['path']} ({file_info['lines']}줄, {file_info['size_kb']:.1f}KB)\n"
        
        report += f"\n🔄 중복 파일 목록:\n"
        for file_path in analysis['duplicate_files'][:10]:  # 상위 10개만
            report += f"  - {file_path}\n"
        
        if len(analysis['duplicate_files']) > 10:
            report += f"  ... 외 {len(analysis['duplicate_files']) - 10}개\n"
        
        return report
    
    def run_full_cleanup(self, dry_run: bool = True) -> Dict[str, List[str]]:
        """전체 정리 실행"""
        results = {
            'duplicate_cleanup': [],
            'file_splitting': [],
            'report': []
        }
        
        # 1. 중복 파일 정리
        results['duplicate_cleanup'] = self.cleanup_duplicate_files(dry_run)
        
        # 2. 대용량 파일 분할
        analysis = self.analyze_project_structure()
        for file_info in analysis['large_files']:
            file_path = Path(file_info['path'])
            split_results = self.split_large_file(file_path, dry_run)
            results['file_splitting'].extend(split_results)
        
        # 3. 보고서 생성
        results['report'] = [self.generate_cleanup_report()]
        
        return results


def main():
    """메인 실행 함수"""
    cleanup_system = AutoCleanupSystem()
    
    print("🔍 프로젝트 분석 중...")
    report = cleanup_system.generate_cleanup_report()
    print(report)
    
    print("\n🧹 정리 실행 (DRY RUN)...")
    results = cleanup_system.run_full_cleanup(dry_run=True)
    
    print("\n📋 정리 계획:")
    print("중복 파일 정리:")
    for item in results['duplicate_cleanup'][:5]:
        print(f"  {item}")
    
    print("\n파일 분할:")
    for item in results['file_splitting'][:5]:
        print(f"  {item}")
    
    print(f"\n💡 실제 정리를 실행하려면: cleanup_system.run_full_cleanup(dry_run=False)")


if __name__ == "__main__":
    main()








