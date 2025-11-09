from flask import request

from core.responses import success, error
from core.admin_services import user_service
from core.admin_services.user_service import UserServiceError, VALID_PLAN_TYPES

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_for_json


@admin_bp.route('/admin/api/users', methods=['GET'])
def list_general_users():
    """일반 사용자 목록을 조회한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    general_users = user_service.fetch_general_users()
    return success('ok', data={'users': general_users})


@admin_bp.route('/admin/api/admin-users', methods=['GET'])
def list_admin_users():
    """시스템 관리자 계정 목록을 조회한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    admin_users = user_service.fetch_admin_users()
    return success('ok', data={'admin_users': admin_users})


@admin_bp.route('/admin/api/admin-dashboard-stats', methods=['GET'])
def fetch_dashboard_stats():
    """관리자 대시보드에서 사용하는 요약 통계를 반환한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    stats = user_service.fetch_dashboard_stats()
    return success('ok', data=stats)


@admin_bp.route('/admin/api/users/<int:user_id>', methods=['PUT'])
def update_user_email(user_id: int):
    """특정 사용자의 이메일 정보를 수정한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email:
        return error('email required', status=400)

    try:
        user_service.update_user_email(user_id, email)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('updated')


@admin_bp.route('/admin/api/user-conversions/<int:user_id>', methods=['GET'])
def list_user_conversions(user_id: int):
    """특정 사용자의 최근 변환 이력을 조회한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        conversions = user_service.fetch_user_conversions(user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success(data={'conversions': conversions})


@admin_bp.route('/admin/api/users/<int:user_id>/approve', methods=['POST'])
def approve_user_by_id(user_id: int):
    """승인 대기 중인 사용자를 즉시 승인한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        user_service.approve_user(user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User approved successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/reject', methods=['POST'])
def reject_user_by_id(user_id: int):
    """승인 요청을 거절 처리한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        user_service.reject_user(user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User rejected successfully')


@admin_bp.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
def soft_delete_user(user_id: int):
    """사용자를 소프트 삭제 처리한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        user_service.soft_delete_user(user_id, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User status updated')


@admin_bp.route('/admin/api/users/<int:user_id>/restore', methods=['POST'])
def restore_user(user_id: int):
    """삭제/비활성/미승인 상태의 계정을 즉시 복구한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        user_service.restore_user(user_id, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User restored successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/purge', methods=['POST'])
def purge_user(user_id: int):
    """특정 사용자의 모든 데이터를 완전히 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        message = user_service.purge_user(user_id, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success(message)


@admin_bp.route('/admin/api/users/purge-all', methods=['POST'])
def purge_all_users():
    """지정한 관리자 계정을 제외하고 모든 사용자를 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    keep_username = data.get('keep_username') or 'kweon4309'

    try:
        message = user_service.purge_all_users(keep_username, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success(message)


@admin_bp.route('/admin/api/approve-user', methods=['POST'])
def approve_user_from_payload():
    """사용자 ID를 payload로 받아 승인한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    try:
        user_service.approve_user_from_payload(user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User approved successfully')


@admin_bp.route('/admin/api/delete-user', methods=['POST'])
def delete_user_from_payload():
    """사용자 ID를 payload로 받아 소프트 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    try:
        user_service.delete_user_from_payload(user_id, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success('User soft-deleted successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/change-plan', methods=['POST'])
@admin_bp.route('/admin/api/users/<int:user_id>/update-plan', methods=['POST'])
def change_user_plan(user_id: int):
    """사용자의 요금제를 변경한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    plan_type = data.get('plan_type')

    if not plan_type or plan_type not in VALID_PLAN_TYPES:
        return error(f'유효하지 않은 플랜 유형입니다. 가능한 값: {", ".join(VALID_PLAN_TYPES)}', status=400)

    try:
        message = user_service.change_user_plan(user_id, plan_type, admin_user_id)
    except UserServiceError as exc:
        return _handle_service_error(exc)

    return success(message)


def _handle_service_error(exc: UserServiceError):
    message = str(exc)
    lowered = message.lower()
    status = 400
    if 'not found' in lowered:
        status = 404
    elif 'administrator privileges' in lowered:
        status = 403
    return error(message, status=status)
