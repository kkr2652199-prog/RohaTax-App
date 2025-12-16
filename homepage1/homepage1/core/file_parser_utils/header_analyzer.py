"""
헤더 분석 연동 모듈
file_parser.py의 헤더 분석 기능을 확장
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class HeaderAnalyzer:
    """헤더 분석 연동 클래스"""
    
    def __init__(self):
        """헤더 분석기 초기화"""
        self.logger = logger
        
        # 헤더 키워드 매핑
        self.header_keywords = {
            'business_number': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '공급받는자사업자', '공급받는자 사업자', '공급받는자 등록번호', '공급받는자 사업자등록번호', '공급받는자 사업자번호', '공급받는자번호',
                '구매자 등록번호', '구매자 사업자등록번호', '구매자 사업자번호', '수취인 등록번호', '수취인 사업자등록번호', '수취인 사업자번호',
                '고객 사업자등록번호', '고객 사업자번호', '거래처 등록번호', '거래처 사업자등록번호', '거래처 사업자번호',
                '매입자 등록번호', '매입자 사업자등록번호', '매입자 사업자번호',
                '법인등록번호', '법인 사업자등록번호', '법인 사업자번호',
                '업체 사업자등록번호', '업체 사업자번호', '가맹점 사업자등록번호', '가맹점 사업자번호',
                '매장 사업자등록번호', '매장 사업자번호', '점포 사업자등록번호', '점포 사업자번호', '업소 사업자등록번호', '업소 사업자번호'
            ],
            'store_name': [
                '상호명', '상호', '업체명', '가맹점명', '매장명', '점포명', '업소명',
                '공급받는자명', '공급받는자 상호', '공급받는자 업체명', '공급받는자 가맹점명',
                '구매자명', '구매자 상호', '구매자 업체명', '구매자 가맹점명',
                '수취인명', '수취인 상호', '수취인 업체명', '수취인 가맹점명',
                '고객명', '고객 상호', '고객 업체명', '고객 가맹점명',
                '거래처명', '거래처 상호', '거래처 업체명', '거래처 가맹점명',
                '매입자명', '매입자 상호', '매입자 업체명', '매입자 가맹점명',
                '법인명', '법인 상호', '법인 업체명', '법인 가맹점명',
                '업체명', '업체 상호', '업체 업체명', '업체 가맹점명',
                '가맹점명', '가맹점 상호', '가맹점 업체명', '가맹점 가맹점명',
                '매장명', '매장 상호', '매장 업체명', '매장 가맹점명',
                '점포명', '점포 상호', '점포 업체명', '점포 가맹점명',
                '업소명', '업소 상호', '업소 업체명', '업소 가맹점명'
            ],
            'representative_name': [
                '대표자명', '대표자', '대표', '사장', '원장', '원장님', '사장님', '대표님',
                '대표자성명', '대표자 성명', '대표자이름', '대표자 이름', '대표이름', '대표 이름',
                '대표자성함', '대표자 성함', '대표성명', '대표 성명', '대표성함', '대표 성함',
                '대표자님', '대표자님성명', '대표님성명', '대표자님성함', '대표님성함',
                '사장성명', '사장 성명', '사장이름', '사장 이름', '사장성함', '사장 성함', '사장님성명', '사장님성함',
                '공급받는자 대표자', '공급받는자 대표', '공급받는자 사장', '공급받는자 원장',
                '공급받는자성명', '공급받는자 성명', '공급받는자이름', '공급받는자 이름', '공급받는자성함', '공급받는자 성함',
                '구매자 대표자', '구매자 대표', '구매자 사장', '구매자 원장',
                '수취인 대표자', '수취인 대표', '수취인 사장', '수취인 원장',
                '고객 대표자', '고객 대표', '고객 사장', '고객 원장',
                '거래처 대표자', '거래처 대표', '거래처 사장', '거래처 원장',
                '매입자 대표자', '매입자 대표', '매입자 사장', '매입자 원장',
                '법인 대표자', '법인 대표', '법인 사장', '법인 원장',
                '업체 대표자', '업체 대표', '업체 사장', '업체 원장', '업체대표', '업체 대표', '업체대표명', '업체 대표명', '업체대표님', '업체 대표님',
                '가맹점 대표자', '가맹점 대표', '가맹점 사장', '가맹점 원장',
                '매장 대표자', '매장 대표', '매장 사장', '매장 원장',
                '점포 대표자', '점포 대표', '점포 사장', '점포 원장',
                '업소 대표자', '업소 대표', '업소 사장', '업소 원장'
            ],
            'address': [
                '주소', '사업장주소', '업체주소', '가맹점주소', '매장주소', '점포주소', '업소주소',
                '공급받는자 주소', '공급받는자 사업장주소', '공급받는자 업체주소', '공급받는자 가맹점주소',
                '구매자 주소', '구매자 사업장주소', '구매자 업체주소', '구매자 가맹점주소',
                '수취인 주소', '수취인 사업장주소', '수취인 업체주소', '수취인 가맹점주소',
                '고객 주소', '고객 사업장주소', '고객 업체주소', '고객 가맹점주소',
                '거래처 주소', '거래처 사업장주소', '거래처 업체주소', '거래처 가맹점주소',
                '매입자 주소', '매입자 사업장주소', '매입자 업체주소', '매입자 가맹점주소',
                '법인 주소', '법인 사업장주소', '법인 업체주소', '법인 가맹점주소',
                '업체 주소', '업체 사업장주소', '업체 업체주소', '업체 가맹점주소',
                '가맹점 주소', '가맹점 사업장주소', '가맹점 업체주소', '가맹점 가맹점주소',
                '매장 주소', '매장 사업장주소', '매장 업체주소', '매장 가맹점주소',
                '점포 주소', '점포 사업장주소', '점포 업체주소', '점포 가맹점주소',
                '업소 주소', '업소 사업장주소', '업소 업체주소', '업소 가맹점주소'
            ],
            'phone': [
                '전화번호', '휴대폰번호', '핸드폰번호', '연락처', '연락번호', '전화', '휴대폰', '핸드폰',
                '공급받는자 전화번호', '공급받는자 휴대폰번호', '공급받는자 핸드폰번호', '공급받는자 연락처',
                '구매자 전화번호', '구매자 휴대폰번호', '구매자 핸드폰번호', '구매자 연락처',
                '수취인 전화번호', '수취인 휴대폰번호', '수취인 핸드폰번호', '수취인 연락처',
                '고객 전화번호', '고객 휴대폰번호', '고객 핸드폰번호', '고객 연락처',
                '거래처 전화번호', '거래처 휴대폰번호', '거래처 핸드폰번호', '거래처 연락처',
                '매입자 전화번호', '매입자 휴대폰번호', '매입자 핸드폰번호', '매입자 연락처',
                '법인 전화번호', '법인 휴대폰번호', '법인 핸드폰번호', '법인 연락처',
                '업체 전화번호', '업체 휴대폰번호', '업체 핸드폰번호', '업체 연락처',
                '가맹점 전화번호', '가맹점 휴대폰번호', '가맹점 핸드폰번호', '가맹점 연락처',
                '매장 전화번호', '매장 휴대폰번호', '매장 핸드폰번호', '매장 연락처',
                '점포 전화번호', '점포 휴대폰번호', '점포 핸드폰번호', '점포 연락처',
                '업소 전화번호', '업소 휴대폰번호', '업소 핸드폰번호', '업소 연락처'
            ],
            'email': [
                '이메일', '메일', 'email', 'mail', '이메일주소', '메일주소',
                '공급받는자 이메일', '공급받는자 메일', '공급받는자 email', '공급받는자 mail',
                '구매자 이메일', '구매자 메일', '구매자 email', '구매자 mail',
                '수취인 이메일', '수취인 메일', '수취인 email', '수취인 mail',
                '고객 이메일', '고객 메일', '고객 email', '고객 mail',
                '거래처 이메일', '거래처 메일', '거래처 email', '거래처 mail',
                '매입자 이메일', '매입자 메일', '매입자 email', '매입자 mail',
                '법인 이메일', '법인 메일', '법인 email', '법인 mail',
                '업체 이메일', '업체 메일', '업체 email', '업체 mail',
                '가맹점 이메일', '가맹점 메일', '가맹점 email', '가맹점 mail',
                '매장 이메일', '매장 메일', '매장 email', '매장 mail',
                '점포 이메일', '점포 메일', '점포 email', '점포 mail',
                '업소 이메일', '업소 메일', '업소 email', '업소 mail'
            ]
        }
    
    def analyze_headers(self, headers: List[str]) -> Dict[str, Any]:
        """
        헤더 분석 및 매핑
        
        Args:
            headers: 헤더 리스트
            
        Returns:
            Dict: 헤더 분석 결과
        """
        try:
            analysis_result = {
                'original_headers': headers,
                'mapped_headers': {},
                'unmapped_headers': [],
                'confidence_scores': {},
                'analysis_summary': {}
            }
            
            # 각 헤더에 대해 매핑 시도
            for header in headers:
                mapping_result = self._map_header(header)
                if mapping_result['mapped']:
                    analysis_result['mapped_headers'][header] = mapping_result
                    analysis_result['confidence_scores'][header] = mapping_result['confidence']
                else:
                    analysis_result['unmapped_headers'].append(header)
            
            # 분석 요약 생성
            analysis_result['analysis_summary'] = self._generate_analysis_summary(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"헤더 분석 오류: {str(e)}")
            return {'error': str(e)}
    
    def _map_header(self, header: str) -> Dict[str, Any]:
        """개별 헤더 매핑"""
        try:
            header_lower = header.lower().strip()
            
            # 각 필드 타입에 대해 매칭 시도
            for field_type, keywords in self.header_keywords.items():
                for keyword in keywords:
                    keyword_lower = keyword.lower().strip()
                    
                    # 정확한 매칭
                    if keyword_lower == header_lower:
                        return {
                            'mapped': True,
                            'field_type': field_type,
                            'confidence': 1.0,
                            'match_type': 'exact',
                            'keyword': keyword
                        }
                    
                    # 부분 매칭
                    if keyword_lower in header_lower or header_lower in keyword_lower:
                        confidence = self._calculate_confidence(header_lower, keyword_lower)
                        if confidence > 0.5:  # 임계값 이상일 때만 매핑
                            return {
                                'mapped': True,
                                'field_type': field_type,
                                'confidence': confidence,
                                'match_type': 'partial',
                                'keyword': keyword
                            }
            
            return {'mapped': False, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.error(f"헤더 매핑 오류: {str(e)}")
            return {'mapped': False, 'confidence': 0.0, 'error': str(e)}
    
    def _calculate_confidence(self, header: str, keyword: str) -> float:
        """매칭 신뢰도 계산"""
        try:
            # 길이 기반 신뢰도
            length_ratio = min(len(header), len(keyword)) / max(len(header), len(keyword))
            
            # 공통 문자 기반 신뢰도
            common_chars = set(header) & set(keyword)
            char_ratio = len(common_chars) / max(len(set(header)), len(set(keyword)))
            
            # 종합 신뢰도
            confidence = (length_ratio * 0.4) + (char_ratio * 0.6)
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.0
    
    def _generate_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 요약 생성"""
        try:
            total_headers = len(analysis_result['original_headers'])
            mapped_count = len(analysis_result['mapped_headers'])
            unmapped_count = len(analysis_result['unmapped_headers'])
            
            summary = {
                'total_headers': total_headers,
                'mapped_headers': mapped_count,
                'unmapped_headers': unmapped_count,
                'mapping_rate': mapped_count / total_headers if total_headers > 0 else 0,
                'average_confidence': sum(analysis_result['confidence_scores'].values()) / mapped_count if mapped_count > 0 else 0,
                'field_types_found': list(set([mapping['field_type'] for mapping in analysis_result['mapped_headers'].values()]))
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"요약 생성 오류: {str(e)}")
            return {'error': str(e)}


