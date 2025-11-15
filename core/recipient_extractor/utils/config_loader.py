"""설정 및 키워드 로더 전담 모듈."""

from typing import Dict, List


def load_keywords() -> Dict[str, List[str]]:
    """키워드 리스트를 딕셔너리 형태로 반환한다."""
    return {
        'store': [
            '가맹점', '상호', '매장', '점포', '상점', '업체', '사업체', '매장명', '점포명', '상호명', '업소명', 
            '사업장명', '가게', '가게명', '업소', '사업장', '점', '상점명', '가맹점명', '업체명', '사업체명'
        ],
        'korean_cities': [
            '서울특별시', '서울시', '부산광역시', '부산시', '대구광역시', '대구시', '인천광역시', '인천시', 
            '광주광역시', '광주시', '대전광역시', '대전시', '울산광역시', '울산시', '세종특별자치시', '세종시', 
            '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', 
            '제주특별자치도', '제주도', '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종'
        ],
        'email_domains': [
            'naver.com', 'daum.net', 'gmail.com', 'nate.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'hanmail.net', 'kakao.com', 'tistory.com', 'live.com', 'msn.com', 'icloud.com', 'me.com', 
            'mac.com', 'aol.com', 'zoho.com', 'protonmail.com'
        ],
        'korean_surnames': [
            '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전', '고', 
            '문', '양', '손', '배', '조', '백', '허', '유', '남', '심', '노', '정', '하', '곽', '성', '차', '주', '우', '구', '신', 
            '원', '태', '나', '전', '민', '유', '진', '지', '엄', '채', '천', '양', '공', '현', '방', '변', '여', '추', '노', '도', '소'
        ],
        'foreign_names': [
            'John', 'David', 'Michael', 'James', 'Robert', 'William', 'Richard', 'Charles', 'Thomas', 'Christopher', 
            'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 
            'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas'
        ],
    }


def load_config() -> Dict[str, List[str]]:
    """설정값을 딕셔너리 형태로 반환한다."""
    return {
        'required_columns': ['사업자등록번호', '상호', '대표명', '사업장주소', '사업자이메일'],
        'amount_columns': ['공급가액', '부가세', '요금합계'],
    }

