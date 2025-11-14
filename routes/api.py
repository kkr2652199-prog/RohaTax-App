from flask import Blueprint, jsonify, request, session
from core.db import get_conn_optimized as get_conn
import sqlite3
import json
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 사용자 관련 API는 routes/api_modules/user_api.py로 이동됨
# 관리자 관련 API는 routes/api_modules/admin_api.py로 이동됨