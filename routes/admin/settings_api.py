from flask import request

from core.responses import success, error
from core.admin_services import settings_service
from core.admin_services.settings_service import SettingsServiceError

from . import admin_bp
from ..utils.auth import ensure_admin_for_json


@admin_bp.route('/admin/api/email-settings', methods=['GET'])
def get_email_settings():
    """이메일 인증 관련 시스템 설정 값을 조회한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        result = settings_service.fetch_email_settings()
        return success('ok', data=result)

    except SettingsServiceError as exc:
        return error(str(exc), status=400)
    except Exception as exc:  # pylint: disable=broad-except
        return error(f'설정 조회 중 오류가 발생했습니다: {str(exc)}', status=500)


@admin_bp.route('/admin/api/email-settings/update', methods=['POST'])
def update_email_settings():
    """이메일 인증 시스템 설정 값을 갱신한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        data = request.get_json(silent=True) or {}
        settings_service.update_email_settings(data)
        return success('이메일 인증 설정이 업데이트되었습니다')

    except SettingsServiceError as exc:
        return error(str(exc), status=400)
    except Exception as exc:  # pylint: disable=broad-except
        return error(f'설정 업데이트 중 오류가 발생했습니다: {str(exc)}', status=500)
