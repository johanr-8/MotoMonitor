import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-to-something-secret")

# SMTP config (for future email notifications)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

# SMS config (stub)
SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
