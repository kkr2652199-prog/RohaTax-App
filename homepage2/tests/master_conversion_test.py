#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
변환 시스템 실제 테스트 100% 마스터 스크립트

실제 변환 앱에 테스트 파일을 직접 실행하여 모든 변환 과정의 코드 위치, 
함수명, 변수명, 로직을 라인 단위로 파악하고, 각 규칙이 어떻게 작동하는지, 
왜 그렇게 설계되었는지, 언제 실행되는지를 완벽히 이해하여 문서화
"""

import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 프로젝트 루트를 Python 경로에 추가 (한글 경로 문제 해결)
project_root = Path(r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전")
sys.path.insert(0, str(project_root))

try:
    from core.file_parser import FileParser
    from core.recipient_extractor.main_extractor import RecipientExtractor
    from core.conversion_engine import ConversionEngine
    from core.template_manager import TemplateManager
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("프로젝트 루트 경로를 확인하세요.")
    sys.exit(1)

class MasterConversionTester:
    """변환 시스템 실제 테스트 100% 마스터 클래스"""
    
    def __init__(self):
        self.test_files = [
            r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\tests\input\sample_invoice.xlsx",
            r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\tests\input\sample_invoice2.xlsx", 
            r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\tests\input\sample_invoice3.xlsx",
            r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\tests\input\sample_invoice4.xlsx"
        ]
        
        # 로그 디렉토리 생성 (한글 경로 문제 해결)
        self.log_dir = Path(r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\logs\master_test")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 결과 저장 디렉토리
        self.result_dir = Path(r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\tests\output\master")
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # 상세 분석 결과 저장
        self.analysis_dir = Path(r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전\변환규칙\실제테스트_분석결과")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        self.all_results = []
        self.line_tracking = {}  # 라인 단위 실행 추적
        self.variable_tracking = {}  # 변수 값 변화 추적
        self.function_call_order = []  # 함수 호출 순서 추적
        
    def setup_detailed_logging(self, test_file_name: str) -> logging.Logger:
        """상세 로깅 설정 - 라인 단위 실행 추적"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{test_file_name}_{timestamp}.log"
        
        # 로거 생성
        logger = logging.getLogger(f"master_test_{test_file_name}")
        logger.setLevel(logging.DEBUG)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 파일 핸들러 추가
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 상세 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def track_function_call(self, function_name: str, file_path: str, line_number: int, 
                           input_data: Dict = None, output_data: Dict = None):
        """함수 호출 추적"""
        call_info = {
            'timestamp': datetime.now().isoformat(),
            'function_name': function_name,
            'file_path': file_path,
            'line_number': line_number,
            'input_data': input_data,
            'output_data': output_data
        }
        self.function_call_order.append(call_info)
    
    def track_variable_change(self, variable_name: str, old_value: Any, new_value: Any, 
                            context: str = ""):
        """변수 값 변화 추적"""
        if variable_name not in self.variable_tracking:
            self.variable_tracking[variable_name] = []
        
        change_info = {
            'timestamp': datetime.now().isoformat(),
            'old_value': old_value,
            'new_value': new_value,
            'context': context
        }
        self.variable_tracking[variable_name].append(change_info)
    
    def test_single_file_master(self, file_path: str) -> Dict[str, Any]:
        """단일 파일 실제 변환 테스트 - 마스터 레벨"""
        file_name = Path(file_path).name.replace('.xlsx', '')
        
        print(f"\n🔬 마스터 레벨 실제 변환 테스트 시작: {file_name}")
        print("=" * 80)
        
        # 상세 로깅 설정
        logger = self.setup_detailed_logging(file_name)
        
        result = {
            'file_name': file_name,
            'file_path': file_path,
            'start_time': time.time(),
            'steps': [],
            'line_tracking': {},
            'variable_tracking': {},
            'function_calls': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: 파일 파싱 (FileParser)
            logger.info(f"📁 Step 1: 파일 파싱 시작 - {file_path}")
            self.track_function_call("parse_file", "core/file_parser.py", 95, 
                                   {"file_path": file_path})
            
            file_parser = FileParser()
            parsed_data = file_parser.parse_file(file_path)
            
            self.track_function_call("parse_file", "core/file_parser.py", 95, 
                                   {"file_path": file_path}, parsed_data)
            
            step1_result = {
                'step': 1,
                'name': '파일 파싱',
                'function': 'FileParser.parse_file()',
                'file_location': 'core/file_parser.py:95',
                'input': {'file_path': file_path},
                'output': parsed_data,
                'execution_time': time.time() - result['start_time']
            }
            result['steps'].append(step1_result)
            logger.info(f"✅ Step 1 완료: {len(parsed_data.get('families', []))}개 가족 데이터 추출")
            
            # Step 2: 공급받는자 추출 (RecipientExtractor)
            logger.info(f"👥 Step 2: 공급받는자 추출 시작")
            self.track_function_call("extract_recipients", "core/recipient_extractor/main_extractor.py", 
                                   None, {"parsed_data": parsed_data})
            
            recipient_extractor = RecipientExtractor()
            extracted_recipients = recipient_extractor.extract_recipients(parsed_data)
            
            self.track_function_call("extract_recipients", "core/recipient_extractor/main_extractor.py", 
                                   None, {"parsed_data": parsed_data}, extracted_recipients)
            
            step2_result = {
                'step': 2,
                'name': '공급받는자 추출',
                'function': 'RecipientExtractor.extract_recipients()',
                'file_location': 'core/recipient_extractor/main_extractor.py',
                'input': {'parsed_data': parsed_data},
                'output': extracted_recipients,
                'execution_time': time.time() - result['start_time']
            }
            result['steps'].append(step2_result)
            logger.info(f"✅ Step 2 완료: {len(extracted_recipients)}개 공급받는자 추출")
            
            # Step 3: 변환 엔진 (ConversionEngine)
            logger.info(f"🔄 Step 3: 변환 엔진 시작")
            self.track_function_call("convert_data", "core/conversion_engine.py", 
                                   None, {"recipients": extracted_recipients})
            
            conversion_engine = ConversionEngine()
            converted_data = conversion_engine.convert_data(extracted_recipients)
            
            self.track_function_call("convert_data", "core/conversion_engine.py", 
                                   None, {"recipients": extracted_recipients}, converted_data)
            
            step3_result = {
                'step': 3,
                'name': '변환 엔진',
                'function': 'ConversionEngine.convert_data()',
                'file_location': 'core/conversion_engine.py',
                'input': {'recipients': extracted_recipients},
                'output': converted_data,
                'execution_time': time.time() - result['start_time']
            }
            result['steps'].append(step3_result)
            logger.info(f"✅ Step 3 완료: {len(converted_data)}개 데이터 변환")
            
            # Step 4: 템플릿 생성 (TemplateManager)
            logger.info(f"📄 Step 4: 템플릿 생성 시작")
            self.track_function_call("generate_template", "core/template_manager.py", 
                                   None, {"converted_data": converted_data})
            
            template_manager = TemplateManager()
            template_result = template_manager.generate_template(converted_data)
            
            self.track_function_call("generate_template", "core/template_manager.py", 
                                   None, {"converted_data": converted_data}, template_result)
            
            step4_result = {
                'step': 4,
                'name': '템플릿 생성',
                'function': 'TemplateManager.generate_template()',
                'file_location': 'core/template_manager.py',
                'input': {'converted_data': converted_data},
                'output': template_result,
                'execution_time': time.time() - result['start_time']
            }
            result['steps'].append(step4_result)
            logger.info(f"✅ Step 4 완료: 템플릿 생성 완료")
            
            # 최종 결과 정리
            result['success'] = True
            result['total_execution_time'] = time.time() - result['start_time']
            result['line_tracking'] = self.line_tracking.copy()
            result['variable_tracking'] = self.variable_tracking.copy()
            result['function_calls'] = self.function_call_order.copy()
            
            logger.info(f"🎉 마스터 테스트 완료: {file_name} (총 {result['total_execution_time']:.2f}초)")
            
        except Exception as e:
            error_msg = f"❌ 마스터 테스트 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(f"상세 오류: {traceback.format_exc()}")
            
            result['success'] = False
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
            result['errors'].append(error_msg)
        
        return result
    
    def run_all_master_tests(self):
        """모든 파일에 대해 마스터 테스트 실행"""
        print("🚀 변환 시스템 실제 테스트 100% 마스터 시작")
        print("=" * 80)
        
        for file_path in self.test_files:
            if not Path(file_path).exists():
                print(f"⚠️ 파일이 존재하지 않습니다: {file_path}")
                continue
            
            result = self.test_single_file_master(file_path)
            self.all_results.append(result)
            
            # 결과 저장
            result_file = self.result_dir / f"{result['file_name']}_master_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        # 전체 결과 요약 생성
        self.generate_master_summary()
        
        print("\n🎯 마스터 테스트 완료!")
        print(f"총 {len(self.all_results)}개 파일 테스트 완료")
        print(f"결과 저장 위치: {self.result_dir}")
        print(f"로그 저장 위치: {self.log_dir}")
    
    def generate_master_summary(self):
        """마스터 테스트 결과 요약 생성"""
        summary = {
            'test_info': {
                'total_files': len(self.all_results),
                'successful_tests': len([r for r in self.all_results if r.get('success', False)]),
                'failed_tests': len([r for r in self.all_results if not r.get('success', False)]),
                'test_date': datetime.now().isoformat()
            },
            'file_results': [],
            'line_tracking_summary': {},
            'variable_tracking_summary': {},
            'function_call_summary': {},
            'performance_metrics': {}
        }
        
        for result in self.all_results:
            file_summary = {
                'file_name': result['file_name'],
                'success': result.get('success', False),
                'execution_time': result.get('total_execution_time', 0),
                'steps_count': len(result.get('steps', [])),
                'errors_count': len(result.get('errors', [])),
                'warnings_count': len(result.get('warnings', []))
            }
            summary['file_results'].append(file_summary)
        
        # 성능 지표 계산
        successful_results = [r for r in self.all_results if r.get('success', False)]
        if successful_results:
            execution_times = [r.get('total_execution_time', 0) for r in successful_results]
            summary['performance_metrics'] = {
                'average_execution_time': sum(execution_times) / len(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'total_execution_time': sum(execution_times)
            }
        
        # 요약 저장
        summary_file = self.analysis_dir / "마스터테스트_전체요약.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📊 마스터 테스트 요약 생성: {summary_file}")

def main():
    """메인 실행 함수"""
    tester = MasterConversionTester()
    tester.run_all_master_tests()

if __name__ == "__main__":
    main()
