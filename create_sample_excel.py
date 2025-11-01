import pandas as pd
import os

# 샘플 데이터 생성
data = {
    '공급자사업자번호': ['123-45-67890', '234-56-78901', '345-67-89012'],
    '공급받는자사업자번호': ['111-11-11111', '222-22-22222', '333-33-33333'],
    '공급자명': ['로하테크', '테스트회사1', '테스트회사2'],
    '공급받는자명': ['고객사1', '고객사2', '고객사3'],
    '공급가액': [100000, 200000, 300000],
    '세액': [10000, 20000, 30000],
    '작성일자': ['2024-01-15', '2024-01-16', '2024-01-17']
}

# DataFrame 생성
df = pd.DataFrame(data)

# 엑셀 파일로 저장
output_path = 'static/videos/sample_conversion_data.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"샘플 엑셀 파일이 생성되었습니다: {output_path}")
print(f"파일 크기: {os.path.getsize(output_path)} bytes")





