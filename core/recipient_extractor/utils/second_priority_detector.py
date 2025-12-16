"""
2순위 시트 감지 로직 모듈

main_extractor.py의 2순위 시트 감지 관련 로직을 독립 모듈로 분리
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def detect_second_priority_sheet(recipients: List[Dict[str, Any]], logger_instance: logging.Logger = None) -> bool:
    """
    🎯 2순위 시트 감지: 분산된 가족이 있는지 확인
    
    분산된 가족 통합 예외 지침 적용 조건:
    - 같은 사업자번호의 여러 행이 있는지 확인
    - 상호나 대표자명이 다른 경우가 있는지 확인
    
    Args:
        recipients: 추출된 공급받는자 리스트
        logger_instance: 로거 인스턴스 (선택사항)
        
    Returns:
        bool: 2순위 시트 여부 (분산된 가족이 있으면 True)
    """
    log = logger_instance or logger
    
    if not recipients:
        return False
    
    # 사업자번호별로 그룹화
    business_groups = {}
    for recipient in recipients:
        business_num = recipient.get('사업자등록번호', '')
        if business_num and business_num != '':
            if business_num not in business_groups:
                business_groups[business_num] = []
            business_groups[business_num].append(recipient)
    
    # 분산된 가족이 있는지 확인
    for business_num, group in business_groups.items():
        if len(group) > 1:
            # 같은 사업자번호의 여러 행이 있음
            # 상호나 대표자명이 다른지 확인
            store_names = [r.get('상호', '') for r in group if r.get('상호', '')]
            representative_names = [r.get('대표명', '') for r in group if r.get('대표명', '')]
            
            # 상호나 대표자명이 다른 경우가 있으면 분산된 가족
            if len(set(store_names)) > 1 or len(set(representative_names)) > 1:
                log.info(f"🎯 2순위 시트 감지: 사업자번호 {business_num} - 분산된 가족 {len(group)}건")
                return True
    
    return False

