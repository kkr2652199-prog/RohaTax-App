"""
개별 필드 추출 기능 모듈

공급받는자 정보의 각 필드를 추출하는 기능을 제공합니다.
- 사업자등록번호
- 상호명
- 대표자명
- 주소
- 이메일
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FieldExtractors:
    """개별 필드 추출기"""
    
    def __init__(self):
        self.logger = logger
        
        # 기본 키워드들
        self.city_keywords = [
            "서울특별시", "서울시", "부산광역시", "부산시", "대구광역시", "대구시",
            "인천광역시", "인천시", "광주광역시", "광주시", "대전광역시", "대전시",
            "울산광역시", "울산시", "세종특별자치시", "세종시", "경기도", "강원도",
            "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도",
            "제주특별자치도", "제주도", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종"
        ]
        
        self.email_domains = [
            "naver.com", "daum.net", "gmail.com", "nate.com", "yahoo.com", 
            "hotmail.com", "outlook.com", "hanmail.net", "kakao.com", "tistory.com",
            "live.com", "msn.com", "icloud.com", "me.com", "mac.com", "aol.com", 
            "zoho.com", "protonmail.com"
        ]
        
        self.korean_names = [
            "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신",
            "권", "황", "안", "송", "전", "고", "문", "양", "손", "배", "조", "백", "허", "유",
            "남", "심", "노", "정", "하", "곽", "성", "차", "주", "우", "구", "신", "원", "태",
            "나", "전", "민", "유", "진", "지", "엄", "채", "천", "양", "공", "현", "방", "변",
            "여", "추", "노", "도", "소"
        ]
        
        self.foreign_names = [
            "John", "David", "Michael", "James", "Robert", "William", "Richard", "Charles",
            "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
            "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald",
            "Jason", "Edward", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas"
        ]

    def get_synonyms(self, field: str) -> List[str]:
        """필드별 동의어 반환"""
        synonyms_map = {
            '사업자등록번호': ['사업자', '등록번호', '사업자번호', '사업자등록번호', '사업자등록', '사업자번호', '사업자등록번호'],
            '상호': ['상호', '가맹점', '매장', '점포', '업체', '업체명', '가게명', '상호명'],
            '대표자명': ['대표자', '대표', '성명', '이름', '대표자명', '대표자성명'],
            '사업장주소': ['주소', '소재지', '사업장', '사업장주소', '주소지', '소재지주소'],
            '이메일': ['이메일', 'email', '메일', '이메일주소', '메일주소']
        }
        return synonyms_map.get(field, [])

    def extract_business_number(self, text: str) -> str:
        """사업자등록번호 추출 (숫자만 10자리) - 완전 정규화"""
        if not text:
            return ""
        
        # 모든 숫자를 추출해서 연결
        numbers_only = re.sub(r'[^0-9]', '', str(text))
        
        # 10자리 숫자인지 확인
        if len(numbers_only) == 10 and numbers_only.isdigit():
            self.logger.debug(f"✅ 사업자번호 정규화 완료: '{text}' → '{numbers_only}'")
            return numbers_only
        
        # 기존 패턴들도 지원 (하위 호환성)
        # 하이픈 포함 패턴: 212-12-99909, 213-12-99908
        pattern_with_hyphen = r'\d{3}-?\d{2}-?\d{5}'
        match = re.search(pattern_with_hyphen, text)
        if match:
            # 모든 비숫자 문자 제거
            digits = re.sub(r'[^0-9]', '', match.group())
            if len(digits) == 10:
                return digits
        
        # 하이픈 없이 10자레 숫자 패턴
        pattern_without_hyphen = r'\d{10}'
        match = re.search(pattern_without_hyphen, text)
        if match:
            return match.group()
        
        self.logger.debug(f"사업자번호 정규화 실패: '{text}' → 숫자만 '{numbers_only}' ({len(numbers_only)}자리)")
        self.logger.warning(f"⚠️ 사업자번호 형식 오류: '{text}' - 표준 10자리 숫자가 아닙니다")
        return ""

    def extract_store_name(self, text: str, row: pd.Series, store_keywords: List[str] = None) -> str:
        """상호명 추출 (가맹점, 업체명, 가게명 등)"""
        if store_keywords is None:
            store_keywords = []
            
        # 키워드 기반 추출
        for keyword in store_keywords:
            if keyword in text:
                # 키워드 다음에 오는 텍스트 추출
                pattern = f"{keyword}[:\\s]*([가-힣a-zA-Z0-9\\s]+)"
                match = re.search(pattern, text)
                if match:
                    store_name = match.group(1).strip()
                    if len(store_name) > 1:  # 최소 2글자 이상
                        return store_name
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            if any(keyword in str(col_name) for keyword in store_keywords):
                value = str(row[col_name]).strip()
                if value and value != 'nan' and len(value) > 1:
                    return value
        
        return ""

    def extract_representative(self, text: str, row: pd.Series) -> str:
        """대표자명 추출 (한글/영문)"""
        # 한글 이름 패턴
        korean_pattern = r'([가-힣]{2,4})'
        matches = re.findall(korean_pattern, text)
        
        for match in matches:
            # 한국 성씨 확인
            if match[0] in self.korean_names:
                return match
        
        # 영문 이름 패턴
        english_pattern = r'\b([A-Z][a-z]+)\b'
        matches = re.findall(english_pattern, text)
        
        for match in matches:
            if match in self.foreign_names:
                return match
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            if any(keyword in str(col_name) for keyword in ["대표", "성명", "이름", "사업자명"]):
                value = str(row[col_name]).strip()
                if value and value != 'nan':
                    return value
        
        return ""

    def extract_address(self, text: str, row: pd.Series) -> str:
        """사업장 주소 추출 (도로명/지번)"""
        # 도시명 기반 주소 추출
        for city in self.city_keywords:
            if city in text:
                # 도시명 다음에 오는 주소 추출
                pattern = f"{city}[가-힣\\s\\d-]+"
                match = re.search(pattern, text)
                if match:
                    address = match.group().strip()
                    if len(address) > len(city) + 2:  # 도시명보다 충분히 긴 주소
                        return address
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            clean_col_name = str(col_name).replace('\n', ' ').strip()
            address_keywords = ["공급받는자 사업장주소", "사업장주소", "공급받는자 주소", "주소", "소재지", "사업장", "주소지"]
            
            if any(keyword in clean_col_name for keyword in address_keywords):
                value = str(row[col_name]).strip()
                if value and value != 'nan' and value.lower() != 'none' and len(value) > 5:
                    self.logger.debug(f"✅ 주소 데이터 발견: 컬럼 '{clean_col_name}' → '{value}'")
                    return value
                else:
                    self.logger.debug(f"⚠️ 주소 컬럼 발견했지만 유효하지 않은 값: '{clean_col_name}' → '{value}'")
        
        return ""

    def extract_email(self, text: str, row: pd.Series) -> str:
        """이메일 추출 (한국 주요 도메인)"""
        # 이메일 패턴
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        for match in matches:
            domain = match.split('@')[1].lower()
            if domain in self.email_domains:
                return match
        
        # 컬럼명 기반 추출
        for col_name in row.index:
            if any(keyword in str(col_name) for keyword in ["이메일", "email", "메일"]):
                value = str(row[col_name]).strip()
                if value and value != 'nan' and '@' in value:
                    return value
        
        return ""

    def extract_amount(self, value) -> int:
        """금액 추출 (정수만 반환하여 과학표기법 방지)"""
        try:
            if pd.isna(value):
                return 0
            value_str = str(value)
            
            # 회계표기와 공백/단위 제거
            value_str = value_str.replace(',', '').replace('원', '').replace(' ', '')
            
            # 과학표기 방지: 과학표기가 포함된 경우 직접 정수 변환
            if 'e' in value_str.lower() or 'E' in value_str:
                try:
                    num_float = float(value_str)
                    return int(round(num_float))
                except Exception:
                    pass
            
            # 숫자만 추출
            import re
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                try:
                    # 정량이 큰 수의 경우 과학표기법 방지를 위해 문자열로 처리
                    num_str = numbers[0]
                    if '.' in num_str:
                        return int(float(num_str))
                    else:
                        # 큰 정수의 경우 직접 정수 변환
                        return int(num_str)
                except Exception:
                    return 0
            return 0
        except:
            return 0

    def _is_valid_email_format(self, email: str) -> bool:
        """간단한 이메일 형식 검증"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def auto_correct_email(self, email: str) -> str:
        """이메일 자동 수정 및 검증 (@ 기호 누락, 도메인 오류 자동 수정)"""
        try:
            email_str = str(email).strip()
            
            if not email_str or email_str == 'nan' or email_str == '':
                return None
            original_email = email_str
            
            # @ 기호가 없는 경우 처리
            if '@' not in email_str:
                wrong_separators = ['$', '#', '!', '/', '\\', '|', ':', ';', ' ']
                found_separator = False
                for sep in wrong_separators:
                    if sep in email_str:
                        email_str = email_str.replace(sep, '@', 1)
                        found_separator = True
                        self.logger.debug(f"지능앱 이메일 수정: 잘못된 구분자 '{sep}'를 '@'로 변경")
                        break
                
                if not found_separator:
                    if 'naver' in email_str.lower():
                        email_str = email_str.replace('naver', '@naver', 1)
                        self.logger.debug(f"지능앱 이메일 수정: 'naver'를 '@naver'로 변경")
                    elif 'gmail' in email_str:
                        email_str = email_str.replace('gmail', '@gmail', 1)
                        self.logger.debug(f"지능앱 이메일 수정: 'gmail'를 '@gmail'로 변경")
                    elif 'daum' in email_str:
                        email_str = email_str.replace('daum', '@daum', 1)
                        self.logger.debug(f"지능앱 이메일 수정: 'daum'를 '@daum'로 변경")
                    elif 'hanmail' in email_str:
                        email_str = email_str.replace('hanmail', '@hanmail', 1)
                        self.logger.debug(f"지능앱 이메일 수정: 'hanmail'를 '@hanmail'로 변경")
                    else:
                        email_str = email_str + '@naver.com'
                        self.logger.debug(f"지능앱 이메일 수정: 기본 도메인 '@naver.com' 추가")
            
            # 도메인 부분 정리
            if '@' in email_str:
                parts = email_str.split('@')
                if len(parts) == 2:
                    domain = parts[1]
                    wrong_domain_chars = [',', '(', ')', '[', ']', '{', '}', ' ', '$', '#', '!', '/', '\\', '|', ':', ';']
                    for char in wrong_domain_chars:
                        if char in domain:
                            domain = domain.replace(char, '.')
                            self.logger.debug(f"지능앱 이메일 수정: 도메인에서 잘못된 문자 '{char}'를 '.'로 변경")
                    email_str = parts[0] + '@' + domain
            
            # 중복된 마침표 제거
            if '@' in email_str:
                parts = email_str.split('@')
                if len(parts) == 2:
                    domain = parts[1]
                    while '..' in domain:
                        domain = domain.replace('..', '.')
                        self.logger.debug(f"지능앱 이메일 수정: 중복된 마침표 제거")
                    email_str = parts[0] + '@' + domain
            
            # 최종 검증
            if '@' in email_str and '.' in email_str:
                if original_email != email_str:
                    self.logger.info(f"지능앱 이메일 수정 완료: '{original_email}' → '{email_str}'")
                return email_str
            else:
                self.logger.warning(f"지능앱 이메일 수정 실패: '{original_email}' → '{email_str}' (유효하지 않은 형식)")
                return None
                
        except Exception as e:
            self.logger.error(f"지능앱 이메일 수정 오류: {str(e)}")
            return None
