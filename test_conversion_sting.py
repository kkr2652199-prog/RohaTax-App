"""
함정 수사 작전: sample_invoice2.xlsx 파일로 변환 프로세스 테스트
"""
import requests
import os
import sys
import traceback

# 테스트 파일 경로
test_file_path = os.path.join(os.path.dirname(__file__), 'tests', 'input', 'sample_invoice2.xlsx')

if not os.path.exists(test_file_path):
    print(f"[ERROR] 테스트 파일을 찾을 수 없습니다: {test_file_path}")
    sys.exit(1)

print(f"[OK] 테스트 파일 확인: {test_file_path}")

# 세션 생성 (쿠키 유지)
session = requests.Session()

# 1. 먼저 로그인 페이지에 접속하여 세션 확인
try:
    print("\n[1단계] 세션 확인 중...")
    response = session.get('http://localhost:5001/conversion')
    print(f"   상태 코드: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   [WARNING] 예상치 못한 상태 코드")
    
    # 2. 파일 업로드 및 변환 시작
    print("\n[2단계] 파일 업로드 및 변환 시작...")
    
    with open(test_file_path, 'rb') as f:
        files = {
            'file': ('sample_invoice2.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        data = {
            'template_id': 'hometax_official',
            'issue_date': '2025-01-20',
            'file_name': '세금계산서_20250120.xlsx',
            'industry_type': 'delivery'
        }
        
        print(f"   파일: {test_file_path}")
        print(f"   템플릿 ID: {data['template_id']}")
        print(f"   발행일자: {data['issue_date']}")
        print(f"   업종: {data['industry_type']}")
        
        response = session.post(
            'http://localhost:5001/api/convert/start',
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"\n[3단계] 응답 수신")
        print(f"   상태 코드: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # 응답 내용 확인
        try:
            if 'application/json' in response.headers.get('Content-Type', ''):
                result = response.json()
                print(f"\n   JSON 응답:")
                print(f"   {result}")
            else:
                print(f"\n   텍스트 응답 (처음 500자):")
                print(f"   {response.text[:500]}")
        except Exception as e:
            print(f"\n   응답 파싱 오류: {e}")
            print(f"   원본 응답 (처음 1000자):")
            print(f"   {response.text[:1000]}")
            
except requests.exceptions.RequestException as e:
    print(f"\n[ERROR] 네트워크 오류 발생:")
    print(f"   {str(e)}")
    print(f"\n   Traceback:")
    traceback.print_exc()
except Exception as e:
    print(f"\n[ERROR] 예상치 못한 오류 발생:")
    print(f"   {str(e)}")
    print(f"\n   Traceback:")
    traceback.print_exc()

print("\n" + "="*80)
print("함정 수사 작전 완료 - 서버 터미널 로그를 확인하세요")
print("="*80)

