"""변환 엔진 응답 생성 유틸리티."""

from __future__ import annotations

from typing import Any, Dict, List


def create_error_response(error_message: str, conversion_log: List[str]) -> Dict[str, Any]:
    """표준 오류 응답을 생성한다."""

    return {
        "success": False,
        "error_message": error_message,
        "files": [],
        "total_recipients": 0,
        "extraction_summary": {},
        "amount_summary": {},
        "conversion_log": conversion_log,
    }


def create_success_response(
    result_files: List[str],
    recipients: List[Dict[str, Any]],
    extraction_summary: Dict[str, Any],
    conversion_log: List[str],
    detailed_stats: Dict[str, Any],
    template_count: int = None,  # ✅ 추가: 실제 템플릿 기입 건수
) -> Dict[str, Any]:
    """표준 성공 응답을 생성한다."""

    # ✅ template_count가 제공되지 않으면 recipients 길이 사용 (하위 호환성)
    actual_template_count = template_count if template_count is not None else len(recipients)

    return {
        "success": True,
        "files": result_files,
        "total_recipients": len(recipients),  # 전체 추출 건수 (참고용)
        "template_count": actual_template_count,  # ✅ 추가: 실제 템플릿 기입 건수 (토큰 차감용)
        "actual_templates": actual_template_count,  # ✅ 추가: 별칭 (안전장치)
        "extraction_summary": extraction_summary,
        "conversion_log": conversion_log,
        "recipients_preview": recipients[:5],
        "detailed_stats": detailed_stats,
    }


def get_conversion_status(conversion_result: Dict[str, Any]) -> Dict[str, Any]:
    """변환 결과 상태 요약을 생성한다."""

    if not conversion_result.get("success"):
        return {
            "status": "failed",
            "message": conversion_result.get("error_message", "변환 실패"),
            "files_count": 0,
            "recipients_count": 0,
        }

    extraction_summary = conversion_result.get("extraction_summary", {})
    amount_summary = conversion_result.get("amount_summary", {})

    return {
        "status": "success",
        "message": "변환 완료",
        "files_count": len(conversion_result.get("files", [])),
        "recipients_count": conversion_result.get("total_recipients", 0),
        "extraction_rate": extraction_summary.get("extraction_rate", 0),
        "total_amount": amount_summary.get("total_amount", 0),
    }
