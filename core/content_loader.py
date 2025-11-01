import json
import os
from typing import Any, Dict


def load_content() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    content_path = os.path.join(base_dir, 'core', 'content.json')
    try:
        with open(content_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


CONTENT_CACHE: Dict[str, Any] = load_content()


def get_text(path: str, default: str = "") -> str:
    parts = path.split('.')
    node: Any = CONTENT_CACHE
    for p in parts:
        if isinstance(node, dict) and p in node:
            node = node[p]
        else:
            return default
    return node if isinstance(node, str) else default

















