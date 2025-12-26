"""
비즈니스 라운지 라우트
소상공인 지원사업 및 금융 정보 제공 페이지
"""
from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
import json
from core.db import get_conn

biz_lounge_bp = Blueprint('biz_lounge', __name__, url_prefix='/biz-lounge')


def get_policies_from_db(target_type=None):
    """데이터베이스에서 지원사업 데이터 조회"""
    with get_conn() as conn:
        query = "SELECT * FROM policies WHERE is_active = 1"
        params = []
        
        if target_type:
            query += " AND target_type = ?"
            params.append(target_type)
        
        query += " ORDER BY d_day ASC, created_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        
        policies = []
        for row in rows:
            # detail_json 파싱
            detail_data = {}
            if row['detail_json']:
                try:
                    detail_data = json.loads(row['detail_json'])
                except:
                    detail_data = {}
            
            # 기존 더미 데이터 구조와 호환되도록 변환
            policy = {
                'id': row['id'],
                'title': row['title'],
                'organization': row['agency'],
                'org_short': row['agency'].split()[0] if row['agency'] else '',
                'd_day': row['d_day'] or 0,
                'tags': detail_data.get('tags', []),
                'status': '마감임박' if row['d_day'] and row['d_day'] <= 3 else '접수중',
                'description': detail_data.get('description', ''),
                'amount': row['amount_desc'] or '',
                'rate': detail_data.get('rate', ''),
                'period': row['period_desc'] or '',
                'detail_amount': detail_data.get('detail_amount', row['amount_desc'] or ''),
                'interest_rate_desc': detail_data.get('interest_rate_desc', ''),
                'repayment': detail_data.get('repayment', ''),
                'link': row['link'] or '',
                'documents': detail_data.get('documents', []),
                'target_type': row['target_type'],
                'support_type': row['support_type']
            }
            policies.append(policy)
        
        return policies


def get_dummy_loans():
    """금융상품 데이터 생성 (일반 은행 + 신용보증재단 연계 상품)"""
    loans = [
        # 일반 은행 상품
        {
            'id': 1,
            'bank': 'KB국민은행',
            'product_name': 'KB 스마트론',
            'rate': '3.54%',
            'rate_detail': '연 3.54% ~ 6.50% (변동금리)',
            'limit': '최대 3억원',
            'features': ['온라인 신청 가능', '당일 승인', '중도상환 수수료 없음'],
            'target': '소상공인, 자영업자',
            'term': '최대 5년',
            'guarantee_org': None
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
            'term': '최대 7년',
            'guarantee_org': None
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
            'term': '최대 3년',
            'guarantee_org': None
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
            'term': '최대 10년',
            'guarantee_org': None
        },
        # 신용보증재단 연계 상품
        {
            'id': 5,
            'bank': '케이뱅크',
            'product_name': '사장님 대출',
            'rate': '3.42%',
            'rate_detail': '연 3.42% (고정금리)',
            'limit': '최대 3,000만원',
            'features': ['비대면 신청', '10분 이내 승인', '신용보증재단 연계'],
            'target': '개인사업자, 소상공인',
            'term': '최대 3년',
            'guarantee_org': '신용보증재단'
        },
        {
            'id': 6,
            'bank': '카카오뱅크',
            'product_name': '대구 상생 대출',
            'rate': '3.35%',
            'rate_detail': '연 3.35% ~ 4.50% (변동금리)',
            'limit': '최대 1억원',
            'features': ['대구 지역 특화', '신용보증재단 연계', '빠른 심사'],
            'target': '대구 지역 소상공인',
            'term': '최대 5년',
            'guarantee_org': '대구신용보증재단'
        },
        {
            'id': 7,
            'bank': '신용보증재단',
            'product_name': '특례보증 대출',
            'rate': '3.20%',
            'rate_detail': '연 3.20% ~ 4.00% (변동금리)',
            'limit': '최대 5,000만원',
            'features': ['저금리 특례보증', '담보 불필요', '빠른 승인'],
            'target': '소상공인, 자영업자',
            'term': '최대 5년',
            'guarantee_org': '신용보증재단'
        },
        {
            'id': 8,
            'bank': '토스뱅크',
            'product_name': '토스 비즈론',
            'rate': '3.50%',
            'rate_detail': '연 3.50% ~ 5.50% (변동금리)',
            'limit': '최대 5,000만원',
            'features': ['모바일 전용', '당일 승인', '신용보증재단 연계'],
            'target': '소상공인, 자영업자',
            'term': '최대 3년',
            'guarantee_org': '신용보증재단'
        }
    ]
    
    return loans


@biz_lounge_bp.route('/')
def index():
    """비즈니스 라운지 메인 페이지"""
    # URL 파라미터에서 target_type 가져오기 (기본값: BIZ)
    target_type = request.args.get('target', 'BIZ')
    
    # DB에서 데이터 조회
    policies = get_policies_from_db(target_type=target_type)
    
    # 금융상품은 아직 하드코딩 유지 (나중에 확장 가능)
    loans = get_dummy_loans()
    
    return render_template(
        'biz_lounge/index.html',
        policies=policies,
        loans=loans,
        current_target=target_type
    )

