"""
파일 업로드 보안 강화 모듈
MIME 타입 검증 및 파일 헤더 검사
"""

import os
import magic
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileSecurityValidator:
    """파일 업로드 보안 검증 클래스"""
    
    def __init__(self):
        """보안 검증기 초기화"""
        # 허용된 MIME 타입 목록
        self.allowed_mime_types = {
            # Excel 파일
            'application/vnd.ms-excel',  # .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            # CSV 파일
            'text/csv',
            'application/csv',
            # 기타 텍스트 파일
            'text/plain',
            'text/tab-separated-values'
        }
        
        # 허용된 파일 확장자
        self.allowed_extensions = {'.xlsx', '.xls', '.csv', '.txt', '.tsv'}
        
        # 위험한 파일 확장자 (차단)
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.php', '.asp', '.jsp', '.py', '.rb', '.pl', '.sh'
        }
        
        # 최대 파일 크기 (50MB)
        self.max_file_size = 50 * 1024 * 1024
        
    def validate_file_security(self, file_path: str) -> Dict[str, Any]:
        """
        파일 보안 검증 수행
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            검증 결과 딕셔너리
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        try:
            file_path = Path(file_path)
            
            # 1. 파일 존재 확인
            if not file_path.exists():
                result['errors'].append("파일이 존재하지 않습니다.")
                return result
            
            # 2. 파일 크기 검사
            file_size = file_path.stat().st_size
            result['file_info']['size'] = file_size
            
            if file_size > self.max_file_size:
                result['errors'].append(f"파일 크기가 너무 큽니다. (최대: {self.max_file_size // (1024*1024)}MB)")
                return result
            
            if file_size == 0:
                result['errors'].append("빈 파일입니다.")
                return result
            
            # 3. 파일 확장자 검사
            file_extension = file_path.suffix.lower()
            result['file_info']['extension'] = file_extension
            
            if file_extension in self.dangerous_extensions:
                result['errors'].append(f"위험한 파일 형식입니다: {file_extension}")
                return result
            
            if file_extension not in self.allowed_extensions:
                result['errors'].append(f"지원하지 않는 파일 형식입니다: {file_extension}")
                return result
            
            # 4. MIME 타입 검사 (실제 파일 내용 기반)
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
                result['file_info']['mime_type'] = mime_type
                
                if mime_type not in self.allowed_mime_types:
                    result['errors'].append(f"허용되지 않는 파일 형식입니다: {mime_type}")
                    return result
                
                # 확장자와 MIME 타입 일치성 검사
                if not self._validate_extension_mime_match(file_extension, mime_type):
                    result['warnings'].append(f"파일 확장자와 내용이 일치하지 않을 수 있습니다.")
                
            except Exception as e:
                result['errors'].append(f"MIME 타입 검사 실패: {str(e)}")
                return result
            
            # 5. 파일 헤더 검사
            header_validation = self._validate_file_header(file_path)
            if not header_validation['is_valid']:
                result['errors'].extend(header_validation['errors'])
                return result
            
            # 6. 파일 해시 계산 (무결성 검사용)
            file_hash = self._calculate_file_hash(file_path)
            result['file_info']['hash'] = file_hash
            
            # 모든 검증 통과
            result['is_valid'] = True
            result['file_info']['name'] = file_path.name
            result['file_info']['path'] = str(file_path)
            
            logger.info(f"파일 보안 검증 통과: {file_path.name}")
            
        except Exception as e:
            result['errors'].append(f"파일 검증 중 오류 발생: {str(e)}")
            logger.error(f"파일 보안 검증 오류: {file_path} - {str(e)}")
        
        return result
    
    def _validate_extension_mime_match(self, extension: str, mime_type: str) -> bool:
        """파일 확장자와 MIME 타입 일치성 검사"""
        extension_mime_map = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': ['text/csv', 'application/csv'],
            '.txt': 'text/plain',
            '.tsv': 'text/tab-separated-values'
        }
        
        expected_mimes = extension_mime_map.get(extension, [])
        if isinstance(expected_mimes, str):
            expected_mimes = [expected_mimes]
        
        return mime_type in expected_mimes
    
    def _validate_file_header(self, file_path: Path) -> Dict[str, Any]:
        """파일 헤더 검사"""
        result = {'is_valid': True, 'errors': []}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # 첫 1KB 읽기
            
            # Excel 파일 시그니처 검사
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                if not self._is_valid_excel_header(header):
                    result['errors'].append("유효하지 않은 Excel 파일 헤더입니다.")
                    result['is_valid'] = False
            
            # CSV 파일 검사
            elif file_path.suffix.lower() == '.csv':
                if not self._is_valid_csv_header(header):
                    result['errors'].append("유효하지 않은 CSV 파일 헤더입니다.")
                    result['is_valid'] = False
            
        except Exception as e:
            result['errors'].append(f"파일 헤더 검사 실패: {str(e)}")
            result['is_valid'] = False
        
        return result
    
    def _is_valid_excel_header(self, header: bytes) -> bool:
        """Excel 파일 헤더 검증"""
        # XLSX 파일 시그니처 (ZIP 기반)
        xlsx_signatures = [
            b'PK\x03\x04',  # ZIP 파일 시그니처
            b'PK\x05\x06',  # ZIP 파일 시그니처
        ]
        
        # XLS 파일 시그니처
        xls_signatures = [
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE2 시그니처
        ]
        
        for sig in xlsx_signatures + xls_signatures:
            if header.startswith(sig):
                return True
        
        return False
    
    def _is_valid_csv_header(self, header: bytes) -> bool:
        """CSV 파일 헤더 검증"""
        try:
            # UTF-8 BOM 체크
            if header.startswith(b'\xef\xbb\xbf'):
                header = header[3:]
            
            # 텍스트 파일인지 확인
            text = header.decode('utf-8', errors='ignore')
            
            # CSV 특성 확인 (쉼표, 탭, 세미콜론 등 구분자 존재)
            separators = [',', '\t', ';', '|']
            return any(sep in text for sep in separators)
            
        except Exception:
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산 (SHA-256)"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {file_path} - {str(e)}")
            return ""
    
    def get_security_report(self, file_path: str) -> Dict[str, Any]:
        """파일 보안 보고서 생성"""
        validation_result = self.validate_file_security(file_path)
        
        report = {
            'file_path': file_path,
            'validation_result': validation_result,
            'security_score': self._calculate_security_score(validation_result),
            'recommendations': self._get_security_recommendations(validation_result)
        }
        
        return report
    
    def _calculate_security_score(self, validation_result: Dict[str, Any]) -> int:
        """보안 점수 계산 (0-100)"""
        if not validation_result['is_valid']:
            return 0
        
        score = 100
        
        # 경고당 10점 감점
        score -= len(validation_result['warnings']) * 10
        
        # 최소 점수 0점
        return max(0, score)
    
    def _get_security_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """보안 권장사항 생성"""
        recommendations = []
        
        if validation_result['warnings']:
            recommendations.append("파일 확장자와 내용이 일치하지 않을 수 있습니다. 파일을 다시 확인해주세요.")
        
        if validation_result['file_info'].get('size', 0) > 10 * 1024 * 1024:  # 10MB 이상
            recommendations.append("대용량 파일입니다. 처리 시간이 오래 걸릴 수 있습니다.")
        
        return recommendations


# 전역 인스턴스
file_security_validator = FileSecurityValidator()


def validate_uploaded_file(file_path: str) -> Dict[str, Any]:
    """
    업로드된 파일 보안 검증 (편의 함수)
    
    Args:
        file_path: 검증할 파일 경로
        
    Returns:
        검증 결과 딕셔너리
    """
    return file_security_validator.validate_file_security(file_path)


def get_file_security_report(file_path: str) -> Dict[str, Any]:
    """
    파일 보안 보고서 생성 (편의 함수)
    
    Args:
        file_path: 검증할 파일 경로
        
    Returns:
        보안 보고서 딕셔너리
    """
    return file_security_validator.get_security_report(file_path)








