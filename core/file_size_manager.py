"""
파일 크기 관리 시스템 (500줄 제한)
- 파일이 500줄을 초과할 때 자동 분할
- 분할된 파일들 간의 연동 관리
- AI가 규칙을 지키도록 강제하는 시스템
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

class FileSizeManager:
    """파일 크기 관리자 - 500줄 제한 시스템"""
    
    MAX_LINES = 500  # 최대 500줄 제한
    SPLIT_SUFFIX = "_part"  # 분할 파일 접미사
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.split_files = {}  # 분할된 파일들 추적
        
    def check_file_size(self, file_path: str) -> Dict[str, Any]:
        """파일 크기 확인 및 분할 필요성 검사"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_count = len(lines)
            
            result = {
                'file_path': file_path,
                'line_count': line_count,
                'needs_split': line_count > self.MAX_LINES,
                'status': 'OK' if line_count <= self.MAX_LINES else 'NEEDS_SPLIT'
            }
            
            if result['needs_split']:
                self.logger.warning(f"🚨 파일 크기 초과: {file_path} ({line_count}줄 > {self.MAX_LINES}줄)")
                result['split_plan'] = self._create_split_plan(lines)
            
            return result
            
        except Exception as e:
            self.logger.error(f"파일 크기 확인 오류: {str(e)}")
            return {'error': str(e)}
    
    def _create_split_plan(self, lines: List[str]) -> Dict[str, Any]:
        """분할 계획 생성"""
        total_lines = len(lines)
        num_parts = (total_lines + self.MAX_LINES - 1) // self.MAX_LINES  # 올림 계산
        
        split_plan = {
            'total_lines': total_lines,
            'num_parts': num_parts,
            'lines_per_part': self.MAX_LINES,
            'last_part_lines': total_lines % self.MAX_LINES or self.MAX_LINES
        }
        
        return split_plan
    
    def split_large_file(self, file_path: str) -> List[str]:
        """큰 파일을 여러 부분으로 분할"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) <= self.MAX_LINES:
                return [file_path]  # 분할 불필요
            
            # 파일 경로 준비
            base_path = Path(file_path)
            base_name = base_path.stem
            extension = base_path.suffix
            directory = base_path.parent
            
            split_files = []
            split_plan = self._create_split_plan(lines)
            
            # 각 부분별로 파일 생성
            for part_num in range(split_plan['num_parts']):
                start_idx = part_num * self.MAX_LINES
                end_idx = min(start_idx + self.MAX_LINES, len(lines))
                
                part_lines = lines[start_idx:end_idx]
                
                # 분할 파일명 생성
                part_filename = f"{base_name}{self.SPLIT_SUFFIX}{part_num + 1:02d}{extension}"
                part_path = directory / part_filename
                
                # 파일 작성
                with open(part_path, 'w', encoding='utf-8') as f:
                    f.writelines(part_lines)
                
                split_files.append(str(part_path))
                self.logger.info(f"✅ 분할 파일 생성: {part_path} ({len(part_lines)}줄)")
            
            # 원본 파일 백업
            backup_path = directory / f"{base_name}_original{extension}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 분할 파일들 추적
            self.split_files[file_path] = {
                'split_files': split_files,
                'backup_path': str(backup_path),
                'split_plan': split_plan
            }
            
            self.logger.info(f"🎯 파일 분할 완료: {file_path} → {len(split_files)}개 파일")
            return split_files
            
        except Exception as e:
            self.logger.error(f"파일 분할 오류: {str(e)}")
            return []
    
    def create_file_linker(self, split_files: List[str]) -> str:
        """분할된 파일들을 연동하는 링커 파일 생성"""
        try:
            if not split_files:
                return ""
            
            # 링커 파일 경로
            first_file = Path(split_files[0])
            linker_path = first_file.parent / f"{first_file.stem.replace(self.SPLIT_SUFFIX + '01', '')}_linker.py"
            
            # 링커 파일 내용 생성
            linker_content = self._generate_linker_content(split_files)
            
            # 링커 파일 작성
            with open(linker_path, 'w', encoding='utf-8') as f:
                f.write(linker_content)
            
            self.logger.info(f"🔗 파일 링커 생성: {linker_path}")
            return str(linker_path)
            
        except Exception as e:
            self.logger.error(f"링커 생성 오류: {str(e)}")
            return ""
    
    def _generate_linker_content(self, split_files: List[str]) -> str:
        """링커 파일 내용 생성"""
        base_name = Path(split_files[0]).stem.replace(self.SPLIT_SUFFIX + '01', '')
        
        content = f'''"""
자동 생성된 파일 링커: {base_name}
- 분할된 파일들을 연동하는 시스템
- AI가 500줄 제한을 지키도록 강제
"""

import os
import sys
from pathlib import Path

class {base_name.title().replace('_', '')}Linker:
    """분할된 {base_name} 파일들을 연동하는 클래스"""
    
    def __init__(self):
        self.split_files = {split_files}
        self.current_part = 0
    
    def get_all_content(self) -> str:
        """모든 분할 파일의 내용을 합쳐서 반환"""
        content = ""
        for file_path in self.split_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content += f.read()
        return content
    
    def get_part_content(self, part_num: int) -> str:
        """특정 부분의 내용 반환"""
        if 0 <= part_num < len(self.split_files):
            file_path = self.split_files[part_num]
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        return ""
    
    def get_next_part(self) -> str:
        """다음 부분의 내용 반환"""
        if self.current_part < len(self.split_files):
            content = self.get_part_content(self.current_part)
            self.current_part += 1
            return content
        return ""
    
    def reset(self):
        """현재 부분을 처음으로 리셋"""
        self.current_part = 0

# 전역 인스턴스
{base_name}_linker = {base_name.title().replace('_', '')}Linker()

# 편의 함수들
def get_{base_name}_content():
    """전체 내용 반환"""
    return {base_name}_linker.get_all_content()

def get_{base_name}_part(part_num: int):
    """특정 부분 반환"""
    return {base_name}_linker.get_part_content(part_num)

def get_{base_name}_next():
    """다음 부분 반환"""
    return {base_name}_linker.get_next_part()
'''
        return content
    
    def enforce_size_limit(self, file_path: str) -> str:
        """파일 크기 제한 강제 적용"""
        check_result = self.check_file_size(file_path)
        
        if check_result.get('needs_split', False):
            split_files = self.split_large_file(file_path)
            if split_files:
                linker_path = self.create_file_linker(split_files)
                return linker_path
        
        return file_path
    
    def get_split_info(self, file_path: str) -> Dict[str, Any]:
        """분할 정보 반환"""
        return self.split_files.get(file_path, {})

# 전역 인스턴스
file_size_manager = FileSizeManager()







