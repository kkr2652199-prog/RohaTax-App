"""
비즈니스 라운지 라우트
소상공인 지원사업 및 금융 정보 제공 페이지
"""
from flask import Blueprint, render_template
from datetime import datetime, timedelta

biz_lounge_bp = Blueprint('biz_lounge', __name__, url_prefix='/biz-lounge')


def get_dummy_policies():
    """더미 지원사업 데이터 생성 (실제 정책자금 공고 수준)"""
    policies = [
        {
            'id': 1,
            'title': '2025년도 스마트상점 기술보급사업 모집 공고',
            'organization': '중소벤처기업진흥공단',
            'org_short': '중기진흥공단',
            'd_day': 5,
            'tags': ['#저금리', '#인천'],
            'status': '접수중',
            'description': '소상공인 매장의 디지털 전환을 위한 스마트 POS, 무인결제 시스템 등 기술보급 지원',
            'amount': '최대 5억원',
            'rate': '연 2.5%',
            'period': '2025.01.15 ~ 01.31',
            'detail_amount': '운전자금 최대 3억원 / 시설자금 최대 5억원',
            'interest_rate_desc': '정책자금 기준금리 + 0.5%p (변동)',
            'repayment': '2년 거치 3년 분할상환',
            'link': 'https://www.semas.or.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '대표자 신분증 사본']
        },
        {
            'id': 2,
            'title': '2025년 상반기 소상공인 경영안정자금 신규 모집',
            'organization': '소상공인시장진흥공단',
            'org_short': '소상공인공단',
            'd_day': 2,
            'tags': ['#저금리', '#경영안정'],
            'status': '마감임박',
            'description': '영업손실 보전 및 자금난 해소를 위한 저금리 대출 지원 (변동금리 적용)',
            'amount': '매출액의 150% 이내',
            'rate': '연 3.54%~',
            'period': '2025.01.20 ~ 01.25',
            'detail_amount': '운전자금 최대 7천만원 / 시설자금 최대 1억원',
            'interest_rate_desc': '정책자금 기준금리 + 0.2%p (변동)',
            'repayment': '2년 거치 3년 분할상환',
            'link': 'https://www.semas.or.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '소상공인 확인서', '대표자 신분증 사본']
        },
        {
            'id': 3,
            'title': '디지털 전환 지원사업 (스마트스토어 구축)',
            'organization': '과학기술정보통신부',
            'org_short': '과기정통부',
            'd_day': 12,
            'tags': ['#디지털', '#IT'],
            'status': '접수중',
            'description': '소상공인 온라인 판매 채널 구축 및 디지털 마케팅 시스템 도입 지원',
            'amount': '최대 2천만원',
            'rate': '보조금 80%',
            'period': '2025.02.01 ~ 02.28',
            'detail_amount': '보조금 최대 2천만원 (자부담 20%)',
            'interest_rate_desc': '보조금 형태 (이자 없음)',
            'repayment': '보조금 (상환 불필요)',
            'link': 'https://www.msit.go.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '사업계획서', '예산서']
        },
        {
            'id': 4,
            'title': '청년창업사관학교 2025년 1기 모집',
            'organization': '중소벤처기업부',
            'org_short': '중기부',
            'd_day': 8,
            'tags': ['#청년', '#창업'],
            'status': '접수중',
            'description': '만 39세 이하 청년 창업자 대상 창업자금 및 6개월 집중 멘토링 지원',
            'amount': '최대 1억원',
            'rate': '연 1.5%',
            'period': '2025.01.25 ~ 02.15',
            'detail_amount': '창업자금 최대 1억원 (단일 한도)',
            'interest_rate_desc': '정책자금 기준금리 + 0.0%p (고정)',
            'repayment': '3년 거치 2년 분할상환',
            'link': 'https://www.smba.go.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '대표자 신분증 사본', '창업계획서', '청년 확인서류']
        },
        {
            'id': 5,
            'title': '지역균형발전 특별자금 (2025년 상반기)',
            'organization': '한국산업은행',
            'org_short': '한국산업은행',
            'd_day': 1,
            'tags': ['#저금리', '#지역균형'],
            'status': '마감임박',
            'description': '지역 중소기업 경쟁력 강화를 위한 장기 저금리 자금 지원 (최대 10년)',
            'amount': '최대 10억원',
            'rate': '연 2.0%~',
            'period': '2025.01.10 ~ 01.26',
            'detail_amount': '운전자금 최대 5억원 / 시설자금 최대 10억원',
            'interest_rate_desc': '정책자금 기준금리 + 0.3%p (변동)',
            'repayment': '3년 거치 7년 분할상환',
            'link': 'https://www.kdb.co.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '재무제표', '대표자 신분증 사본']
        },
        {
            'id': 6,
            'title': '여성기업 성장지원사업 (기술개발 및 시장진입)',
            'organization': '여성가족부',
            'org_short': '여가부',
            'd_day': 15,
            'tags': ['#여성', '#성장지원'],
            'status': '접수중',
            'description': '여성기업 경영역량 강화 및 신시장 진입을 위한 기술개발비 및 마케팅비 지원',
            'amount': '최대 5천만원',
            'rate': '보조금 70%',
            'period': '2025.02.05 ~ 02.20',
            'detail_amount': '보조금 최대 5천만원 (자부담 30%)',
            'interest_rate_desc': '보조금 형태 (이자 없음)',
            'repayment': '보조금 (상환 불필요)',
            'link': 'https://www.mogef.go.kr',
            'documents': ['사업자등록증명', '국세납세증명서', '지방세납세증명서', '매출과세표준증명원', '여성기업 확인서', '사업계획서']
        }
    ]
    
    return policies


def get_dummy_loans():
    """더미 금융상품 데이터 생성"""
    loans = [
        {
            'id': 1,
            'bank': 'KB국민은행',
            'product_name': 'KB 스마트론',
            'rate': '3.54%',
            'rate_detail': '연 3.54% ~ 6.50% (변동금리)',
            'limit': '최대 3억원',
            'features': ['온라인 신청 가능', '당일 승인', '중도상환 수수료 없음'],
            'target': '소상공인, 자영업자',
            'term': '최대 5년'
        },
        {
            'id': 2,
            'bank': '신한은행',
            'product_name': '신한 비즈론',
            'rate': '3.78%',
            'rate_detail': '연 3.78% ~ 7.00% (변동금리)',
            'limit': '최대 5억원',
            'features': ['신용도 기반 금리', '빠른 심사', '담보 가능'],
            'target': '법인, 개인사업자',
            'term': '최대 7년'
        },
        {
            'id': 3,
            'bank': '하나은행',
            'product_name': '하나 원큐론',
            'rate': '3.42%',
            'rate_detail': '연 3.42% ~ 5.80% (변동금리)',
            'limit': '최대 2억원',
            'features': ['모바일 신청', '24시간 승인', '우대금리 적용'],
            'target': '소상공인',
            'term': '최대 3년'
        },
        {
            'id': 4,
            'bank': '우리은행',
            'product_name': '우리 비즈니스론',
            'rate': '3.66%',
            'rate_detail': '연 3.66% ~ 6.80% (변동금리)',
            'limit': '최대 10억원',
            'features': ['대출 한도 높음', '장기 상환 가능', '전문 상담 서비스'],
            'target': '중소기업, 법인',
            'term': '최대 10년'
        }
    ]
    
    return loans


@biz_lounge_bp.route('/')
def index():
    """비즈니스 라운지 메인 페이지"""
    policies = get_dummy_policies()
    loans = get_dummy_loans()
    
    return render_template(
        'biz_lounge/index.html',
        policies=policies,
        loans=loans
    )

