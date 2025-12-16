import re
from typing import Any, Dict, Tuple


SCHEMA_VERSION = "1.0.0"


def _is_valid_date_iso(date_str: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str or ""))


def validate_convert_start(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate request body for /api/convert/start according to data bus contract.

    Required fields:
      - schema_version: str
      - template_id: str
      - issue_date: YYYY-MM-DD
      - file_name: str
    Optional:
      - options: dict
    """
    errors: Dict[str, str] = {}

    if not isinstance(payload, dict):
        return False, {"payload": "must be an object"}

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors["schema_version"] = f"unsupported or missing schema_version (expected {SCHEMA_VERSION})"

    template_id = payload.get("template_id")
    if not template_id or not isinstance(template_id, str):
        errors["template_id"] = "template_id is required"

    file_name = payload.get("file_name")
    if not file_name or not isinstance(file_name, str):
        errors["file_name"] = "file_name is required"

    issue_date = payload.get("issue_date")
    if not issue_date or not isinstance(issue_date, str) or not _is_valid_date_iso(issue_date):
        errors["issue_date"] = "issue_date must be YYYY-MM-DD"

    options = payload.get("options")
    if options is not None and not isinstance(options, dict):
        errors["options"] = "options must be an object"

    return (len(errors) == 0), errors


def normalize_convert_start(template_id: str, issue_date_iso: str, file_name: str, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "template_id": template_id,
        "issue_date": issue_date_iso,
        "file_name": file_name,
        "options": options or {},
    }


