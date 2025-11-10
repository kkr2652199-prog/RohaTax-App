"""
변환 처리 라우트 모듈
파일 변환, 다운로드 등의 핵심 변환 기능
"""

from flask import Blueprint, session, jsonify, request, send_file
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
# from core.template_manager import template_manager
from core.data_bus import validate_convert_start, normalize_convert_start, SCHEMA_VERSION
from core.conversion_engine import ConversionEngine
from core.security import generate_csrf_token
from datetime import datetime
from core.token_log_schema import make_token_log, DEFAULT_TOKEN_COSTS
from core.token_logger import write_token_log
import os
import tempfile
import json

convert_bp = Blueprint('convert', __name__)

def _row_value(row, key, default=None):
    """sqlite3.Row 안전 접근 헬퍼"""
    try:
        value = row[key]
    except Exception:
        return default
    return default if value is None else value


@convert_bp.route('/api/convert/start', methods=['POST'])
def start_conversion():
    """변환 시작 API (파일 업로드 + 공급받는자 정보 추출 + 템플릿 기입)"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    # CSRF 토큰 검증
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not csrf_token:
        return error('보안 토큰이 없습니다. 다시 시도해주세요.', status=403)

    # Form Data에서 파라미터 추출
    template_id = (request.form.get('template_id') or 'hometax_official').strip()
    issue_date_raw = (request.form.get('issue_date') or '').strip()
    file_name = (request.form.get('file_name') or '').strip()
    industry_type = (request.form.get('industry_type') or 'delivery').strip()
    guidelines_json = request.form.get('guidelines', '{}')
    
    # 업종별 지침 파싱
    try:
        guidelines = json.loads(guidelines_json)
        print(f"📋 활성화된 지침: {guidelines.get('name', 'Unknown')}")
    except:
        guidelines = {}
    
    # 파일 업로드 확인
    if 'file' not in request.files:
        return error('배달대행사 정산서 파일을 업로드해주세요', status=400)
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return error('파일이 선택되지 않았습니다', status=400)

    if not issue_date_raw:
        return error('전자세금일자를 선택하세요', status=400)
    if not file_name:
        return error('파일명을 입력하세요', status=400)

    # issue_date 정규화
    def normalize_issue_date(s: str) -> str:
        try:
            # 251001 형태
            if len(s) == 6 and s.isdigit():
                yy = int(s[0:2])
                mm = int(s[2:4])
                dd = int(s[4:6])
                yyyy = 2000 + yy
                return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
            # 25년10월01일 형태
            if '년' in s and '월' in s and '일' in s:
                yy = int(s.split('년')[0][-2:])
                rest = s.split('년')[1]
                mm = int(rest.split('월')[0])
                dd = int(rest.split('월')[1].split('일')[0])
                yyyy = 2000 + yy
                return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
            # ISO 날짜 시도
            return datetime.fromisoformat(s).date().isoformat()
        except Exception:
            return ''

    issue_date = normalize_issue_date(issue_date_raw)
    if not issue_date:
        return error('전자세금일자 형식이 올바르지 않습니다', status=400)

    # 사용자 정보 로드
    with get_conn() as conn:
        user = conn.execute(
            """
            SELECT username, email, company_name, business_number,
                   representative_name, phone, address, business_type, business_category,
                   token_balance, COALESCE(tokens_used, 0) AS tokens_used
            FROM users WHERE id = ?
            """,
            (session['user_id'],)
        ).fetchone()

        if not user:
            return error('사용자를 찾을 수 없습니다', status=404)

        # 토큰 확인 및 사용 1회
        available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
        if available_tokens < 1:
            return error('토큰이 부족합니다', status=400)

        new_tokens_used = (user['tokens_used'] or 0) + 1
        conn.execute(
            "UPDATE users SET tokens_used = ? WHERE id = ?",
            (new_tokens_used, session['user_id'])
        )
        conn.commit()

    # 공급자 정보 구성
    supplier_info = {
        'company_name': user['company_name'] or '미입력',
        'business_number': user['business_number'] or '미입력',
        'representative_name': user['representative_name'] or '미입력',
        'phone': user['phone'] or '미입력',
        'address': user['address'] or '미입력',
        'business_type': user['business_type'] or '미입력',
        'business_category': user['business_category'] or '미입력',
        'email': user['email'] or '미입력'
    }

    # 임시 파일 저장
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, uploaded_file.filename)
    uploaded_file.save(temp_file_path)

    # 로깅: 변환 시작
    try:
        write_token_log(make_token_log(
            user_id=session['user_id'],
            username=user['username'],
            action='convert_start',
            tokens=0,
            balance_before=available_tokens,
            balance_after=available_tokens,
            request_id=None,
            meta={
                'template_id': template_id,
                'issue_date': issue_date,
                'file_name': file_name,
                'industry_type': industry_type,
            }
        ))
        # 요청별 새로운 변환 엔진 인스턴스 생성 (상태 격리)
        conversion_engine = ConversionEngine()
        
        # 전체 변환 프로세스 실행 (상태 격리된 인스턴스 사용)
        conversion_result = conversion_engine.convert_file(
            file_path=temp_file_path,
            template_id=template_id,
            issue_date=issue_date,
            file_name=file_name,
            supplier_info=supplier_info,
            industry_type=industry_type,
            guidelines=guidelines
        )

        if conversion_result.get('success'):
            # 변환된 파일 경로 반환
            converted_file_path = conversion_result.get('output_file_path')
            # 로깅: 변환 성공 (과금 기록)
            try:
                cost = DEFAULT_TOKEN_COSTS.get('convert_success', 1)
                write_token_log(make_token_log(
                    user_id=session['user_id'],
                    username=user['username'],
                    action='convert_success',
                    tokens=cost,
                    balance_before=available_tokens,
                    balance_after=available_tokens - cost,
                    request_id=conversion_result.get('conversion_id'),
                    meta={'recipient_count': conversion_result.get('recipient_count', 0)}
                ))
            except Exception:
                pass
            
            return success('변환 완료', data={
                'conversion_id': conversion_result.get('conversion_id'),
                'file_name': file_name,
                'template_id': template_id,
                'issue_date': issue_date,
                'recipient_count': conversion_result.get('recipient_count', 0),
                'total_amount': conversion_result.get('total_amount', 0),
                'download_url': f'/api/convert/download?conversion_id={conversion_result.get("conversion_id")}',
                'remaining_tokens': available_tokens - 1
            })
        else:
            # 로깅: 변환 실패
            try:
                write_token_log(make_token_log(
                    user_id=session['user_id'],
                    username=user['username'],
                    action='convert_fail',
                    tokens=0,
                    balance_before=available_tokens,
                    balance_after=available_tokens,
                    request_id=None,
                    meta={'error': conversion_result.get('error', 'unknown')}
                ))
            except Exception:
                pass
            return error(f'변환 실패: {conversion_result.get("error", "알 수 없는 오류")}', status=500)

    except Exception as e:
        try:
            write_token_log(make_token_log(
                user_id=session.get('user_id', 0),
                username=None,
                action='convert_fail',
                tokens=0,
                balance_before=None,
                balance_after=None,
                request_id=None,
                meta={'exception': str(e)}
            ))
        except Exception:
            pass
        return error(f'변환 중 오류가 발생했습니다: {str(e)}', status=500)
    
    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            os.rmdir(temp_dir)
        except:
            pass


@convert_bp.route('/api/convert/download', methods=['GET'])
def download_converted_file():
    """변환된 파일 다운로드 API"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    try:
        conversion_id = request.args.get('conversion_id')
        if not conversion_id:
            return error('변환 ID가 필요합니다', status=400)
        
        # 변환 결과 파일 경로 조회 (실제 구현에서는 DB에서 조회)
        # 여기서는 임시로 파일 경로를 반환
        file_path = f"output/{conversion_id}_converted.xlsx"
        
        if not os.path.exists(file_path):
            return error('변환된 파일을 찾을 수 없습니다', status=404)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"converted_{conversion_id}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return error(f'파일 다운로드 중 오류가 발생했습니다: {str(e)}', status=500)
