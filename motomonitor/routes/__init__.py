from .auth import auth_bp
from .vehicles import vehicles_bp
from .reminders import reminders_bp
from .documents import documents_bp
from .dashboard import dashboard_bp
from .marketplace import marketplace_bp
from .admin import admin_bp
from .api import api_bp

all_blueprints = [
    auth_bp,
    vehicles_bp,
    reminders_bp,
    documents_bp,
    dashboard_bp,
    marketplace_bp,
    admin_bp,
    api_bp,
]
