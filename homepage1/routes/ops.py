from flask import Blueprint
from core.responses import success

ops_bp = Blueprint('ops', __name__)


@ops_bp.route('/healthz')
def healthz():
    return success('ok')


@ops_bp.route('/readiness')
def readiness():
    # 간단한 준비 상태 확인 (확장 시 DB 핑 등 추가)
    return success('ready', data={'ready': True})


