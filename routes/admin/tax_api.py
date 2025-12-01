"""
세무 리포트 API 모듈
상용화 준비: 부가세 신고를 위한 전용 통계 시스템
"""

from flask import Blueprint, request, jsonify, send_file, session
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
import sqlite3
import logging
from datetime import datetime, timedelta
import pandas as pd
import io
from ..utils.auth import ensure_admin_for_json

logger = logging.getLogger(__name__)

admin_tax_bp = Blueprint('admin_tax', __name__, url_prefix='/admin/api/tax')


@admin_tax_bp.route('/stats', methods=['GET'])
def get_tax_stats():
    """
    세무 통계 조회 API
    
    Query Parameters:
        type: daily, monthly, quarterly, yearly (기본값: monthly)
        year: 연도 (기본값: 현재 연도)
        month: 월 (1-12, 기본값: 현재 월)
        start_date: 시작일 (YYYY-MM-DD 형식)
        end_date: 종료일 (YYYY-MM-DD 형식)
    
    Response:
        {
            "success": true,
            "data": {
                "total_revenue": 0,      # 총 매출 (부가세 포함)
                "total_supply": 0,      # 총 공급가액
                "total_vat": 0,          # 총 부가세 (납부예정액)
                "order_count": 0,       # 주문 건수
                "chart_data": [         # 차트용 데이터
                    {
                        "date": "2024-01",
                        "revenue": 0,
                        "supply": 0,
                        "vat": 0
                    }
                ]
            }
        }
    """
    # 관리자 인증 확인
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    # 파라미터 파싱
    report_type = request.args.get('type', 'monthly')  # daily, monthly, quarterly, yearly
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 날짜 범위 계산
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 날짜 범위 설정
            if start_date and end_date:
                # 직접 지정된 날짜 범위 사용
                date_filter = "DATE(o.created_at) BETWEEN ? AND ?"
                date_params = (start_date, end_date)
                date_format = "%Y-%m-%d"
            elif report_type == 'daily':
                # 일별: 지정된 날짜 또는 오늘
                target_date = f"{year}-{month:02d}-{now.day:02d}" if month else now.strftime("%Y-%m-%d")
                date_filter = "DATE(o.created_at) = ?"
                date_params = (target_date,)
                date_format = "%Y-%m-%d"
            elif report_type == 'monthly':
                # 월별: 지정된 연도-월
                date_filter = "strftime('%Y-%m', o.created_at) = ?"
                date_params = (f"{year}-{month:02d}",)
                date_format = "%Y-%m"
            elif report_type == 'quarterly':
                # 분기별: 지정된 연도의 분기
                quarter = (month - 1) // 3 + 1 if month else (now.month - 1) // 3 + 1
                start_month = (quarter - 1) * 3 + 1
                end_month = quarter * 3
                date_filter = "strftime('%Y-%m', o.created_at) BETWEEN ? AND ?"
                date_params = (f"{year}-{start_month:02d}", f"{year}-{end_month:02d}")
                date_format = "%Y-%m"
            elif report_type == 'yearly':
                # 년별: 지정된 연도
                date_filter = "strftime('%Y', o.created_at) = ?"
                date_params = (str(year),)
                date_format = "%Y"
            else:
                # 기본값: 이번 달
                date_filter = "strftime('%Y-%m', o.created_at) = ?"
                date_params = (now.strftime("%Y-%m"),)
                date_format = "%Y-%m"
            
            # 총 통계 조회 (status='paid'인 주문만)
            total_stats = conn.execute(
                f"""
                SELECT 
                    COUNT(*) as order_count,
                    COALESCE(SUM(o.amount), 0) as total_revenue,
                    COALESCE(SUM(o.supply_price), 0) as total_supply,
                    COALESCE(SUM(o.vat), 0) as total_vat
                FROM orders o
                WHERE o.status = 'paid'
                  AND {date_filter}
                """,
                date_params
            ).fetchone()
            
            # 차트 데이터 조회 (일별/월별 그룹화)
            if report_type == 'daily':
                # 일별 데이터
                chart_query = f"""
                    SELECT 
                        DATE(o.created_at) as date,
                        COUNT(*) as order_count,
                        COALESCE(SUM(o.amount), 0) as revenue,
                        COALESCE(SUM(o.supply_price), 0) as supply,
                        COALESCE(SUM(o.vat), 0) as vat
                    FROM orders o
                    WHERE o.status = 'paid'
                      AND {date_filter}
                    GROUP BY DATE(o.created_at)
                    ORDER BY date ASC
                """
            elif report_type == 'monthly':
                # 월별 데이터
                chart_query = f"""
                    SELECT 
                        strftime('%Y-%m', o.created_at) as date,
                        COUNT(*) as order_count,
                        COALESCE(SUM(o.amount), 0) as revenue,
                        COALESCE(SUM(o.supply_price), 0) as supply,
                        COALESCE(SUM(o.vat), 0) as vat
                    FROM orders o
                    WHERE o.status = 'paid'
                      AND {date_filter}
                    GROUP BY strftime('%Y-%m', o.created_at)
                    ORDER BY date ASC
                """
            elif report_type == 'quarterly':
                # 분기별 데이터
                chart_query = f"""
                    SELECT 
                        strftime('%Y-Q', o.created_at) || CAST((CAST(strftime('%m', o.created_at) AS INTEGER) - 1) / 3 + 1 AS TEXT) as date,
                        COUNT(*) as order_count,
                        COALESCE(SUM(o.amount), 0) as revenue,
                        COALESCE(SUM(o.supply_price), 0) as supply,
                        COALESCE(SUM(o.vat), 0) as vat
                    FROM orders o
                    WHERE o.status = 'paid'
                      AND {date_filter}
                    GROUP BY strftime('%Y', o.created_at), (CAST(strftime('%m', o.created_at) AS INTEGER) - 1) / 3 + 1
                    ORDER BY date ASC
                """
            else:  # yearly
                # 년별 데이터
                chart_query = f"""
                    SELECT 
                        strftime('%Y', o.created_at) as date,
                        COUNT(*) as order_count,
                        COALESCE(SUM(o.amount), 0) as revenue,
                        COALESCE(SUM(o.supply_price), 0) as supply,
                        COALESCE(SUM(o.vat), 0) as vat
                    FROM orders o
                    WHERE o.status = 'paid'
                      AND {date_filter}
                    GROUP BY strftime('%Y', o.created_at)
                    ORDER BY date ASC
                """
            
            chart_rows = conn.execute(chart_query, date_params).fetchall()
            chart_data = [
                {
                    'date': row['date'],
                    'revenue': row['revenue'] or 0,
                    'supply': row['supply'] or 0,
                    'vat': row['vat'] or 0,
                    'order_count': row['order_count'] or 0
                }
                for row in chart_rows
            ]
            
            return success('세무 통계 조회 성공', data={
                'total_revenue': total_stats['total_revenue'] or 0,
                'total_supply': total_stats['total_supply'] or 0,
                'total_vat': total_stats['total_vat'] or 0,
                'order_count': total_stats['order_count'] or 0,
                'chart_data': chart_data,
                'report_type': report_type,
                'date_range': {
                    'start': start_date or (f"{year}-{month:02d}-01" if month else f"{year}-01-01"),
                    'end': end_date or (f"{year}-{month:02d}-{now.day:02d}" if month else f"{year}-12-31")
                }
            })
            
    except Exception as e:
        logger.error(f"세무 통계 조회 실패: {str(e)}")
        return error(f'세무 통계 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_tax_bp.route('/download', methods=['GET'])
def download_tax_report():
    """
    세무 리포트 엑셀 다운로드 API
    
    Query Parameters:
        type: daily, monthly, quarterly, yearly (기본값: monthly)
        year: 연도
        month: 월 (1-12)
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
    
    Response:
        Excel 파일 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
        컬럼: 일자, 주문번호, 상품명, 공급가, 부가세, 합계
    """
    # 관리자 인증 확인
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    # 파라미터 파싱
    report_type = request.args.get('type', 'monthly')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 날짜 범위 계산
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 날짜 범위 설정
            if start_date and end_date:
                date_filter = "DATE(o.created_at) BETWEEN ? AND ?"
                date_params = (start_date, end_date)
            elif report_type == 'daily':
                target_date = f"{year}-{month:02d}-{now.day:02d}" if month else now.strftime("%Y-%m-%d")
                date_filter = "DATE(o.created_at) = ?"
                date_params = (target_date,)
            elif report_type == 'monthly':
                date_filter = "strftime('%Y-%m', o.created_at) = ?"
                date_params = (f"{year}-{month:02d}",)
            elif report_type == 'quarterly':
                quarter = (month - 1) // 3 + 1 if month else (now.month - 1) // 3 + 1
                start_month = (quarter - 1) * 3 + 1
                end_month = quarter * 3
                date_filter = "strftime('%Y-%m', o.created_at) BETWEEN ? AND ?"
                date_params = (f"{year}-{start_month:02d}", f"{year}-{end_month:02d}")
            elif report_type == 'yearly':
                date_filter = "strftime('%Y', o.created_at) = ?"
                date_params = (str(year),)
            else:
                date_filter = "strftime('%Y-%m', o.created_at) = ?"
                date_params = (now.strftime("%Y-%m"),)
            
            # 주문 내역 조회
            orders = conn.execute(
                f"""
                SELECT 
                    DATE(o.created_at) as 일자,
                    o.merchant_uid as 주문번호,
                    o.product_name as 상품명,
                    o.supply_price as 공급가,
                    o.vat as 부가세,
                    o.amount as 합계
                FROM orders o
                WHERE o.status = 'paid'
                  AND {date_filter}
                ORDER BY o.created_at ASC
                """,
                date_params
            ).fetchall()
            
            # DataFrame 생성
            df = pd.DataFrame([dict(row) for row in orders])
            
            if df.empty:
                # 빈 데이터프레임인 경우 기본 구조만 생성
                df = pd.DataFrame(columns=['일자', '주문번호', '상품명', '공급가', '부가세', '합계'])
            
            # 엑셀 파일 생성 (메모리 버퍼)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='세무 리포트', index=False)
                
                # 시트 스타일링 (선택사항)
                worksheet = writer.sheets['세무 리포트']
                # 컬럼 너비 자동 조정
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
            
            output.seek(0)
            
            # 파일명 생성
            if start_date and end_date:
                filename = f"세무리포트_{start_date}_{end_date}.xlsx"
            elif report_type == 'daily':
                filename = f"세무리포트_일별_{year}{month:02d}{now.day:02d}.xlsx"
            elif report_type == 'monthly':
                filename = f"세무리포트_월별_{year}{month:02d}.xlsx"
            elif report_type == 'quarterly':
                quarter = (month - 1) // 3 + 1 if month else (now.month - 1) // 3 + 1
                filename = f"세무리포트_분기별_{year}Q{quarter}.xlsx"
            else:  # yearly
                filename = f"세무리포트_년별_{year}.xlsx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        logger.error(f"세무 리포트 다운로드 실패: {str(e)}")
        return error(f'세무 리포트 다운로드 중 오류가 발생했습니다: {str(e)}', status=500)

