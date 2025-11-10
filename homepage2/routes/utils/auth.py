"""세션 기반 인증 보조 유틸리티.

`routes` 계층에서 반복되는 로그인 여부 확인 로직을 공통화한다.
"""

from __future__ import annotations

from typing import Optional, Tuple

from flask import session, redirect, url_for, flash

from core.responses import error


def current_user_id() -> Optional[int]:
    """세션에 저장된 사용자 ID를 정수 형태로 반환한다."""

    user_id = session.get("user_id")
    if user_id is None:
        return None

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def is_authenticated() -> bool:
    """로그인 상태 여부."""

    return current_user_id() is not None


def ensure_login_for_json() -> Tuple[Optional[int], Optional[object]]:
    """JSON 응답을 반환하는 라우트에서 로그인 여부를 검증한다."""

    user_id = current_user_id()
    if user_id is None:
        return None, error("로그인이 필요합니다", status=401)

    return user_id, None


def is_admin_user() -> bool:
    """세션에 설정된 관리자 여부를 확인한다."""

    return bool(session.get("is_admin"))


def ensure_admin_for_json() -> Tuple[Optional[int], Optional[object]]:
    """관리자 전용 JSON 라우트 검증."""

    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return None, guard_response

    if not is_admin_user():
        return None, error("관리자 권한이 필요합니다", status=403)

    return user_id, None


def redirect_if_unauthenticated(endpoint: str = "home.login"):
    """로그인하지 않은 경우 지정한 엔드포인트로 리디렉션한다."""

    if not is_authenticated():
        return redirect(url_for(endpoint))

    return None


def ensure_logged_in_view(
    *,
    login_endpoint: str = "home.login",
    flash_message: str = "로그인이 필요합니다",
    flash_category: str = "error",
):
    """뷰 함수에서 로그인 여부를 확인하고 필요 시 리디렉션."""

    if not is_authenticated():
        flash(flash_message, flash_category)
        return redirect(url_for(login_endpoint))
    return None


def ensure_admin_view(
    *,
    login_endpoint: str = "home.login",
    unauthorized_endpoint: str = "home.home",
    login_message: str = "로그인이 필요합니다",
    unauthorized_message: str = "관리자 권한이 필요합니다",
    category: str = "error",
):
    """관리자용 뷰 보호자."""

    response = ensure_logged_in_view(
        login_endpoint=login_endpoint,
        flash_message=login_message,
        flash_category=category,
    )
    if response is not None:
        return response

    if not is_admin_user():
        flash(unauthorized_message, category)
        return redirect(url_for(unauthorized_endpoint))

    return None

