"""
마이그레이션 실행 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import importlib.util
spec = importlib.util.spec_from_file_location("create_activity_logs_model", Path(__file__).parent / "database" / "migrations" / "create_activity_logs_model.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
create_activity_logs_table = module.create_activity_logs_table
verify_table_structure = module.verify_table_structure

if __name__ == '__main__':
    print("=" * 80)
    print("활동 로그 테이블 생성 마이그레이션")
    print("=" * 80)
    print("\n[진행] 마이그레이션 실행 중...")
    
    if create_activity_logs_table():
        print("\n[검증] 테이블 구조 검증 중...")
        verify_table_structure()
        print("\n[완료] 마이그레이션 완료!")
    else:
        print("\n[실패] 마이그레이션 실패!")

