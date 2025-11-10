#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 변환 엔진 테스트 스크립트

실제 FileParser, RecipientExtractor, ConversionEngine을 사용하여
sample_invoice 파일들을 테스트하고 상세 로그를 생성합니다.
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
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

class RealConversionTester:
    """실제 변환 엔진 테스트 클래스"""
    
    def __init__(self):
        self.test_files = [
            "tests/input/sample_invoice.xlsx",
            "tests/input/sample_invoice2.xlsx", 
            "tests/input/sample_invoice3.xlsx",
            "tests/input/sample_invoice4.xlsx"
        ]
        
        # 로그 디렉토리 생성
        self.log_dir = Path("logs/real_test")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 결과 저장 디렉토리
        self.result_dir = Path("변환규칙/실제_테스트_결과")
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        self.all_results = []
        
    def setup_logging(self, test_file_name):
        """테스트별 로그 설정"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{test_file_name}_{timestamp}.log"
        
        # 로거 생성
        logger = logging.getLogger(f"real_test_{test_file_name}")
        logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 파일 핸들러 추가
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger, log_file
    
    def test_single_file(self, file_path):
        """단일 파일 실제 변환 테스트"""
        file_name = Path(file_path).name.replace('.xlsx', '')
        
        print(f"\n🧪 실제 변환 테스트 시작: {file_name}")
        print("=" * 60)
        
        # 로그 설정
        logger, log_file = self.setup_logging(file_name)
        
        result = {
            'file_name': file_name,
            'file_path': file_path,
            'log_file': str(log_file),
            'start_time': time.time(),
            'success': False,
            'errors': [],
            'steps': {}
        }
        
        try:
            # 1단계: 파일 파싱
            logger.info(f"📊 1단계: 파일 파싱 시작 - {file_path}")
            parser = FileParser()
            
            parsed_data = parser.parse_file(file_path)
            result['steps']['parsing'] = {
                'success': parsed_data.get('parsing_status') == 'success',
                'selected_sheet': parsed_data.get('selected_sheet'),
                'total_rows': parsed_data.get('total_rows', 0),
                'families_count': len(parsed_data.get('families', []))
            }
            
            if parsed_data.get('parsing_status') != 'success':
                raise Exception(f"파싱 실패: {parsed_data.get('error', 'Unknown error')}")
            
            logger.info(f"✅ 파싱 성공: 시트 '{parsed_data.get('selected_sheet')}', 행 {parsed_data.get('total_rows')}개")
            
            # 2단계: 공급받는자 추출
            logger.info(f"👥 2단계: 공급받는자 추출 시작")
            extractor = RecipientExtractor()
            
            recipients = extractor.extract_recipients(parsed_data)
            result['steps']['extraction'] = {
                'success': len(recipients) > 0,
                'recipient_count': len(recipients),
                'family_integration_count': sum(1 for r in recipients if r.get('family_integrated', False))
            }
            
            if len(recipients) == 0:
                raise Exception("공급받는자 추출 실패: 추출된 데이터 없음")
            
            logger.info(f"✅ 추출 성공: {len(recipients)}건, 가족통합 {result['steps']['extraction']['family_integration_count']}건")
            
            # 3단계: 변환 엔진 실행
            logger.info(f"🔄 3단계: 변환 엔진 실행")
            conversion_engine = ConversionEngine()
            
            conversion_result = conversion_engine.convert_to_hometax_template(
                parsed_data, recipients
            )
            result['steps']['conversion'] = {
                'success': conversion_result.get('success', False),
                'converted_count': conversion_result.get('converted_count', 0),
                'template_file': conversion_result.get('template_file', '')
            }
            
            if not conversion_result.get('success'):
                raise Exception(f"변환 실패: {conversion_result.get('error', 'Unknown error')}")
            
            logger.info(f"✅ 변환 성공: {conversion_result.get('converted_count', 0)}건")
            
            # 4단계: 템플릿 기입
            logger.info(f"📝 4단계: 템플릿 기입")
            template_manager = TemplateManager()
            
            template_result = template_manager.fill_template(recipients)
            result['steps']['template_filling'] = {
                'success': template_result.get('success', False),
                'filled_count': template_result.get('filled_count', 0)
            }
            
            if not template_result.get('success'):
                raise Exception(f"템플릿 기입 실패: {template_result.get('error', 'Unknown error')}")
            
            logger.info(f"✅ 템플릿 기입 성공: {template_result.get('filled_count', 0)}건")
            
            result['success'] = True
            logger.info(f"🎉 전체 테스트 성공: {file_name}")
            
        except Exception as e:
            error_msg = f"테스트 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(f"상세 오류: {traceback.format_exc()}")
            result['errors'].append(error_msg)
            
        finally:
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - result['start_time']
            
            logger.info(f"⏱️ 테스트 완료: {result['duration']:.2f}초")
            logger.info(f"📄 로그 파일: {log_file}")
            
            # 핸들러 정리
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        return result
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 실제 변환 엔진 테스트 시작")
        print("=" * 80)
        
        for file_path in self.test_files:
            if os.path.exists(file_path):
                result = self.test_single_file(file_path)
                self.all_results.append(result)
            else:
                print(f"⚠️ 파일을 찾을 수 없음: {file_path}")
        
        # 종합 결과 출력
        self.print_summary()
        
        # 결과 저장
        self.save_results()
        
        return self.all_results
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📊 실제 테스트 결과 요약")
        print("=" * 80)
        
        success_count = sum(1 for r in self.all_results if r['success'])
        total_count = len(self.all_results)
        
        print(f"총 테스트 파일: {total_count}개")
        print(f"성공한 테스트: {success_count}개")
        print(f"실패한 테스트: {total_count - success_count}개")
        print(f"성공률: {success_count/total_count*100:.1f}%")
        
        print(f"\n평균 처리 시간: {sum(r['duration'] for r in self.all_results)/total_count:.2f}초")
        
        print("\n📋 파일별 상세 결과:")
        print("-" * 60)
        for result in self.all_results:
            status = "✅ 성공" if result['success'] else "❌ 실패"
            duration = f"{result['duration']:.2f}초"
            
            print(f"{result['file_name']:20} | {status:8} | {duration:8}")
            
            if result['success']:
                steps = result['steps']
                print(f"  └─ 파싱: {steps['parsing']['selected_sheet']}")
                print(f"  └─ 추출: {steps['extraction']['recipient_count']}건")
                print(f"  └─ 변환: {steps['conversion']['converted_count']}건")
                print(f"  └─ 기입: {steps['template_filling']['filled_count']}건")
            else:
                for error in result['errors']:
                    print(f"  └─ 오류: {error}")
    
    def save_results(self):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.result_dir / f"실제_테스트_결과_{timestamp}.md"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"# 실제 변환 엔진 테스트 결과\n\n")
            f.write(f"## 테스트 개요\n")
            f.write(f"- 테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 테스트 파일 수: {len(self.all_results)}개\n")
            f.write(f"- 성공한 테스트: {sum(1 for r in self.all_results if r['success'])}개\n")
            f.write(f"- 실패한 테스트: {sum(1 for r in self.all_results if not r['success'])}개\n\n")
            
            # 파일별 상세 결과
            f.write("## 파일별 상세 결과\n\n")
            for result in self.all_results:
                f.write(f"### {result['file_name']}\n")
                f.write(f"- 파일 경로: {result['file_path']}\n")
                f.write(f"- 로그 파일: {result['log_file']}\n")
                f.write(f"- 테스트 결과: {'✅ 성공' if result['success'] else '❌ 실패'}\n")
                f.write(f"- 소요 시간: {result['duration']:.2f}초\n")
                
                if result['success']:
                    steps = result['steps']
                    f.write(f"- 파싱 결과: 시트 '{steps['parsing']['selected_sheet']}', 행 {steps['parsing']['total_rows']}개\n")
                    f.write(f"- 추출 결과: {steps['extraction']['recipient_count']}건, 가족통합 {steps['extraction']['family_integration_count']}건\n")
                    f.write(f"- 변환 결과: {steps['conversion']['converted_count']}건\n")
                    f.write(f"- 기입 결과: {steps['template_filling']['filled_count']}건\n")
                else:
                    f.write("- 오류 내용:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")
                
                f.write("\n")
        
        print(f"\n📄 결과 저장 완료: {result_file}")

def main():
    """메인 함수"""
    print("실제 변환 엔진 테스트 시작")
    print("이 테스트는 실제 FileParser, RecipientExtractor, ConversionEngine을 사용합니다.")
    
    tester = RealConversionTester()
    results = tester.run_all_tests()
    
    print(f"\n✅ 테스트 완료!")
    print(f"📊 결과 요약: {sum(1 for r in results if r['success'])}/{len(results)} 성공")
    print(f"📁 로그 파일: logs/real_test/")
    print(f"📁 결과 파일: 변환규칙/실제_테스트_결과/")

if __name__ == "__main__":
    main()



