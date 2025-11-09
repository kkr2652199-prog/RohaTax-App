from flask import request

from core.responses import success, error
from core.admin_services import token_service
from core.admin_services.token_service import TokenServiceError

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_for_json


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/grant', methods=['POST'])
def grant_tokens_to_user(user_id: int):
    """특정 사용자에게 토큰을 지급한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    try:
        token_service.grant_tokens(user_id, amount, admin_user_id)
    except TokenServiceError as exc:
        return _handle_token_service_error(exc)

    return success('granted')


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/reset', methods=['POST'])
def reset_tokens_for_user(user_id: int):
    """특정 사용자의 토큰 잔액과 사용량을 초기화한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        token_service.reset_tokens(user_id, admin_user_id)
    except TokenServiceError as exc:
        return _handle_token_service_error(exc)

    return success('reset')


@admin_bp.route('/admin/api/token-history', methods=['GET'])
def get_token_history():
    """비활성화된 사용자 목록을 조회한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        history = token_service.get_token_history()
    except TokenServiceError as exc:
        return _handle_token_service_error(exc)

    return success('ok', data={'history': history})


# --- [제거됨] 토큰 이력 삭제 API ---
# activity_logs는 감사 추적 목적상 삭제 불가능한 영구 기록으로 관리됩니다.
# 따라서 토큰 이력 삭제 기능은 제거되었습니다.


@admin_bp.route('/admin/api/grant-tokens', methods=['POST'])
def grant_tokens_via_payload():
    """사용자 ID와 금액을 payload로 받아 토큰을 지급한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or not amount:
        return error('User ID and token amount are required', status=400)

    try:
        amount = int(amount)
        if amount <= 0:
            return error('Token amount must be greater than zero', status=400)
    except ValueError:
        return error('Invalid token amount', status=400)

    admin_user_id = current_user_id()
    try:
        token_service.grant_tokens_bulk(user_id, amount, admin_user_id)
    except TokenServiceError as exc:
        return _handle_token_service_error(exc)

    return success('Tokens granted successfully')


@admin_bp.route('/admin/api/reset-tokens', methods=['POST'])
def reset_tokens_via_payload():
    """사용자 ID를 payload로 받아 토큰을 초기화한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    admin_user_id = current_user_id()
    try:
        token_service.reset_tokens_bulk(user_id, admin_user_id)
    except TokenServiceError as exc:
        return _handle_token_service_error(exc)

    return success('Tokens fully reset (balance 0, used 0)')


def _handle_token_service_error(exc: TokenServiceError):
    message = str(exc)
    lowered = message.lower()
    status = 400
    if 'administrator privileges' in lowered or 'invalid admin' in lowered:
        status = 403
    elif 'not found' in lowered:
        status = 404
    return error(message, status=status)
