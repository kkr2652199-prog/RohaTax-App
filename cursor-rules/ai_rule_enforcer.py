"""
AI 규칙 강제 시스템
- AI가 500줄 제한을 지키도록 강제
- 파일 크기 모니터링 및 자동 분할
- 규칙 위반 시 경고 및 자동 수정
"""

import os
import logging
from typing import Dict, List, Any
from pathlib import Path
from core.file_size_manager import file_size_manager

class AIRuleEnforcer:
    """AI 규칙 강제 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.violations = []  # 규칙 위반 기록
        self.auto_fixes = []  # 자동 수정 기록
        
    def check_all_files(self, directory: str = ".") -> Dict[str, Any]:
        """모든 파일의 크기 확인"""
        violations = []
        auto_fixes = []
        
        for root, dirs, files in os.walk(directory):
            # 특정 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.css', '.html', '.md')):
                    file_path = os.path.join(root, file)
                    
                    # 파일 크기 확인
                    check_result = file_size_manager.check_file_size(file_path)
                    
                    if check_result.get('needs_split', False):
                        violations.append({
                            'file': file_path,
                            'lines': check_result['line_count'],
                            'max_lines': file_size_manager.MAX_LINES,
                            'excess': check_result['line_count'] - file_size_manager.MAX_LINES
                        })
                        
                        # 자동 수정 시도
                        fixed_path = file_size_manager.enforce_size_limit(file_path)
                        if fixed_path != file_path:
                            auto_fixes.append({
                                'original': file_path,
                                'fixed': fixed_path,
                                'action': 'split'
                            })
        
        return {
            'violations': violations,
            'auto_fixes': auto_fixes,
            'total_violations': len(violations),
            'total_fixes': len(auto_fixes)
        }
    
    def generate_violation_report(self, violations: List[Dict]) -> str:
        """규칙 위반 보고서 생성"""
        if not violations:
            return "✅ 모든 파일이 500줄 제한을 준수합니다!"
        
        report = "🚨 파일 크기 위반 보고서\n"
        report += "=" * 50 + "\n"
        
        for i, violation in enumerate(violations, 1):
            report += f"{i}. {violation['file']}\n"
            report += f"   현재: {violation['lines']}줄\n"
            report += f"   제한: {violation['max_lines']}줄\n"
            report += f"   초과: {violation['excess']}줄\n\n"
        
        report += f"총 {len(violations)}개 파일이 규칙을 위반했습니다.\n"
        report += "자동 분할을 통해 수정되었습니다."
        
        return report
    
    def enforce_ai_rules(self) -> Dict[str, Any]:
        """AI 규칙 강제 적용"""
        self.logger.info("🔒 AI 규칙 강제 시스템 시작")
        
        # 모든 파일 확인
        check_result = self.check_all_files()
        
        # 위반 보고서 생성
        violation_report = self.generate_violation_report(check_result['violations'])
        
        # 결과 저장
        result = {
            'status': 'success',
            'violations': check_result['violations'],
            'auto_fixes': check_result['auto_fixes'],
            'report': violation_report,
            'timestamp': self._get_timestamp()
        }
        
        # 로그 기록
        self.logger.info(f"규칙 위반: {check_result['total_violations']}개")
        self.logger.info(f"자동 수정: {check_result['total_fixes']}개")
        
        return result
    
    def _get_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def create_rule_monitor(self) -> str:
        """규칙 모니터링 스크립트 생성"""
        monitor_script = '''"""
AI 규칙 모니터링 스크립트
- 실시간으로 파일 크기 모니터링
- 규칙 위반 시 자동 경고 및 수정
"""

import os
import time
import logging
from core.file_size_manager import file_size_manager
from core.ai_rule_enforcer import AIRuleEnforcer

def monitor_file_sizes():
    """파일 크기 모니터링"""
    enforcer = AIRuleEnforcer()
    
    while True:
        try:
            # 규칙 강제 적용
            result = enforcer.enforce_ai_rules()
            
            if result['violations']:
                print("🚨 규칙 위반 감지!")
                print(result['report'])
            
            # 30초마다 체크
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\\n모니터링 중단")
            break
        except Exception as e:
            print(f"모니터링 오류: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_file_sizes()
'''
        
        monitor_path = "monitor_ai_rules.py"
        with open(monitor_path, 'w', encoding='utf-8') as f:
            f.write(monitor_script)
        
        self.logger.info(f"📊 규칙 모니터링 스크립트 생성: {monitor_path}")
        return monitor_path

# 전역 인스턴스
ai_rule_enforcer = AIRuleEnforcer()














