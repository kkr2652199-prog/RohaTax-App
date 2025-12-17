"""
금액 정보 추출 부품 - 배달대행사 정산서에서 요금합계와 부가세 추출
배달대행사 공급받는자 절대지침에 따라 금액 정보 추출 및 계산
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AmountExtractor:
    """요금합계와 부가세 추출"""
    
    def __init__(self):
        """금액 추출기 초기화"""
        self.logger = logger
        
        # 금액 관련 키워드
        self.amount_keywords = [
            "요금합계", "배달요금", "총배달요금", "합계", "총액", "금액", "요금",
            "배달비", "배달수수료", "수수료", "총요금", "전체요금", "배달비용"
        ]
        
        self.vat_keywords = [
            "부가세", "VAT", "세금", "부가가치세", "세액", "부가세액", "세금액"
        ]
        
        # 금액 패턴 (천단위 구분자 포함)
        self.amount_patterns = [
            r'[\d,]+원?',           # 50,000원 또는 50000원
            r'[\d,]+\.?\d*',        # 50,000.00 또는 50000
            r'[\d]+원',             # 50000원
            r'[\d,]+'               # 50,000
        ]
    
    def extract_amounts(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        파싱된 데이터에서 금액 정보 추출
        
        Args:
            parsed_data: FileParser.parse_file() 결과
            
        Returns:
            List[Dict]: 추출된 금액 정보 리스트
            [
                {
                    '요금합계': float,
                    '부가세': float,
                    '공급가액': float,  # 요금합계 - 부가세
                    'confidence': float,
                    'source_row': int,
                    'calculation_method': str  # 'extracted' 또는 'calculated'
                }
            ]
        """
        if parsed_data['parsing_status'] != 'success':
            self.logger.error("파싱 실패된 데이터로부터 금액 추출 시도")
            return []
        
        try:
            df = parsed_data['raw_data']
            amounts = []
            
            # 각 행에서 금액 정보 추출
            for index, row in df.iterrows():
                amount_info = self._extract_from_row(row, index)
                if amount_info and self._validate_amount(amount_info):
                    amounts.append(amount_info)
            
            self.logger.info(f"금액 정보 추출 완료: {len(amounts)}건")
            return amounts
            
        except Exception as e:
            self.logger.error(f"금액 정보 추출 오류: {str(e)}")
            return []
    
    def _extract_from_row(self, row: pd.Series, row_index: int) -> Optional[Dict[str, Any]]:
        """단일 행에서 금액 정보 추출"""
        try:
            # 행의 모든 텍스트 수집
            row_text = " ".join([str(value) for value in row.values if pd.notna(value)])
            
            # 요금합계와 부가세 추출
            total_fee = self._extract_total_fee(row_text, row)
            vat_amount = self._extract_vat(row_text, row)
            
            # 부가세가 없으면 계산
            if not vat_amount and total_fee:
                vat_amount = self._calculate_vat_from_total(total_fee)
                calculation_method = 'calculated'
            else:
                calculation_method = 'extracted'
            
            # 공급가액 계산 (요금합계 - 부가세)
            supply_amount = total_fee - vat_amount if total_fee and vat_amount else total_fee
            
            # 신뢰도 점수 계산
            confidence = self._calculate_confidence(total_fee, vat_amount, calculation_method)
            
            return {
                '요금합계': total_fee,
                '부가세': vat_amount,
                '공급가액': supply_amount,
                'confidence': confidence,
                'source_row': row_index,
                'calculation_method': calculation_method
            }
            
        except Exception as e:
            self.logger.error(f"행 {row_index} 금액 추출 오류: {str(e)}")
            return None
    
    def _extract_total_fee(self, text: str, row: pd.Series) -> float:
        """요금합계 추출"""
        # 키워드 기반 추출
        for keyword in self.amount_keywords:
            if keyword in text:
                # 키워드 다음에 오는 금액 추출
                pattern = f"{keyword}[:\s]*([\d,]+원?)"
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1)
                    amount = self._parse_amount(amount_str)
                    if amount > 0:
                        return amount
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            if any(keyword in str(col_name) for keyword in self.amount_keywords):
                value = str(row[col_name]).strip()
                if value and value != 'nan':
                    amount = self._parse_amount(value)
                    if amount > 0:
                        return amount
        
        # 숫자 패턴으로 직접 추출 (큰 금액 우선)
        amounts = self._extract_all_amounts(text)
        if amounts:
            # 가장 큰 금액을 요금합계로 추정
            return max(amounts)
        
        return 0.0
    
    def _extract_vat(self, text: str, row: pd.Series) -> float:
        """부가세 추출"""
        # 키워드 기반 추출
        for keyword in self.vat_keywords:
            if keyword in text:
                # 키워드 다음에 오는 금액 추출
                pattern = f"{keyword}[:\s]*([\d,]+원?)"
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1)
                    amount = self._parse_amount(amount_str)
                    if amount > 0:
                        return amount
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            if any(keyword in str(col_name) for keyword in self.vat_keywords):
                value = str(row[col_name]).strip()
                if value and value != 'nan':
                    amount = self._parse_amount(value)
                    if amount > 0:
                        return amount
        
        return 0.0
    
    def _extract_all_amounts(self, text: str) -> List[float]:
        """텍스트에서 모든 금액 추출"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                amount = self._parse_amount(match)
                if amount > 0:
                    amounts.append(amount)
        
        return amounts
    
    def _parse_amount(self, amount_str: str) -> float:
        """금액 문자열을 숫자로 변환"""
        try:
            # 천단위 구분자 제거
            cleaned = re.sub(r'[,\s]', '', amount_str)
            
            # 원, 콤마 등 제거
            cleaned = re.sub(r'[원,원\s]', '', cleaned)
            
            # 숫자만 추출
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            if numbers:
                return float(numbers[0])
            
            return 0.0
            
        except (ValueError, IndexError):
            return 0.0
    
    def _calculate_vat_from_total(self, total_amount: float) -> float:
        """
        총액에서 부가세 계산 (10%)
        부가세 = 총액 / 11 (부가세 포함 총액에서 부가세 계산)
        """
        if total_amount <= 0:
            return 0.0
        
        # 부가세 포함 총액에서 부가세 계산
        vat = total_amount / 11
        return round(vat, 2)
    
    def _calculate_confidence(self, total_fee: float, vat_amount: float, 
                              calculation_method: str) -> float:
        """추출된 금액의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        scores = []
        
        # 요금합계 점수
        if total_fee > 0:
            scores.append(0.6)  # 요금합계는 가장 중요
        
        # 부가세 점수
        if vat_amount > 0:
            if calculation_method == 'extracted':
                scores.append(0.4)  # 직접 추출된 부가세
            else:
                scores.append(0.2)  # 계산된 부가세
        
        # 금액 합리성 검증
        if total_fee > 0 and vat_amount > 0:
            calculated_vat = self._calculate_vat_from_total(total_fee)
            if abs(vat_amount - calculated_vat) / calculated_vat < 0.1:  # 10% 오차 허용
                scores.append(0.2)  # 합리적인 금액
        
        return min(sum(scores), 1.0)
    
    def _validate_amount(self, amount_info: Dict[str, Any]) -> bool:
        """추출된 금액 정보 검증"""
        total_fee = amount_info.get('요금합계', 0)
        vat_amount = amount_info.get('부가세', 0)
        confidence = amount_info.get('confidence', 0)
        
        # 최소 요금합계가 있어야 함
        if total_fee <= 0:
            return False
        
        # 신뢰도 0.3 이상
        if confidence < 0.3:
            return False
        
        # 부가세가 총액보다 클 수 없음
        if vat_amount > total_fee:
            return False
        
        return True
    
    def match_amounts_with_recipients(self, recipients: List[Dict], 
                                     amounts: List[Dict]) -> List[Dict]:
        """
        공급받는자와 금액 정보 매칭
        5개 필수 항목이 일치하는 경우에만 금액 정보 추가
        """
        matched_data = []
        
        for recipient in recipients:
            # 해당 행의 금액 정보 찾기
            recipient_row = recipient.get('source_row', -1)
            matching_amount = None
            
            for amount in amounts:
                if amount.get('source_row') == recipient_row:
                    matching_amount = amount
                    break
            
            # 매칭된 데이터 생성
            matched_recipient = recipient.copy()
            if matching_amount:
                matched_recipient.update({
                    '요금합계': matching_amount.get('요금합계', 0),
                    '부가세': matching_amount.get('부가세', 0),
                    '공급가액': matching_amount.get('공급가액', 0),
                    'amount_confidence': matching_amount.get('confidence', 0),
                    'calculation_method': matching_amount.get('calculation_method', 'none')
                })
            else:
                # 금액 정보가 없는 경우 기본값
                matched_recipient.update({
                    '요금합계': 0,
                    '부가세': 0,
                    '공급가액': 0,
                    'amount_confidence': 0,
                    'calculation_method': 'none'
                })
            
            matched_data.append(matched_recipient)
        
        return matched_data
    
    def get_amount_summary(self, amounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """금액 추출 결과 요약"""
        if not amounts:
            return {
                'total_count': 0,
                'total_amount': 0.0,
                'total_vat': 0.0,
                'high_confidence': 0,
                'extraction_rate': 0.0
            }
        
        total_amount = sum(amount.get('요금합계', 0) for amount in amounts)
        total_vat = sum(amount.get('부가세', 0) for amount in amounts)
        high_confidence = sum(1 for amount in amounts if amount.get('confidence', 0) >= 0.7)
        
        return {
            'total_count': len(amounts),
            'total_amount': total_amount,
            'total_vat': total_vat,
            'high_confidence': high_confidence,
            'extraction_rate': high_confidence / len(amounts) if amounts else 0.0
        }

# 테스트용 함수
def test_amount_extractor():
    """AmountExtractor 테스트"""
    extractor = AmountExtractor()
    
    # 테스트 데이터
    test_data = {
        '가맹점명': ['신전떡볶이', '맘스터치', '피자헛'],
        '요금합계': ['50,000원', '75,000원', '60,000원'],
        '부가세': ['5,000원', '7,500원', '6,000원'],
        '배달요금': [50000, 75000, 60000],
        'VAT': [5000, 7500, 6000]
    }
    
    df = pd.DataFrame(test_data)
    
    # 파싱 결과 시뮬레이션
    parsed_data = {
        'parsing_status': 'success',
        'raw_data': df
    }
    
    # 금액 정보 추출
    amounts = extractor.extract_amounts(parsed_data)
    
    print("추출된 금액 정보:")
    for i, amount in enumerate(amounts, 1):
        print(f"{i}. {amount}")
    
    # 추출 결과 요약
    summary = extractor.get_amount_summary(amounts)
    print(f"\n금액 추출 결과 요약: {summary}")

if __name__ == "__main__":
    test_amount_extractor()


