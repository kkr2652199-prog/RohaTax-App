from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Register route modules
from . import dashboard  # noqa: F401
from . import user_api  # noqa: F401
from . import token_api  # noqa: F401
from . import settings_api  # noqa: F401
from . import activity_log_api  # noqa: F401
