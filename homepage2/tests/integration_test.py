#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2순위 시트 정밀 테스트 - 통합 로직 분석
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from collections import defaultdict

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


def analyze_integration_logic(file_path):
    """통합 로직 상세 분석"""
    print(f"\n=== 통합 로직 정밀 분석: {os.path.basename(file_path)} ===")
    
    # 전체 변환 실행
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

    result = engine.convert_file(
        uploaded_file_path=file_path,
        supplier_info=supplier_info,
        template_id="hometax_official",
        industry_type="delivery",
        guidelines={},
        issue_date=None,
        user_info={"business_number": "1234567890", "company_name": "테스트공급자"},
    )
    
    if not result.get('success'):
        print("❌ 변환 실패")
        return None
    
    # 추출된 데이터 분석
    recipients = result.get('recipients_preview', [])
    print(f"\n📊 추출된 총 건수: {len(recipients)}")
    
    # 사업자등록번호별 그룹화 분석
    business_number_groups = defaultdict(list)
    representative_groups = defaultdict(list)
    
    for recipient in recipients:
        business_number = recipient.get('사업자등록번호', '')
        representative = recipient.get('대표명', '')
        
        business_number_groups[business_number].append(recipient)
        representative_groups[representative].append(recipient)
    
    print(f"\n🔍 사업자등록번호별 그룹 수: {len(business_number_groups)}")
    print(f"🔍 대표자명별 그룹 수: {len(representative_groups)}")
    
    # 사업자등록번호 중복 분석
    print(f"\n📋 사업자등록번호 중복 분석:")
    duplicate_business_numbers = {k: v for k, v in business_number_groups.items() if len(v) > 1}
    
    if duplicate_business_numbers:
        print(f"  중복된 사업자등록번호: {len(duplicate_business_numbers)}개")
        for business_number, group in duplicate_business_numbers.items():
            print(f"    사업자번호 {business_number}: {len(group)}건")
            total_supply = sum(item.get('공급가액', 0) for item in group)
            total_vat = sum(item.get('부가세', 0) for item in group)
            print(f"      합산 공급가액: {total_supply:,.0f}원")
            print(f"      합산 부가세: {total_vat:,.0f}원")
            print(f"      대표자명들: {[item.get('대표명', '') for item in group]}")
    else:
        print("  중복된 사업자등록번호 없음")
    
    # 대표자명 중복 분석
    print(f"\n📋 대표자명 중복 분석:")
    duplicate_representatives = {k: v for k, v in representative_groups.items() if len(v) > 1}
    
    if duplicate_representatives:
        print(f"  중복된 대표자명: {len(duplicate_representatives)}개")
        for representative, group in duplicate_representatives.items():
            print(f"    대표자 {representative}: {len(group)}건")
            business_numbers = [item.get('사업자등록번호', '') for item in group]
            print(f"      사업자번호들: {business_numbers}")
            
            # 사업자번호가 다른 경우만 표시
            unique_business_numbers = set(business_numbers)
            if len(unique_business_numbers) > 1:
                print(f"      ⚠️ 서로 다른 사업자번호: {len(unique_business_numbers)}개")
                for bn in unique_business_numbers:
                    bn_group = [item for item in group if item.get('사업자등록번호') == bn]
                    total_supply = sum(item.get('공급가액', 0) for item in bn_group)
                    print(f"        {bn}: 공급가액 {total_supply:,.0f}원")
    else:
        print("  중복된 대표자명 없음")
    
    # 통합 로직 시뮬레이션
    print(f"\n🔄 통합 로직 시뮬레이션:")
    
    # 1단계: 사업자등록번호별 통합
    integrated_by_business_number = {}
    for business_number, group in business_number_groups.items():
        if len(group) > 1:
            # 통합
            integrated = {
                '사업자등록번호': business_number,
                '상호': group[0].get('상호', ''),
                '대표명': group[0].get('대표명', ''),
                '사업장주소': group[0].get('사업장주소', ''),
                '사업자이메일': group[0].get('사업자이메일', ''),
                '공급가액': sum(item.get('공급가액', 0) for item in group),
                '부가세': sum(item.get('부가세', 0) for item in group),
                '요금합계': sum(item.get('요금합계', 0) for item in group),
                '통합된_행수': len(group)
            }
            integrated_by_business_number[business_number] = integrated
            print(f"  사업자번호 {business_number}: {len(group)}행 → 1행 통합")
            print(f"    공급가액: {integrated['공급가액']:,.0f}원")
            print(f"    부가세: {integrated['부가세']:,.0f}원")
        else:
            integrated_by_business_number[business_number] = group[0]
    
    # 최종 통합 결과
    final_count = len(integrated_by_business_number)
    print(f"\n📈 통합 결과:")
    print(f"  원본 건수: {len(recipients)}")
    print(f"  통합 후 건수: {final_count}")
    print(f"  통합률: {((len(recipients) - final_count) / len(recipients) * 100):.1f}%")
    
    return {
        'original_count': len(recipients),
        'integrated_count': final_count,
        'business_number_groups': dict(business_number_groups),
        'representative_groups': dict(representative_groups),
        'duplicate_business_numbers': duplicate_business_numbers,
        'duplicate_representatives': duplicate_representatives,
        'integrated_results': integrated_by_business_number
    }


def generate_integration_report(analysis_result, file_path):
    """통합 분석 리포트 생성"""
    if not analysis_result:
        return
    
    report = {
        "test_info": {
            "file": os.path.basename(file_path),
            "test_time": datetime.now().isoformat(),
            "test_type": "2순위 시트 통합 로직 정밀 분석"
        },
        "integration_analysis": analysis_result,
        "summary": {
            "original_count": analysis_result['original_count'],
            "integrated_count": analysis_result['integrated_count'],
            "integration_rate": ((analysis_result['original_count'] - analysis_result['integrated_count']) / analysis_result['original_count'] * 100),
            "duplicate_business_numbers": len(analysis_result['duplicate_business_numbers']),
            "duplicate_representatives": len(analysis_result['duplicate_representatives'])
        }
    }
    
    # 리포트 저장
    report_path = os.path.join(PROJECT_ROOT, "tests", "integration_analysis_result.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 통합 분석 리포트 저장: {report_path}")


def main():
    """메인 테스트 실행"""
    print("=== 2순위 시트 통합 로직 정밀 테스트 시작 ===")
    
    # 테스트 파일 경로
    base = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base, "tests", "input", "sample_invoice2.xlsx")
    
    if not os.path.exists(test_file):
        print(f"❌ 테스트 파일을 찾을 수 없습니다: {test_file}")
        return
    
    # 통합 로직 분석
    analysis_result = analyze_integration_logic(test_file)
    
    # 리포트 생성
    generate_integration_report(analysis_result, test_file)
    
    print("\n=== 통합 로직 정밀 테스트 완료 ===")


if __name__ == "__main__":
    main()
