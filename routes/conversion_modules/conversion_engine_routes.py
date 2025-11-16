"""
변환 엔진 라우트 모듈
변환 시작 및 다운로드 기능을 담당하는 핵심 모듈
"""

from flask import Blueprint, session, url_for, request, send_file
from urllib.parse import quote
import os
import time
import logging
import sqlite3
import zipfile
import io
import re
import traceback
from datetime import datetime

from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.conversion_engine import ConversionEngine
from core.token_service import calculate_available_tokens
from core.subscription_utils import get_user_subscription, is_unlimited_user
from core.file_upload_helper import save_uploaded_file, cleanup_temp_file, calculate_template_count
from core.token_deduction_processor import TokenDeductionProcessor
from core.activity_service import record_activity
from routes.utils.auth import ensure_login_for_json
from .conversion_helpers import validate_and_extract_params, prepare_supplier_info, check_token_balance

conversion_engine_bp = Blueprint('conversion_engine', __name__)

logger = logging.getLogger(__name__)


# 변환 시작: 파일 업로드 + 공급받는자 정보 추출 + 템플릿 기입
@conversion_engine_bp.route('/api/convert/start', methods=['POST'])
def start_conversion():
    """변환 시작 API (파일 업로드 + 공급받는자 정보 추출 + 템플릿 기입)

    요청 본문(Form Data):
      - template_id: str (예: hometax_official)
      - issue_date: str (예: 2025-10-01 또는 251001 형식 지원)
      - file_name: str (예: 세금계산서_251001.xlsx)
      - file: file (배달대행사 정산서 파일)
      - options: dict (선택)
    동작:
      - 로그인/토큰 체크 후 1토큰 사용
      - 업로드된 파일에서 공급받는자 정보 추출
      - 금액 정보 추출 (요금합계, 부가세)
      - 홈텍스 템플릿에 공급자 + 공급받는자 정보 기입
    """
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return guard_response
    
    # 파라미터 추출 및 검증
    validation_success, validation_result = validate_and_extract_params(request)
    if not validation_success:
        return validation_result
    
    # 검증 성공 시 파라미터 추출
    template_id = validation_result['template_id']
    issue_date = validation_result['issue_date']
    issue_date_raw = validation_result['issue_date_raw']
    file_name = validation_result['file_name']
    industry_type = validation_result['industry_type']
    guidelines = validation_result['guidelines']
    uploaded_file = validation_result['uploaded_file']

    # 사용자 정보 로드 → 공급자 정보 자동 매핑
    with get_conn() as conn:
        user = conn.execute(
            """
            SELECT username, email, company_name, business_number,
                   representative_name, phone, address, business_type, business_category,
                   token_balance, COALESCE(tokens_used, 0) AS tokens_used, plan_type
            FROM users WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if not user:
            return error('사용자를 찾을 수 없습니다', status=404)
    
    # ============================================
    # 핵심 변경 1: 파일을 먼저 저장
    # ============================================
    # 파일을 임시 디렉토리에 저장
    temp_file_path = save_uploaded_file(uploaded_file)
    
    # ============================================
    # 핵심 변경 2: 템플릿 건수 정밀 계산
    # ============================================
    template_count = calculate_template_count(temp_file_path, industry_type)
    
    if template_count == 0:
        # 임시 파일 정리
        cleanup_temp_file(temp_file_path)
        return error('파일에서 템플릿 건수를 계산할 수 없습니다. 파일 형식을 확인해주세요.', status=400)
    
    logger.info(f"템플릿 건수 계산 완료: {template_count}개")
    
    # ============================================
    # 토큰 잔량 확인
    # ============================================
    token_check_success, token_error_response = check_token_balance(user_id, template_count)
    if not token_check_success:
        return token_error_response

    # ============================================
    # 핵심 변경 4: 토큰은 변환 후 실제 생성된 수만큼만 차감
    # ============================================
    # 변환 전에는 차감하지 않고 잔량만 확인함
    # 토큰 차감을 위해 is_unlimited 재확인
    is_unlimited = is_unlimited_user(user_id)
    # 변환 시작 시간 기록
    conversion_start_time = time.time()
    logger.info(f"변환 시작: {time.strftime('%Y-%m-%d %H:%M:%S')} - 사용자 {user_id}")

    # ============================================
    # 골드 회원 공급자 선택 분기
    # ============================================
    supplier = prepare_supplier_info(user, validation_result, user_id)

    
    # 사용자 정보를 절대지침 시스템에 전달
    user_info = {
        'user_id': user_id,  # 사용자 ID 추가
        'company_name': user['company_name'] or user['username'],
        'business_number': user['business_number'] or '',
        'representative': user['representative_name'] or '',
        'email': user['email'] or '',
        'address': user['address'] or '',
        'phone': user['phone'] if 'phone' in user.keys() else '',
        'business_type': user['business_type'] or '',
        'business_category': user['business_category'] or '',
    }

    # 파일은 이미 저장됨 (temp_file_path에 저장되어 있음)

    # 변환 엔진 실행
    try:
        # 요청별 새로운 변환 엔진 인스턴스 생성 (상태 격리)
        conversion_engine = ConversionEngine()
        
        # 전체 변환 프로세스 실행 (상태 격리된 인스턴스 사용)
        conversion_result = conversion_engine.convert_file(
            uploaded_file_path=temp_file_path,
            supplier_info=supplier,
            template_id=template_id,
            industry_type=industry_type,
            guidelines=guidelines,
            issue_date=issue_date,
            file_name=file_name,
            user_info=user_info
        )
        
        if not conversion_result['success']:
            # 임시 파일 정리
            cleanup_temp_file(temp_file_path)
            return error(f"변환 실패: {conversion_result.get('error_message', '알 수 없는 오류')}", status=500)
        
        # 임시 파일 정리
        cleanup_temp_file(temp_file_path)
        
        # ============================================
        # 핵심 변경: 기록관을 통한 활동 로그 기록 및 토큰 업데이트
        # ============================================
        # DB 트랜잭션 내에서 활동 로그 기록 및 토큰 업데이트
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                
                # 사용자 정보 재조회 (최신 토큰 잔액 확인)
                user_current = cursor.execute(
                    """
                    SELECT id, plan_type, token_balance, COALESCE(tokens_used, 0) AS tokens_used
                    FROM users WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()
                
                if not user_current:
                    logger.error(f"사용자 정보를 찾을 수 없습니다: user_id={user_id}")
                    return error('사용자 정보를 찾을 수 없습니다', status=404)
                
                # --- [수정] '기록관' 호출 방식을 새로운 범용 함수에 맞게 변경 ---
                
                # 1. 정보 추출
                user_id_for_activity = user_current['id']
                plan_type = user_current['plan_type'] or 'free'
                token_balance_before = user_current['token_balance'] or 0
                total_recipients = conversion_result.get('total_recipients', 0)
                
                # 2. '경제 헌법' 적용
                potential_cost = total_recipients * -1
                token_change = 0
                if plan_type not in ['unlimited', 'gold', 'gold-vip']:
                    token_change = potential_cost
                token_balance_after = token_balance_before + token_change
                
                # 3. 범용 activity_data 생성
                activity_data = {
                    'user_id': user_id_for_activity,
                    'performed_by_id': user_id_for_activity,
                    'performed_by_type': 'USER',
                    'activity_type': 'FILE_CONVERT',
                    'details': {
                        "filename": file_name,
                        "extracted_rows": total_recipients,
                        "cost_policy": "1_token_per_row(temp)"
                    },
                    'token_change': token_change,
                    'potential_cost': potential_cost,
                    'token_balance_before': token_balance_before,
                    'token_balance_after': token_balance_after,
                    'user_plan_snapshot': plan_type
                }
                
                # 4. 새로운 범용 '기록관' 호출
                record_activity(cursor, activity_data)
                
                # 트랜잭션 커밋
                conn.commit()
                logger.info(f"활동 로그 기록 완료: user_id={user_id}, file_name={file_name}")
                
        except Exception as activity_error:
            logger.error(f"활동 로그 기록 중 오류 발생: {str(activity_error)}")
            # 활동 로그 기록 실패는 치명적이지 않으므로 계속 진행
            # 하지만 경고 로그는 남김
            traceback.print_exc()
        
        # ============================================
        # 핵심 변경: 연동 모듈을 통한 토큰 차감
        # ============================================
        token_processor = TokenDeductionProcessor()
        token_result = token_processor.process_token_deduction(
            user_id=user_id,
            is_unlimited=is_unlimited,
            conversion_result=conversion_result
        )

        if not token_result.get('success'):
            logger.error(f"토큰 차감 실패: {token_result.get('message')}")
            return error(token_result.get('message', '토큰 처리 중 오류가 발생했습니다'), status=500)

        logger.info(f"토큰 차감 결과: {token_result['message']}")
        
        # 변환 완료 시간 기록 및 실행 시간 계산
        conversion_end_time = time.time()
        execution_time = round(conversion_end_time - conversion_start_time, 2)
        logger.info(f"변환 완료: {time.strftime('%Y-%m-%d %H:%M:%S')} - 실행시간: {execution_time}초 - 사용자 {user_id}")
        
        # 세션에 변환 결과 저장
        session['last_conversion_result'] = conversion_result
        session['last_file_name'] = file_name  # 다운로드 파일명 저장
        
        # 토큰 페이로드 구성 (중앙은행 함수 사용)
        token_balance_fallback = user['token_balance'] or 0
        tokens_used_fallback = user['tokens_used'] or 0
        tokens_payload = {
            'total_granted': token_result.get('total_granted', token_balance_fallback),
            'total_used': token_result.get('tokens_used_after', tokens_used_fallback),
            'available_tokens': token_result.get('available_tokens_after', calculate_available_tokens(token_balance_fallback, tokens_used_fallback)),
            'templates_created': token_result.get('recipient_count', 0)
        }

        return success('변환 완료', data={
            'conversion_result': conversion_result,
            'download_url': url_for('conversion_engine.download_converted', _external=False),
            'download_filename': file_name,
            'detailed_stats': conversion_result.get('detailed_stats', {}),
            'tokens': tokens_payload
        })
        
    except Exception as e:
        # 변환 전에 토큰을 차감하지 않았으므로 환불 불필요
        logger.error(f"변환 실패: {str(e)}")
        traceback.print_exc()
        
        # 임시 파일 정리
        if 'temp_file_path' in locals():
            cleanup_temp_file(temp_file_path)
        return error(f'변환 처리 중 오류 발생: {str(e)}', status=500)


@conversion_engine_bp.route('/api/convert/download', methods=['GET'])
def download_converted():
    """변환된 홈텍스 파일 다운로드

    - 변환 결과 파일이 1개인 경우: XLSX 파일을 직접 다운로드로 반환
    - 변환 결과 파일이 2개 이상인 경우: ZIP으로 묶어 반환 (기존 동작 유지)
    """
    _, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return guard_response

    conversion_result = session.get('last_conversion_result')
    if not conversion_result or not conversion_result.get('success'):
        return error('다운로드할 변환 결과가 없습니다', status=404)

    try:
        files = [p for p in conversion_result.get('files', []) if os.path.exists(p)]

        # 사용자가 다운로드 모드를 선택할 수 있도록 쿼리 파라미터 지원
        # mode=auto(기본): 1개면 단일, 2개 이상이면 ZIP
        # mode=zip: 개수와 무관하게 ZIP으로 묶어서 제공
        mode = (request.args.get('mode') or 'auto').lower()

        # 파일이 하나라면 ZIP이 아닌 단일 파일로 내려준다 (또는 zip 강제 시 ZIP)
        if len(files) == 1 and mode != 'zip':
            single_path = files[0]
            filename = os.path.basename(single_path)
            # xlsx/xlsm 등 확장자에 따라 MIME 설정 (기본 xlsx)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.xlsx', '.xltx']:
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif ext in ['.xlsm']:
                mimetype = 'application/vnd.ms-excel.sheet.macroEnabled.12'
            else:
                mimetype = 'application/octet-stream'

            return send_file(
                single_path,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )

        # 2개 이상 또는 zip 강제 시 ZIP으로 제공
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                filename = os.path.basename(file_path)
                zip_file.write(file_path, filename)
        zip_buffer.seek(0)

        # 사용자 입력 파일명 사용 (쿼리 파라미터 우선, 세션 차선, 없으면 기본값)
        user_file_name = (request.args.get('filename') or session.get('last_file_name', '')).strip()
        zip_filename = '홈텍스_일괄등록_파일들.zip'  # 기본값
        
        if user_file_name:
            # 확장자 제거 후 .zip 추가
            base_name = user_file_name.rsplit('.', 1)[0] if '.' in user_file_name else user_file_name
            # Windows 금지 문자 제거
            base_name = re.sub(r'[\\/:*?"<>|]', '', base_name).strip()
            if base_name:  # 제거 후 빈 문자열이 아니면
                zip_filename = f"{base_name}.zip"
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return error(f'다운로드 처리 중 오류가 발생했습니다: {str(e)}', status=500)
