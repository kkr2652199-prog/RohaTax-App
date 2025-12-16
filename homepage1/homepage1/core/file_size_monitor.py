"""
파일 크기 자동 감시 시스템
- 파일이 권장 크기를 초과하면 경고
- 리팩토링 필요 시 알림
- 분할 관리 시스템과 연동
"""

import os
from typing import Dict, List
from core.notification_system import notification_system
from core.file_protection_system import file_protection_system

class FileSizeMonitor:
    """파일 크기 감시 및 경고 시스템"""
    
    # 파일 타입별 권장 최대 줄 수
    MAX_LINES = {
        'html': 500,
        'py': 500,
        'js': 400,
        'css': 400,
        'json': 200,
        'md': 300
    }
    
    # 경고 임계값 (권장 크기의 80%)
    WARNING_THRESHOLD = 0.8
    
    def __init__(self, root_path: str = '.'):
        self.root_path = root_path
        self.violations = []
        self.warnings = []
        self.protection_system = file_protection_system
    
    def get_file_extension(self, file_path: str) -> str:
        """파일 확장자 추출"""
        return os.path.splitext(file_path)[1].lstrip('.')
    
    def count_lines(self, file_path: str) -> int:
        """파일 줄 수 카운트"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0
    
    def check_file(self, file_path: str) -> Dict:
        """파일 크기 체크 (분할 관리 시스템 연동)"""
        ext = self.get_file_extension(file_path)
        
        # 감시 대상이 아니면 건너뛰기
        if ext not in self.MAX_LINES:
            return None
        
        lines = self.count_lines(file_path)
        max_lines = self.MAX_LINES[ext]
        warning_lines = int(max_lines * self.WARNING_THRESHOLD)
        
        status = 'ok'
        message = ''
        recommendation = ''
        
        # 보호된 파일인지 확인
        is_protected = self.protection_system.is_protected_file(file_path)
        
        if lines > max_lines:
            if is_protected:
                status = 'protected_violation'
                message = f"{file_path}: {lines}줄 (보호된 파일 - 현재 상태 유지)"
                recommendation = "현재 상태 파일 - 분할하지 않음"
            else:
                status = 'violation'
                message = f"{file_path}: {lines}줄 (권장: {max_lines}줄 이하)"
                recommendation = "새 파일 - 자동 분할 적용 가능"
                self.violations.append({
                    'file': file_path,
                    'lines': lines,
                    'max_lines': max_lines,
                    'excess': lines - max_lines,
                    'is_protected': is_protected
                })
        elif lines > warning_lines:
            status = 'warning'
            message = f"💡 {file_path}: {lines}줄 (주의: {max_lines}줄 접근 중)"
            recommendation = "분할 고려 필요"
            self.warnings.append({
                'file': file_path,
                'lines': lines,
                'max_lines': max_lines,
                'percentage': (lines / max_lines) * 100,
                'is_protected': is_protected
            })
        
        return {
            'file': file_path,
            'lines': lines,
            'max_lines': max_lines,
            'status': status,
            'message': message,
            'recommendation': recommendation,
            'is_protected': is_protected
        }
    
    def scan_directory(self, directory: str = None) -> List[Dict]:
        """디렉토리 스캔"""
        if directory is None:
            directory = self.root_path
        
        results = []
        
        for root, dirs, files in os.walk(directory):
            # 제외할 디렉토리
            if any(exclude in root for exclude in ['backups', '__pycache__', '.git', 'node_modules', 'temp', '.venv', 'venv']):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.root_path)
                
                result = self.check_file(file_path)
                if result:
                    results.append(result)
        
        return results
    
    def generate_report(self) -> str:
        """감시 보고서 생성"""
        lines = []
        lines.append("=" * 60)
        lines.append("📊 파일 크기 감시 보고서")
        lines.append("=" * 60)
        
        if self.violations:
            lines.append(f"\n🚨 권장 크기 초과 파일: {len(self.violations)}개")
            lines.append("-" * 60)
            for v in self.violations:
                lines.append(f"  ❌ {v['file']}")
                lines.append(f"     현재: {v['lines']}줄 | 권장: {v['max_lines']}줄 | 초과: +{v['excess']}줄")
        
        if self.warnings:
            lines.append(f"\n⚠️ 주의 필요 파일: {len(self.warnings)}개")
            lines.append("-" * 60)
            for w in self.warnings:
                lines.append(f"  💡 {w['file']}")
                lines.append(f"     현재: {w['lines']}줄 | 권장: {w['max_lines']}줄 | 사용률: {w['percentage']:.1f}%")
        
        if not self.violations and not self.warnings:
            lines.append("\n✅ 모든 파일이 권장 크기 이내입니다!")
        
        lines.append("\n" + "=" * 60)
        lines.append(f"총 감시 파일 타입: {', '.join(self.MAX_LINES.keys())}")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def monitor_and_report(self) -> bool:
        """감시 및 보고 (위반 사항 있으면 False 반환)"""
        self.violations = []
        self.warnings = []
        
        results = self.scan_directory()
        
        # 보고서 출력
        report = self.generate_report()
        print(report)
        
        # 위반 사항이 있으면 알림
        if self.violations:
            print(f"\n⚠️ 알림: {len(self.violations)}개 파일이 권장 크기를 초과했습니다.")
            print("💡 리팩토링을 고려하세요!\n")
            return False
        
        return True

# 싱글톤 인스턴스
file_size_monitor = FileSizeMonitor()

if __name__ == '__main__':
    # 테스트 실행
    file_size_monitor.monitor_and_report()









