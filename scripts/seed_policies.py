"""
비즈니스 라운지 지원사업 초기 데이터 삽입 스크립트
4가지 카테고리: BIZ(사업자), STARTUP(예비창업), YOUTH(청년/학생), WELFARE(임산부/복지)
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_conn_optimized


def seed_policies():
    """지원사업 초기 데이터 삽입"""
    print("=" * 50)
    print("비즈니스 라운지 지원사업 초기 데이터 삽입 시작")
    print("=" * 50)
    
    try:
        with get_conn_optimized() as conn:
            conn.row_factory = sqlite3.Row
            
            # 기존 데이터 삭제
            print("\n[1단계] 기존 지원사업 데이터 삭제 중...")
            conn.execute("DELETE FROM policies")
            conn.commit()
            print("기존 데이터 삭제 완료")
            
            # 테이블이 없으면 생성
            print("\n[2단계] policies 테이블 확인 중...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS policies (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  target_type TEXT NOT NULL,
                  title TEXT NOT NULL,
                  agency TEXT NOT NULL,
                  support_type TEXT NOT NULL,
                  amount_desc TEXT,
                  period_desc TEXT,
                  d_day INTEGER,
                  end_date TEXT,
                  detail_json TEXT,
                  link TEXT,
                  is_active INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL DEFAULT (datetime('now')),
                  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
            print("테이블 확인 완료")
            
            # 초기 데이터 삽입
            print("\n[3단계] 지원사업 데이터 삽입 중...")
            
            # 오늘 날짜 기준으로 D-Day 계산
            today = datetime.now()
            
            policies_data = [
                # BIZ (사업자) 카테고리 - 6개
                {
                    'target_type': 'BIZ',
                    'title': '2026년도 스마트상점 기술보급사업 모집 공고',
                    'agency': '중소벤처기업진흥공단',
                    'support_type': '금융',
                    'amount_desc': '최대 5억원',
                    'period_desc': '2026.01.05 ~ 자금 소진 시',
                    'd_day': 5,
                    'end_date': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '소상공인 매장의 디지털 전환을 위한 스마트 POS, 무인결제 시스템 등 기술보급 지원',
                        'rate': '연 2.5%',
                        'detail_amount': '운전자금 최대 3억원 / 시설자금 최대 5억원',
                        'interest_rate_desc': '정책자금 기준금리 + 0.5%p (변동)',
                        'repayment': '2년 거치 3년 분할상환',
                        'tags': ['#기술보급', '#스마트상점'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '대표자 신분증 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.semas.or.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 상반기 소상공인 경영안정자금 신규 모집',
                    'agency': '소상공인시장진흥공단',
                    'support_type': '금융',
                    'amount_desc': '매출액의 150% 이내',
                    'period_desc': '2026.01.10 ~ 01.25',
                    'd_day': 2,
                    'end_date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '영업손실 보전 및 자금난 해소를 위한 저금리 대출 지원 (변동금리 적용)',
                        'rate': '연 3.54%~',
                        'detail_amount': '운전자금 최대 7천만원 / 시설자금 최대 1억원',
                        'interest_rate_desc': '정책자금 기준금리 + 0.2%p (변동)',
                        'repayment': '2년 거치 3년 분할상환',
                        'tags': ['#저금리', '#경영안정'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '소상공인 확인서', '대표자 신분증 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.semas.or.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 디지털 전환 지원사업 (스마트스토어 구축)',
                    'agency': '과학기술정보통신부',
                    'support_type': '보조금',
                    'amount_desc': '최대 2천만원',
                    'period_desc': '2026.02.01 ~ 02.28',
                    'd_day': 12,
                    'end_date': (today + timedelta(days=12)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '소상공인 온라인 판매 채널 구축 및 디지털 마케팅 시스템 도입 지원',
                        'rate': '보조금 80%',
                        'detail_amount': '보조금 최대 2천만원 (자부담 20%)',
                        'interest_rate_desc': '보조금 형태 (이자 없음)',
                        'repayment': '보조금 (상환 불필요)',
                        'tags': ['#디지털', '#IT'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '사업계획서', '예산서']
                    }, ensure_ascii=False),
                    'link': 'https://www.msit.go.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '지역균형발전 특별자금 (2026년 상반기)',
                    'agency': '한국산업은행',
                    'support_type': '금융',
                    'amount_desc': '최대 10억원',
                    'period_desc': '2026.01.05 ~ 자금 소진 시',
                    'd_day': 1,
                    'end_date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '지역 중소기업 경쟁력 강화를 위한 장기 저금리 자금 지원 (최대 10년)',
                        'rate': '연 2.0%~',
                        'detail_amount': '운전자금 최대 5억원 / 시설자금 최대 10억원',
                        'interest_rate_desc': '정책자금 기준금리 + 0.3%p (변동)',
                        'repayment': '3년 거치 7년 분할상환',
                        'tags': ['#저금리', '#지역균형'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '재무제표', '대표자 신분증 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.kdb.co.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 여성기업 성장지원사업 (기술개발 및 시장진입)',
                    'agency': '여성가족부',
                    'support_type': '보조금',
                    'amount_desc': '최대 5천만원',
                    'period_desc': '2026.02.05 ~ 02.20',
                    'd_day': 15,
                    'end_date': (today + timedelta(days=15)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '여성기업 경영역량 강화 및 신시장 진입을 위한 기술개발비 및 마케팅비 지원',
                        'rate': '보조금 70%',
                        'detail_amount': '보조금 최대 5천만원 (자부담 30%)',
                        'interest_rate_desc': '보조금 형태 (이자 없음)',
                        'repayment': '보조금 (상환 불필요)',
                        'tags': ['#여성', '#성장지원'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '여성기업 확인서', '사업계획서']
                    }, ensure_ascii=False),
                    'link': 'https://www.mogef.go.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 소상공인 창업자금 지원사업',
                    'agency': '중소벤처기업부',
                    'support_type': '금융',
                    'amount_desc': '최대 3억원',
                    'period_desc': '2026.01.15 ~ 02.15',
                    'd_day': 8,
                    'end_date': (today + timedelta(days=8)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '신규 창업 소상공인을 위한 창업자금 및 운영자금 지원',
                        'rate': '연 1.8%',
                        'detail_amount': '창업자금 최대 1억원 / 운영자금 최대 3억원',
                        'interest_rate_desc': '정책자금 기준금리 + 0.0%p (고정)',
                        'repayment': '2년 거치 3년 분할상환',
                        'tags': ['#창업', '#저금리'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '창업계획서']
                    }, ensure_ascii=False),
                    'link': 'https://www.smba.go.kr'
                },
                # 정부 정책자금 3종 추가
                {
                    'target_type': 'BIZ',
                    'title': '2026년 일반 경영안정자금 신규 모집',
                    'agency': '소상공인시장진흥공단',
                    'support_type': '경영안정자금',
                    'amount_desc': '최대 7,000만원',
                    'period_desc': '2026.01.10 ~ 자금 소진 시',
                    'd_day': 7,
                    'end_date': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '6개월 이상 영업 중인 소상공인을 대상으로 한 경영안정을 위한 저금리 자금 지원',
                        'rate': '연 2.0%',
                        'detail_amount': '최대 7,000만원 (단일 한도)',
                        'interest_rate_desc': '정책자금 기준금리 + 0.0%p (고정금리)',
                        'repayment': '2년 거치 3년 분할상환',
                        'tags': ['#경영안정', '#저금리', '#고정금리'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '소상공인 확인서', '영업 6개월 이상 증빙서류', '대표자 신분증 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.semas.or.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 창업 초기자금 지원사업',
                    'agency': '중소벤처기업부',
                    'support_type': '창업자금',
                    'amount_desc': '최대 5,000만원',
                    'period_desc': '2026.01.15 ~ 02.28',
                    'd_day': 10,
                    'end_date': (today + timedelta(days=10)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '창업 1년 미만의 자영업자를 대상으로 한 창업 초기 운영자금 지원 (창업교육 수료 필수)',
                        'rate': '연 2.5% ~ 3.0%',
                        'detail_amount': '최대 5,000만원 (단일 한도)',
                        'interest_rate_desc': '정책자금 기준금리 + 0.5%p ~ 1.0%p (변동금리)',
                        'repayment': '1년 거치 2년 분할상환',
                        'tags': ['#창업', '#초기자금', '#교육필수'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '창업계획서', '창업교육 수료증명서', '창업 1년 미만 증빙서류']
                    }, ensure_ascii=False),
                    'link': 'https://www.smba.go.kr'
                },
                {
                    'target_type': 'BIZ',
                    'title': '2026년 재도전(재창업) 자금 지원사업',
                    'agency': '소상공인시장진흥공단',
                    'support_type': '재창업자금',
                    'amount_desc': '최대 3,000만원',
                    'period_desc': '2026.01.20 ~ 상시 모집',
                    'd_day': 15,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '폐업 후 재창업한 사업자를 대상으로 한 재도전을 위한 저금리 자금 지원',
                        'rate': '연 2.0% 이상',
                        'detail_amount': '최대 3,000만원 (단일 한도)',
                        'interest_rate_desc': '정책자금 기준금리 + 0.0%p 이상 (변동금리)',
                        'repayment': '1년 거치 2년 분할상환',
                        'tags': ['#재창업', '#재도전', '#저금리'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '폐업증명서', '재창업 계획서', '재창업 사업자등록증명']
                    }, ensure_ascii=False),
                    'link': 'https://www.semas.or.kr'
                },
                
                # STARTUP (예비창업) 카테고리 - 5개
                {
                    'target_type': 'STARTUP',
                    'title': '청년창업사관학교 2026년 1기 모집',
                    'agency': '중소벤처기업부',
                    'support_type': '금융',
                    'amount_desc': '최대 1억원',
                    'period_desc': '2026.01.20 ~ 02.15',
                    'd_day': 8,
                    'end_date': (today + timedelta(days=8)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '만 39세 이하 청년 창업자 대상 창업자금 및 6개월 집중 멘토링 지원',
                        'rate': '연 1.5%',
                        'detail_amount': '창업자금 최대 1억원 (단일 한도)',
                        'interest_rate_desc': '정책자금 기준금리 + 0.0%p (고정)',
                        'repayment': '3년 거치 2년 분할상환',
                        'tags': ['#청년', '#창업'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '창업계획서', '청년 확인서류']
                    }, ensure_ascii=False),
                    'link': 'https://www.smba.go.kr'
                },
                {
                    'target_type': 'STARTUP',
                    'title': '2026년 스타트업 창업 지원사업 (K-스타트업)',
                    'agency': '과학기술정보통신부',
                    'support_type': '보조금',
                    'amount_desc': '최대 5천만원',
                    'period_desc': '2026.02.01 ~ 02.28',
                    'd_day': 12,
                    'end_date': (today + timedelta(days=12)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': 'IT/기술 기반 스타트업 창업을 위한 초기 자금 및 기술개발비 지원',
                        'rate': '보조금 80%',
                        'detail_amount': '보조금 최대 5천만원 (자부담 20%)',
                        'interest_rate_desc': '보조금 형태 (이자 없음)',
                        'repayment': '보조금 (상환 불필요)',
                        'tags': ['#스타트업', '#IT'],
                        'documents': ['사업자등록증명', '국세납세증명서', '창업계획서', '기술개발계획서', '예산서']
                    }, ensure_ascii=False),
                    'link': 'https://www.msit.go.kr'
                },
                {
                    'target_type': 'STARTUP',
                    'title': '2026년 예비창업자 교육 및 컨설팅 지원',
                    'agency': '중소벤처기업진흥공단',
                    'support_type': '교육',
                    'amount_desc': '교육비 전액 지원',
                    'period_desc': '2026.01.10 ~ 상시 모집',
                    'd_day': 20,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '예비창업자를 위한 창업 교육 프로그램 및 전문가 컨설팅 지원',
                        'rate': '무료',
                        'detail_amount': '교육비 전액 지원 (교재비 별도)',
                        'interest_rate_desc': '교육 프로그램 (비용 없음)',
                        'repayment': '해당 없음',
                        'tags': ['#교육', '#컨설팅'],
                        'documents': ['신분증 사본', '창업 의지 확인서', '사업 아이디어 제안서']
                    }, ensure_ascii=False),
                    'link': 'https://www.semas.or.kr'
                },
                {
                    'target_type': 'STARTUP',
                    'title': '2026년 청년 창업자금 특별 지원',
                    'agency': '한국산업은행',
                    'support_type': '금융',
                    'amount_desc': '최대 2억원',
                    'period_desc': '2026.01.15 ~ 자금 소진 시',
                    'd_day': 10,
                    'end_date': (today + timedelta(days=10)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '만 40세 이하 청년 창업자 대상 저금리 창업자금 대출 지원',
                        'rate': '연 2.0%',
                        'detail_amount': '창업자금 최대 2억원 (단일 한도)',
                        'interest_rate_desc': '정책자금 기준금리 + 0.5%p (고정)',
                        'repayment': '2년 거치 3년 분할상환',
                        'tags': ['#청년', '#저금리'],
                        'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '창업계획서', '청년 확인서류']
                    }, ensure_ascii=False),
                    'link': 'https://www.kdb.co.kr'
                },
                {
                    'target_type': 'STARTUP',
                    'title': '2026년 사회적기업 창업 지원사업',
                    'agency': '고용노동부',
                    'support_type': '보조금',
                    'amount_desc': '최대 3천만원',
                    'period_desc': '2026.02.10 ~ 03.10',
                    'd_day': 25,
                    'end_date': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '사회적 가치 실현을 목표로 하는 사회적기업 창업을 위한 초기 자금 지원',
                        'rate': '보조금 70%',
                        'detail_amount': '보조금 최대 3천만원 (자부담 30%)',
                        'interest_rate_desc': '보조금 형태 (이자 없음)',
                        'repayment': '보조금 (상환 불필요)',
                        'tags': ['#사회적기업', '#창업'],
                        'documents': ['사업자등록증명', '국세납세증명서', '사회적기업 인증서', '사업계획서', '사회적 가치 실현 계획서']
                    }, ensure_ascii=False),
                    'link': 'https://www.moel.go.kr'
                },
                
                # YOUTH (청년/학생) 카테고리 - 5개
                {
                    'target_type': 'YOUTH',
                    'title': '2026년 국가장학금 1차 신청',
                    'agency': '한국장학재단',
                    'support_type': '장학금',
                    'amount_desc': '최대 520만원/학기',
                    'period_desc': '2026.01.05 ~ 01.31',
                    'd_day': 5,
                    'end_date': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '대학생 및 대학원생을 위한 국가장학금 신청 (소득분위별 차등 지급)',
                        'rate': '장학금 (상환 불필요)',
                        'detail_amount': '소득분위별 최대 520만원/학기',
                        'interest_rate_desc': '장학금 형태 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#장학금', '#대학생'],
                        'documents': ['재학증명서', '가족관계증명서', '소득증빙서류', '통장 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.kosaf.go.kr'
                },
                {
                    'target_type': 'YOUTH',
                    'title': '2026년 청년 취업 지원사업 (K-디지털 트레이닝)',
                    'agency': '과학기술정보통신부',
                    'support_type': '교육',
                    'amount_desc': '교육비 전액 지원 + 생활비',
                    'period_desc': '2026.01.10 ~ 상시 모집',
                    'd_day': 7,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '청년 대상 디지털 역량 강화 교육 프로그램 (AI, 빅데이터, 클라우드 등)',
                        'rate': '무료',
                        'detail_amount': '교육비 전액 지원 + 월 116만원 생활비 지급',
                        'interest_rate_desc': '교육 프로그램 (비용 없음)',
                        'repayment': '해당 없음',
                        'tags': ['#취업', '#교육'],
                        'documents': ['신분증 사본', '이력서', '학력증명서', '지원동기서']
                    }, ensure_ascii=False),
                    'link': 'https://www.msit.go.kr'
                },
                {
                    'target_type': 'YOUTH',
                    'title': '2026년 청년 내일채움공제 가입 신청',
                    'agency': '고용노동부',
                    'support_type': '복지',
                    'amount_desc': '최대 1,200만원',
                    'period_desc': '2026.01.01 ~ 상시 모집',
                    'd_day': 30,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '만 15~34세 청년 근로자 대상 저축 지원 프로그램 (국가 매칭 지원)',
                        'rate': '국가 매칭 1:1',
                        'detail_amount': '월 10만원 저축 시 국가 10만원 추가 지원 (최대 1,200만원)',
                        'interest_rate_desc': '저축 지원 프로그램',
                        'repayment': '해당 없음',
                        'tags': ['#청년', '#저축'],
                        'documents': ['신분증 사본', '근로계약서', '통장 사본', '가입신청서']
                    }, ensure_ascii=False),
                    'link': 'https://www.moel.go.kr'
                },
                {
                    'target_type': 'YOUTH',
                    'title': '2026년 청년 주거비 지원사업 (청년 주거 급여)',
                    'agency': '국토교통부',
                    'support_type': '복지',
                    'amount_desc': '월 최대 30만원',
                    'period_desc': '2026.01.05 ~ 상시 신청',
                    'd_day': 15,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '만 19~34세 무주택 청년 가구 대상 월 임대료 지원',
                        'rate': '급여 형태',
                        'detail_amount': '소득 및 자산에 따라 월 최대 30만원 지급',
                        'interest_rate_desc': '주거 급여 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#청년', '#주거'],
                        'documents': ['신분증 사본', '주민등록등본', '소득증빙서류', '임대차계약서', '통장 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.molit.go.kr'
                },
                {
                    'target_type': 'YOUTH',
                    'title': '2026년 대학생 취업 역량 강화 프로그램',
                    'agency': '교육부',
                    'support_type': '교육',
                    'amount_desc': '교육비 전액 지원',
                    'period_desc': '2026.02.01 ~ 02.28',
                    'd_day': 18,
                    'end_date': (today + timedelta(days=18)).strftime('%Y-%m-%d'),
                    'detail_json': json.dumps({
                        'description': '대학생 대상 취업 준비 교육 및 인턴십 프로그램 지원',
                        'rate': '무료',
                        'detail_amount': '교육비 전액 지원 (교재비 별도)',
                        'interest_rate_desc': '교육 프로그램 (비용 없음)',
                        'repayment': '해당 없음',
                        'tags': ['#대학생', '#취업'],
                        'documents': ['재학증명서', '성적증명서', '이력서', '지원동기서']
                    }, ensure_ascii=False),
                    'link': 'https://www.moe.go.kr'
                },
                
                # WELFARE (임산부/복지) 카테고리 - 4개
                {
                    'target_type': 'WELFARE',
                    'title': '2026년 출산 지원금 신청',
                    'agency': '보건복지부',
                    'support_type': '복지',
                    'amount_desc': '200만원 (1인당)',
                    'period_desc': '2026.01.01 ~ 상시 신청',
                    'd_day': 30,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '출산 가구 대상 출산 지원금 지급 (아기 출생 후 신청 가능)',
                        'rate': '지원금 형태',
                        'detail_amount': '아기 1인당 200만원 지급',
                        'interest_rate_desc': '출산 지원금 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#출산', '#복지'],
                        'documents': ['출생증명서', '주민등록등본', '통장 사본', '신청서']
                    }, ensure_ascii=False),
                    'link': 'https://www.mohw.go.kr'
                },
                {
                    'target_type': 'WELFARE',
                    'title': '2026년 임신·출산 진료비 지원',
                    'agency': '보건복지부',
                    'support_type': '복지',
                    'amount_desc': '최대 100만원',
                    'period_desc': '2026.01.01 ~ 상시 신청',
                    'd_day': 30,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '임신부 대상 산전·산후 진료비 지원 (건강보험 본인부담금 일부 지원)',
                        'rate': '의료비 지원',
                        'detail_amount': '산전·산후 진료비 최대 100만원 지원',
                        'interest_rate_desc': '의료비 지원 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#임신', '#의료비'],
                        'documents': ['임신 확인서', '건강보험증', '진료비 영수증', '통장 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.mohw.go.kr'
                },
                {
                    'target_type': 'WELFARE',
                    'title': '2026년 육아휴직 급여 신청',
                    'agency': '고용노동부',
                    'support_type': '복지',
                    'amount_desc': '월 최대 150만원',
                    'period_desc': '2026.01.01 ~ 상시 신청',
                    'd_day': 30,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '육아휴직 중인 근로자 대상 급여 지급 (최대 1년)',
                        'rate': '급여 형태',
                        'detail_amount': '평균임금의 80% (월 최대 150만원)',
                        'interest_rate_desc': '육아휴직 급여 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#육아', '#휴직'],
                        'documents': ['신분증 사본', '출생증명서', '근로계약서', '육아휴직 신청서', '통장 사본']
                    }, ensure_ascii=False),
                    'link': 'https://www.moel.go.kr'
                },
                {
                    'target_type': 'WELFARE',
                    'title': '2026년 아동수당 신청',
                    'agency': '보건복지부',
                    'support_type': '복지',
                    'amount_desc': '월 10만원 (만 8세 미만)',
                    'period_desc': '2026.01.01 ~ 상시 신청',
                    'd_day': 30,
                    'end_date': None,
                    'detail_json': json.dumps({
                        'description': '만 8세 미만 아동 양육 가구 대상 월 아동수당 지급',
                        'rate': '수당 형태',
                        'detail_amount': '아동 1인당 월 10만원 지급',
                        'interest_rate_desc': '아동수당 (상환 불필요)',
                        'repayment': '해당 없음',
                        'tags': ['#아동', '#수당'],
                        'documents': ['주민등록등본', '가족관계증명서', '소득증빙서류', '통장 사본', '신청서']
                    }, ensure_ascii=False),
                    'link': 'https://www.mohw.go.kr'
                }
            ]
            
            # 데이터 삽입
            insert_count = 0
            for policy in policies_data:
                conn.execute("""
                    INSERT INTO policies (
                        target_type, title, agency, support_type, amount_desc,
                        period_desc, d_day, end_date, detail_json, link, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    policy['target_type'],
                    policy['title'],
                    policy['agency'],
                    policy['support_type'],
                    policy['amount_desc'],
                    policy['period_desc'],
                    policy['d_day'],
                    policy['end_date'],
                    policy['detail_json'],
                    policy['link']
                ))
                insert_count += 1
            
            conn.commit()
            print(f"총 {insert_count}개의 지원사업 데이터 삽입 완료")
            
            # 카테고리별 통계 출력
            print("\n[4단계] 카테고리별 데이터 통계:")
            stats = conn.execute("""
                SELECT target_type, COUNT(*) as count 
                FROM policies 
                WHERE is_active = 1 
                GROUP BY target_type
            """).fetchall()
            
            for stat in stats:
                print(f"  - {stat['target_type']}: {stat['count']}개")
            
            print("\n" + "=" * 50)
            print("지원사업 초기 데이터 삽입 완료!")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n[오류] 데이터 삽입 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    seed_policies()

