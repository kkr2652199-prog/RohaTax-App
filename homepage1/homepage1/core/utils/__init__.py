"""
Core utilities module
"""

from .excel_adapter import MockWorkbook, MockSheet, MockCell

# 기존 utils.py의 row_value 함수를 import
# core/utils.py 파일이 존재하는 경우 직접 import
import sys
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_utils_py_path = os.path.join(_parent_dir, 'utils.py')
if os.path.exists(_utils_py_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("core_utils", _utils_py_path)
    core_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core_utils)
    row_value = core_utils.row_value
else:
    # utils.py가 없는 경우 기본 구현 제공
    def row_value(row, key, default=None):
        try:
            value = row[key]
        except Exception:
            return default
        return default if value is None else value

__all__ = ['MockWorkbook', 'MockSheet', 'MockCell', 'row_value']

