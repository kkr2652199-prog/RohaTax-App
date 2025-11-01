"""
File-based token usage logger.
Appends JSONL entries under logs/token_logs/YYYY-MM-DD.log
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

try:
    from .token_log_schema import TokenLog
except Exception:  # fallback typing only
    TokenLog = object  # type: ignore


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def _log_path(base_dir: str = "logs/token_logs") -> str:
    _ensure_dir(base_dir)
    day = datetime.now(timezone.utc).date().isoformat()
    return os.path.join(base_dir, f"{day}.log")


def write_token_log(entry: TokenLog | dict) -> None:
    """Append a token log entry as JSON line. Safe-noop on errors."""
    try:
        record = entry.dict() if hasattr(entry, "dict") else dict(entry)
        # Ensure ISO timestamp string for readability
        if isinstance(record.get("created_at"), (datetime,)):
            record["created_at"] = record["created_at"].isoformat()
        path = _log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Intentionally swallow to avoid impacting request path
        pass




