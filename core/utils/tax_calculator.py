"""
부가세 계산 유틸리티
상용화 준비: 표준화된 세금 계산 로직

로직:
- 입력받은 total_amount는 무조건 '부가세 포함 금액'이다.
- supply_price (공급가) = total_amount / 1.1 (반올림)
- vat (부가세) = total_amount - supply_price
"""

import math
from typing import Tuple, Dict, Any


def calculate_tax(total_amount: int) -> Tuple[int, int]:
    """
    부가세 포함 금액에서 공급가와 부가세를 계산
    
    Args:
        total_amount: 부가세 포함 총 금액 (원 단위, 정수)
        
    Returns:
        Tuple[int, int]: (supply_price, vat) 튜플
        - supply_price: 공급가액 (원 단위, 정수)
        - vat: 부가세 (원 단위, 정수)
        
    Example:
        >>> supply_price, vat = calculate_tax(11000)
        >>> print(supply_price, vat)
        10000 1000
    """
    if total_amount < 0:
        raise ValueError("금액은 0 이상이어야 합니다")
    
    if total_amount == 0:
        return (0, 0)
    
    # 공급가액 계산: total_amount / 1.1 (반올림)
    supply_price = round(total_amount / 1.1)
    
    # 부가세 계산: total_amount - supply_price
    vat = total_amount - supply_price
    
    return (supply_price, vat)


def calculate_tax_dict(total_amount: int) -> Dict[str, int]:
    """
    부가세 포함 금액에서 공급가와 부가세를 계산 (딕셔너리 반환)
    
    Args:
        total_amount: 부가세 포함 총 금액 (원 단위, 정수)
        
    Returns:
        Dict[str, int]: {
            'supply_price': 공급가액 (원 단위, 정수),
            'vat': 부가세 (원 단위, 정수),
            'total_amount': 총 금액 (원 단위, 정수)
        }
    """
    supply_price, vat = calculate_tax(total_amount)
    
    return {
        'supply_price': supply_price,
        'vat': vat,
        'total_amount': total_amount
    }


def calculate_total_with_vat(supply_price: int) -> Tuple[int, int]:
    """
    공급가액에서 부가세를 가산하여 총 금액 계산 (부가세 별도 과금 방식)
    
    Args:
        supply_price: 공급가액 (원 단위, 정수)
        
    Returns:
        Tuple[int, int]: (total_amount, vat) 튜플
        - total_amount: 부가세 포함 총 금액 (원 단위, 정수)
        - vat: 부가세 (원 단위, 정수)
        
    Example:
        >>> total_amount, vat = calculate_total_with_vat(10000)
        >>> print(total_amount, vat)
        11000 1000
    """
    if supply_price < 0:
        raise ValueError("공급가액은 0 이상이어야 합니다")
    
    if supply_price == 0:
        return (0, 0)
    
    # 부가세 계산: supply_price * 0.1 (반올림)
    vat = round(supply_price * 0.1)
    
    # 총 금액 계산: supply_price + vat
    total_amount = supply_price + vat
    
    return (total_amount, vat)


def validate_tax_calculation(supply_price: int, vat: int, total_amount: int) -> bool:
    """
    세금 계산 결과 검증
    
    Args:
        supply_price: 공급가액
        vat: 부가세
        total_amount: 총 금액
        
    Returns:
        bool: 검증 통과 여부
    """
    # 총 금액 = 공급가액 + 부가세
    if supply_price + vat != total_amount:
        return False
    
    # 부가세 = 공급가액 * 0.1 (10% VAT)
    # 허용 오차: ±1원 (반올림 오차)
    expected_vat = round(supply_price * 0.1)
    if abs(vat - expected_vat) > 1:
        return False
    
    return True


if __name__ == '__main__':
    """
    테스트 코드
    11,000원을 넣었을 때 10,000원(공급가)과 1,000원(부가세)이 나오는지 확인
    """
    print("=" * 50)
    print("부가세 계산기 테스트")
    print("=" * 50)
    
    # 테스트 케이스 1: 11,000원
    test_amount = 11000
    supply_price, vat = calculate_tax(test_amount)
    
    print(f"\n[테스트 1] 총 금액: {test_amount:,}원")
    print(f"  공급가액: {supply_price:,}원")
    print(f"  부가세: {vat:,}원")
    print(f"  합계: {supply_price + vat:,}원")
    
    # 검증
    if supply_price == 10000 and vat == 1000:
        print("  ✅ 테스트 통과: 11,000원 → 10,000원(공급가) + 1,000원(부가세)")
    else:
        print(f"  ❌ 테스트 실패: 예상값 (10,000, 1,000), 실제값 ({supply_price}, {vat})")
    
    # 검증 함수 테스트
    is_valid = validate_tax_calculation(supply_price, vat, test_amount)
    print(f"  검증 결과: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    # 테스트 케이스 2: 딕셔너리 반환
    print(f"\n[테스트 2] 딕셔너리 반환 테스트")
    result_dict = calculate_tax_dict(test_amount)
    print(f"  결과: {result_dict}")
    
    if result_dict['supply_price'] == 10000 and result_dict['vat'] == 1000:
        print("  ✅ 테스트 통과")
    else:
        print(f"  ❌ 테스트 실패")
    
    # 테스트 케이스 3: 다양한 금액
    print(f"\n[테스트 3] 다양한 금액 테스트")
    test_cases = [
        1000,   # 1,000원
        5000,   # 5,000원
        10000,  # 10,000원
        55000,  # 55,000원
        100000, # 100,000원
    ]
    
    for amount in test_cases:
        supply, vat = calculate_tax(amount)
        is_valid = validate_tax_calculation(supply, vat, amount)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {amount:,}원 → 공급가: {supply:,}원, 부가세: {vat:,}원")
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

