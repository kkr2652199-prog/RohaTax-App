"""
변환앱 핵심 기술 구현
- 50개 단위 파일 분할
- 전자세금일자 기입
- 절대값 규칙 적용
"""

import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any

class ConversionCore:
    """변환앱 핵심 기술 클래스"""
    
    def __init__(self):
        self.MAX_PER_FILE = 50  # 절대 규칙: 50개 = 1개 파일
        self.START_ROW = 7       # 절대 규칙: 7행부터 시작
        self.END_ROW = 56       # 절대 규칙: 56행까지 (50개)
        
        # 절대값 규칙
        self.ABSOLUTE_VALUES = {
            'A': '01',    # 전자세금계산서 종류
            'W': '30',    # 절대값
            'BG': '01'    # 절대값
        }
        
        # 공급자 정보 기입 규칙
        self.SUPPLIER_INFO_COLS = {
            'H': 'supplier_business_type',    # 공급자 업태
            'I': 'supplier_business_category' # 공급자 종목
        }
    
    def calculate_file_count(self, total_suppliers: int) -> int:
        """
        50개 단위 분할 계산
        - 50개 = 1개 파일
        - 51개 = 2개 파일
        - 400개 = 8개 파일
        """
        if total_suppliers <= 0:
            return 0
        
        # 50개 단위로 나누고, 나머지가 있으면 +1
        file_count = (total_suppliers - 1) // self.MAX_PER_FILE + 1
        return file_count
    
    def get_supplier_range(self, file_index: int) -> tuple:
        """
        특정 파일의 공급받는자 범위 계산 (0-based 인덱싱)
        - 1번째 파일: 0~49번째 (50개)
        - 2번째 파일: 50~99번째 (50개)
        - 3번째 파일: 100~149번째 (50개)
        """
        start_idx = file_index * self.MAX_PER_FILE
        end_idx = start_idx + self.MAX_PER_FILE
        
        return start_idx, end_idx
    
    def apply_tax_date_rule(self, df: pd.DataFrame, tax_date: str) -> pd.DataFrame:
        """
        전자세금일자 기입 규칙 적용
        - B6: 제목 (작성일자)
        - B7~B56: 유저 지정 전자세금일자 (형식: 20251001)
        """
        # B6에 제목 기입
        df.loc[6, 'B'] = '작성일자'
        
        # B7~B56에 전자세금일자 기입 (8자리 형식: 20251001)
        for row in range(self.START_ROW, self.END_ROW + 1):
            df.loc[row, 'B'] = tax_date
        
        return df
    
    def apply_absolute_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        절대값 규칙 적용
        - A열 7행: 01
        - W열 7행: 30
        - BG열 7행: 01
        """
        start_row = self.START_ROW
        
        # A열 절대값
        df.loc[start_row, 'A'] = self.ABSOLUTE_VALUES['A']
        
        # W열 절대값
        df.loc[start_row, 'W'] = self.ABSOLUTE_VALUES['W']
        
        # BG열 절대값
        df.loc[start_row, 'BG'] = self.ABSOLUTE_VALUES['BG']
        
        return df
    
    def apply_supplier_info(self, df: pd.DataFrame, supplier_info: Dict[str, str]) -> pd.DataFrame:
        """
        공급자 정보 기입 규칙 적용 (절대지침)
        - H열 7행: 공급자 업태
        - I열 7행: 공급자 종목
        """
        start_row = self.START_ROW
        
        # 공급자 업태 기입 (H열 7행)
        if 'supplier_business_type' in supplier_info and supplier_info['supplier_business_type']:
            df.loc[start_row, 'H'] = supplier_info['supplier_business_type'].strip()
        
        # 공급자 종목 기입 (I열 7행)
        if 'supplier_business_category' in supplier_info and supplier_info['supplier_business_category']:
            df.loc[start_row, 'I'] = supplier_info['supplier_business_category'].strip()
        
        return df
    
    def fill_supplier_data(self, df: pd.DataFrame, suppliers: List[Dict], 
                          file_index: int) -> pd.DataFrame:
        """
        공급받는자 데이터 기입
        - 7행부터 시작 (1번째)
        - 56행까지 (50번째)
        """
        start_idx, end_idx = self.get_supplier_range(file_index)
        
        # 해당 파일의 공급받는자 데이터만 추출
        file_suppliers = suppliers[start_idx:end_idx]
        
        # 7행부터 데이터 기입
        for i, supplier in enumerate(file_suppliers):
            row = self.START_ROW + i
            
            # 공급받는자 정보 기입 (예시)
            df.loc[row, 'E'] = supplier.get('company_name', '')
            df.loc[row, 'F'] = supplier.get('representative_name', '')
            df.loc[row, 'G'] = supplier.get('address', '')
            df.loc[row, 'J'] = supplier.get('email', '')
        
        return df
    
    def create_conversion_file(self, suppliers: List[Dict], tax_date: str, 
                             file_index: int, supplier_info: Dict[str, str] = None) -> pd.DataFrame:
        """
        변환 파일 생성
        - 전자세금일자 규칙 적용
        - 절대값 규칙 적용
        - 공급자 정보 기입 (업태/종목) - 절대지침
        - 공급받는자 데이터 기입
        """
        # 빈 DataFrame 생성 (예시: 100행 x 30열)
        df = pd.DataFrame(index=range(1, 101), 
                         columns=[chr(i) for i in range(65, 95)])  # A~BG열
        
        # 전자세금일자 규칙 적용
        df = self.apply_tax_date_rule(df, tax_date)
        
        # 절대값 규칙 적용
        df = self.apply_absolute_values(df)
        
        # 공급자 정보 기입 (업태/종목) - 절대지침
        if supplier_info:
            df = self.apply_supplier_info(df, supplier_info)
        
        # 공급받는자 데이터 기입
        df = self.fill_supplier_data(df, suppliers, file_index)
        
        return df
    
    def process_conversion(self, suppliers: List[Dict], tax_date: str, 
                          supplier_info: Dict[str, str] = None) -> List[pd.DataFrame]:
        """
        전체 변환 프로세스
        - 파일 개수 계산
        - 각 파일별로 변환 수행
        - 공급자 정보 포함
        """
        total_suppliers = len(suppliers)
        file_count = self.calculate_file_count(total_suppliers)
        
        print(f"📊 총 공급받는자: {total_suppliers}개")
        print(f"📁 생성할 파일 수: {file_count}개")
        
        conversion_files = []
        
        for file_index in range(file_count):
            print(f"🔄 {file_index + 1}번째 파일 생성 중...")
            
            # 변환 파일 생성 (공급자 정보 포함)
            df = self.create_conversion_file(suppliers, tax_date, file_index, supplier_info)
            conversion_files.append(df)
        
        return conversion_files
    
    def save_conversion_files(self, conversion_files: List[pd.DataFrame], 
                            output_dir: str = "output") -> List[str]:
        """
        변환 파일들을 Excel로 저장
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        
        for i, df in enumerate(conversion_files):
            filename = f"세금계산서_{i+1}번째.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            df.to_excel(filepath, index=False)
            saved_files.append(filepath)
            
            print(f"✅ {filename} 저장 완료")
        
        return saved_files


# 사용 예시
if __name__ == "__main__":
    # 변환앱 핵심 기술 테스트
    converter = ConversionCore()
    
    # 테스트 데이터 (400개 공급받는자)
    test_suppliers = []
    for i in range(400):
        test_suppliers.append({
            'company_name': f'테스트회사{i+1}',
            'representative_name': f'대표자{i+1}',
            'address': f'주소{i+1}',
            'email': f'test{i+1}@example.com'
        })
    
    # 전자세금일자 (새로운 형식: 6자리)
    tax_date = "251001"  # 25년10월01일
    
    # 변환 프로세스 실행
    conversion_files = converter.process_conversion(test_suppliers, tax_date)
    
    # 파일 저장
    saved_files = converter.save_conversion_files(conversion_files)
    
    print(f"\n🎉 변환 완료! {len(saved_files)}개 파일 생성")
    print("📁 저장된 파일들:")
    for file in saved_files:
        print(f"  - {file}")
