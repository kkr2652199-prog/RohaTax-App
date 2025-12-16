"""
지침 추가 명령어 자동 처리 스크립트
사용법: python tools/guideline_command_processor.py "키워드추가: 커피숍, 베이커리"
"""

import json
import sys
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any

class GuidelineCommandProcessor:
    def __init__(self):
        self.config_dir = "config"
        self.industry_config_path = os.path.join(self.config_dir, "industry_config.json")
        self.absolute_config_path = os.path.join(self.config_dir, "absolute_guidelines_v5.json")
        self.backup_dir = "config/backups"
        
        # 백업 디렉토리 생성
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, file_path: str) -> str:
        """파일 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{filename}.backup_{timestamp}")
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """명령어 처리 메인 함수"""
        print(f"처리 중인 명령어: {command}")
        
        if command.startswith("키워드추가:"):
            return self.add_keywords(command)
        elif command.startswith("규칙수정:"):
            return self.modify_rule(command)
        elif command.startswith("검증규칙:"):
            return self.add_validation_rule(command)
        elif command.startswith("지침추가:"):
            return self.add_guideline(command)
        else:
            return {"success": False, "error": "알 수 없는 명령어"}
    
    def add_keywords(self, command: str) -> Dict[str, Any]:
        """키워드 추가: 커피숍, 베이커리"""
        try:
            keywords_text = command.split(":")[1].strip()
            keywords = [k.strip() for k in keywords_text.split(",")]
            
            # 백업 생성
            backup_path = self.create_backup(self.industry_config_path)
            print(f"백업 생성: {backup_path}")
            
            # industry_config.json 로드
            with open(self.industry_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # store_keywords에 추가
            original_count = len(config['delivery']['store_keywords'])
            config['delivery']['store_keywords'].extend(keywords)
            
            # 중복 제거
            config['delivery']['store_keywords'] = list(set(config['delivery']['store_keywords']))
            new_count = len(config['delivery']['store_keywords'])
            
            # 파일 저장
            with open(self.industry_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True, 
                "added": keywords, 
                "original_count": original_count,
                "new_count": new_count,
                "backup": backup_path
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def modify_rule(self, command: str) -> Dict[str, Any]:
        """규칙 수정: column_matching_threshold 0.8"""
        try:
            parts = command.split(":")[1].strip().split()
            rule_name = parts[0]
            rule_value = parts[1] if len(parts) > 1 else None
            
            # 백업 생성
            backup_path = self.create_backup(self.industry_config_path)
            print(f"백업 생성: {backup_path}")
            
            # industry_config.json 로드
            with open(self.industry_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 규칙 수정
            old_value = None
            if rule_name in config['delivery']:
                old_value = config['delivery'][rule_name]
                
                # 숫자 값인지 확인
                if rule_value and rule_value.replace('.', '').isdigit():
                    config['delivery'][rule_name] = float(rule_value)
                else:
                    config['delivery'][rule_name] = rule_value
            else:
                return {"success": False, "error": f"규칙 '{rule_name}'을 찾을 수 없습니다"}
            
            # 파일 저장
            with open(self.industry_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "rule_name": rule_name,
                "old_value": old_value,
                "new_value": config['delivery'][rule_name],
                "backup": backup_path
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_validation_rule(self, command: str) -> Dict[str, Any]:
        """검증규칙 추가: phone ^010-[0-9]{4}-[0-9]{4}$"""
        try:
            parts = command.split(":")[1].strip().split()
            field_name = parts[0]
            regex_pattern = parts[1] if len(parts) > 1 else None
            
            if not regex_pattern:
                return {"success": False, "error": "정규식 패턴이 필요합니다"}
            
            # 백업 생성
            backup_path = self.create_backup(self.absolute_config_path)
            print(f"백업 생성: {backup_path}")
            
            # absolute_guidelines_v5.json 로드
            with open(self.absolute_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 검증 규칙 추가
            validation_rules = config['absolute_rules']['data_validation_rules']
            validation_rules[field_name] = {
                "format": f"{field_name} 형식",
                "validation_regex": regex_pattern,
                "description": f"유효한 {field_name} 형식이어야 함"
            }
            
            # 파일 저장
            with open(self.absolute_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "field_name": field_name,
                "regex_pattern": regex_pattern,
                "backup": backup_path
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_guideline(self, command: str) -> Dict[str, Any]:
        """지침 추가: 공급받는자 전화번호는 필수입니다"""
        try:
            guideline_text = command.split(":")[1].strip()
            
            # MD 문서에 추가할 내용 생성
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            md_content = f"""
## 새 지침 추가 ({timestamp})

**지침 내용**: {guideline_text}

**추가 방법**:
1. JSON 파일 수정 필요
2. Python 코드 수정 필요 (필요시)
3. 테스트 실행 필요

**상태**: 대기 중
"""
            
            # 지침 로그 파일에 추가
            log_file = "공급받는자_규칙/새_지침_로그.md"
            if os.path.exists(log_file):
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(md_content)
            else:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"# 새 지침 추가 로그\n{md_content}")
            
            return {
                "success": True,
                "guideline": guideline_text,
                "log_file": log_file,
                "note": "MD 문서에 추가됨. JSON 파일 수정이 필요할 수 있습니다."
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_json(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일 검증"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return {"valid": True, "message": "JSON 문법이 올바릅니다"}
        except json.JSONDecodeError as e:
            return {"valid": False, "message": f"JSON 문법 오류: {str(e)}"}
        except Exception as e:
            return {"valid": False, "message": f"파일 읽기 오류: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("사용법: python tools/guideline_command_processor.py \"명령어\"")
        print("예시: python tools/guideline_command_processor.py \"키워드추가: 커피숍, 베이커리\"")
        return
    
    command = sys.argv[1]
    processor = GuidelineCommandProcessor()
    
    result = processor.process_command(command)
    
    if result["success"]:
        print("✅ 성공!")
        for key, value in result.items():
            if key != "success":
                print(f"  {key}: {value}")
    else:
        print("❌ 실패!")
        print(f"  오류: {result['error']}")

if __name__ == "__main__":
    main()






