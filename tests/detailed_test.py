#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2순위 파일 정밀 테스트 스크립트
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Force UTF-8 for reliable Korean output on Windows
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.conversion_engine import ConversionEngine
from core.file_parser import FileParser
from core.recipient_extractor.main_extractor import RecipientExtractor


def analyze_file_structure(file_path):
    """파일 구조 분석"""
    print(f"\n=== 파일 구조 분석: {os.path.basename(file_path)} ===")
    
    try:
        # Excel 파일 읽기
        excel_file = pd.ExcelFile(file_path)
        print(f"시트 목록: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- 시트: {sheet_name} ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")
            print(f"컬럼명: {list(df.columns)}")
            
            # 첫 5행 미리보기
            print("첫 5행 데이터:")
            print(df.head().to_string())
            
    except Exception as e:
        print(f"파일 분석 오류: {e}")


def test_conversion_process(file_path):
    """변환 프로세스 상세 테스트"""
    print(f"\n=== 변환 프로세스 테스트 ===")
    
    # 1. 파일 파싱 테스트
    print("\n1단계: 파일 파싱")
    parser = FileParser()
    try:
        parsed_data = parser.parse_file(file_path)
        print(f"파싱 성공: {len(parsed_data.get('data_section', []))}행")
        print(f"파싱된 데이터 샘플:")
        if parsed_data.get('data_section'):
            sample = parsed_data['data_section'][0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"파싱 오류: {e}")
        return None
    
    # 2. 수신자 추출 테스트
    print("\n2단계: 수신자 추출")
    extractor = RecipientExtractor()
    try:
        recipients = extractor.extract_recipients_simple(
            parsed_data, 
            industry="delivery"
        )
        print(f"추출 성공: {len(recipients)}건")
        
        # 추출된 데이터 샘플
        if recipients:
            sample = recipients[0]
            print("추출된 데이터 샘플:")
            for key, value in sample.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"추출 오류: {e}")
        return None
    
    return recipients


def test_full_conversion(file_path):
    """전체 변환 테스트"""
    print(f"\n=== 전체 변환 테스트 ===")
    
    engine = ConversionEngine()
    supplier_info = {
        "company_name": "테스트공급자",
        "business_number": "123-45-67890",
        "representative_name": "홍길동",
        "address": "서울시 테스트로 1",
        "business_type": "도소매업",
        "business_category": "기타",
        "email": "test@supplier.com",
    }

    start_time = datetime.now()
    
    try:
        result = engine.convert_file(
            uploaded_file_path=file_path,
            supplier_info=supplier_info,
            template_id="hometax_official",
            industry_type="delivery",
            guidelines={},
            issue_date=None,
            user_info={"business_number": "1234567890", "company_name": "테스트공급자"},
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"변환 완료: {duration:.2f}초")
        print(f"결과: {result.get('success', False)}")
        print(f"메시지: {result.get('message', 'N/A')}")
        print(f"추출 건수: {result.get('extracted_count', 0)}")
        print(f"생성 파일: {result.get('output_files', [])}")
        
        return result
        
    except Exception as e:
        print(f"변환 오류: {e}")
        return None


def generate_detailed_report(result, file_path):
    """상세 리포트 생성"""
    if not result:
        return
    
    report = {
        "test_info": {
            "file": os.path.basename(file_path),
            "test_time": datetime.now().isoformat(),
            "test_type": "2순위 파일 정밀 테스트"
        },
        "conversion_result": result,
        "analysis": {
            "success": result.get('success', False),
            "extracted_count": result.get('extracted_count', 0),
            "output_files": result.get('output_files', []),
            "processing_time": result.get('processing_time', 0),
            "errors": result.get('errors', []),
            "warnings": result.get('warnings', [])
        }
    }
    
    # 리포트 저장
    report_path = os.path.join(PROJECT_ROOT, "tests", "detailed_test_result.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n상세 리포트 저장: {report_path}")


def main():
    """메인 테스트 실행"""
    print("=== 2순위 파일 정밀 테스트 시작 ===")
    
    # 테스트 파일 경로
    base = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base, "tests", "input", "sample_invoice2.xlsx")
    
    if not os.path.exists(test_file):
        print(f"테스트 파일을 찾을 수 없습니다: {test_file}")
        return
    
    # 1. 파일 구조 분석
    analyze_file_structure(test_file)
    
    # 2. 변환 프로세스 테스트
    recipients = test_conversion_process(test_file)
    
    # 3. 전체 변환 테스트
    result = test_full_conversion(test_file)
    
    # 4. 상세 리포트 생성
    generate_detailed_report(result, test_file)
    
    print("\n=== 정밀 테스트 완료 ===")


if __name__ == "__main__":
    main()
