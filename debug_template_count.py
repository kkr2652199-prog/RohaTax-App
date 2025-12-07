"""
템플릿 개수 계산 디버깅 스크립트
실제 데이터 구조를 확인하여 필터링이 제대로 작동하는지 검증
"""

import sqlite3
import json
from core.db import get_conn
from core.file_parser import FileParser
from core.file_parser_utils.industry_rules import IndustryRules

def debug_template_count():
    """템플릿 개수 계산 과정 디버깅"""
    print("=" * 80)
    print("템플릿 개수 계산 디버깅")
    print("=" * 80)
    
    # 테스트 파일 경로 (실제 파일 경로로 변경 필요)
    test_file = "temp/test_file.xlsx"  # 실제 테스트 파일 경로
    
    try:
        # 1. 파일 파싱
        file_parser = FileParser()
        parsed_data = file_parser.parse_file(test_file)
        
        if not parsed_data or parsed_data.get('parsing_status') != 'success':
            print("❌ 파일 파싱 실패")
            return
        
        print(f"✅ 파일 파싱 성공")
        print(f"   - 검열 전 건수: {parsed_data.get('total_rows', 0)}건")
        
        # 2. families 데이터 확인
        raw_families = parsed_data.get('families', [])
        print(f"\n📊 raw_families 개수: {len(raw_families)}건")
        
        if raw_families:
            # 3. 가족 통합
            rules = IndustryRules()
            merged_families = rules.merge_family_data(raw_families)
            print(f"📊 merged_families 개수: {len(merged_families)}건")
            
            # 4. merged_families 구조 확인
            if merged_families:
                sample = merged_families[0]
                print(f"\n📋 merged_families 샘플 구조:")
                print(f"   - 키 목록: {list(sample.keys())}")
                print(f"   - mom_amount: {sample.get('mom_amount', 'N/A')}")
                print(f"   - 부가세: {sample.get('부가세', 'N/A')}")
                print(f"   - dad_amount: {sample.get('dad_amount', 'N/A')}")
                print(f"   - 공급가액: {sample.get('공급가액', 'N/A')}")
            
            # 5. 엄마값 0인 항목 확인
            mom_zero_count = 0
            mom_non_zero_count = 0
            for f in merged_families:
                mom_amount = f.get('mom_amount', 0)
                부가세 = f.get('부가세', 0)
                if mom_amount == 0 and 부가세 == 0:
                    mom_zero_count += 1
                else:
                    mom_non_zero_count += 1
            
            print(f"\n📊 엄마값 분석:")
            print(f"   - 엄마값 0인 항목: {mom_zero_count}건")
            print(f"   - 엄마값 0이 아닌 항목: {mom_non_zero_count}건")
            
            # 6. 필터링 테스트
            valid_families = [
                f for f in merged_families 
                if f.get('mom_amount', 0) != 0 or f.get('부가세', 0) != 0
            ]
            print(f"\n✅ 필터링 결과:")
            print(f"   - 원본: {len(merged_families)}건")
            print(f"   - 필터링 후: {len(valid_families)}건")
            print(f"   - 제외된 항목: {len(merged_families) - len(valid_families)}건")
            
            # 7. 필터링이 작동하지 않는 경우 상세 분석
            if len(valid_families) == len(merged_families):
                print(f"\n⚠️ 경고: 필터링이 작동하지 않음!")
                print(f"   - 모든 항목이 엄마값 0이 아닌 것으로 판단됨")
                print(f"   - 상세 분석:")
                for i, f in enumerate(merged_families[:5]):  # 처음 5개만
                    mom = f.get('mom_amount', 0)
                    부가세 = f.get('부가세', 0)
                    print(f"      [{i+1}] mom_amount={mom}, 부가세={부가세}, 타입: mom={type(mom)}, 부가세={type(부가세)}")
        else:
            print(f"\n⚠️ raw_families가 비어있음")
            print(f"   - else 분기로 이동하여 recipients 사용")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_template_count()

