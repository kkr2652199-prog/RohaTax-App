from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Register route modules
from . import dashboard  # noqa: F401
