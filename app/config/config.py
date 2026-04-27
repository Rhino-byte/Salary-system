"""
Configuration file for database connection and external services.

This module loads environment variables from a `.env` file using python-dotenv.
We use `find_dotenv()` so the .env file can live either in the project root
or in this `app/config/` folder without changing code.
"""

import os
from dotenv import load_dotenv, find_dotenv

# Load the closest .env file upwards from this directory
load_dotenv(find_dotenv())

# Neon Database connection string
# Expected format (from your Neon dashboard):
#   postgresql://<user>:<password>@<host>/<database>?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@hostname/database?sslmode=require")

# Validate DATABASE_URL (will be checked at runtime in main.py if needed)
# We don't raise here to allow the app to start and show a proper error message

# Email configuration for notifications (Gmail and generic SMTP)
# Supports either EMAIL_* or SMTP_* names (common in .env files).
def _int_env(*keys: str, default: int) -> int:
    for k in keys:
        v = os.getenv(k)
        if v is not None and str(v).strip() != "":
            try:
                return int(v)
            except ValueError:
                return default
    return default


EMAIL_HOST = os.getenv("EMAIL_HOST") or os.getenv("SMTP_HOST", "smtp.gmail.com")
EMAIL_PORT = _int_env("EMAIL_PORT", "SMTP_PORT", default=587)
EMAIL_USER = (os.getenv("EMAIL_USER") or os.getenv("SMTP_USER") or "").strip()
EMAIL_PASSWORD = (os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or os.getenv("SMTP_FROM_EMAIL") or "").strip()

# Inbound admin alerts (e.g. new advance / off-day requests)
ADMIN_NOTIFICATION_EMAIL = (os.getenv("ADMIN_NOTIFICATION_EMAIL") or "").strip()
_enable_flag = (os.getenv("ENABLE_ADMIN_EMAIL_NOTIFICATIONS") or "").strip().lower()
if _enable_flag in ("0", "false", "no", "off"):
    ENABLE_ADMIN_EMAIL_NOTIFICATIONS = False
elif _enable_flag in ("1", "true", "yes", "on"):
    ENABLE_ADMIN_EMAIL_NOTIFICATIONS = True
else:
    # Unset: enable when recipient and SMTP credentials are present
    ENABLE_ADMIN_EMAIL_NOTIFICATIONS = bool(
        ADMIN_NOTIFICATION_EMAIL and EMAIL_USER and EMAIL_PASSWORD
    )


def _bool_env(key: str, default: bool) -> bool:
    v = (os.getenv(key) or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return default


# Public URL of the deployed app (used in notification emails for absolute links).
# Example: https://payroll.example.com — no trailing slash.
_raw_public = (os.getenv("APP_PUBLIC_URL") or os.getenv("PUBLIC_APP_URL") or "").strip().rstrip("/")
APP_PUBLIC_URL = _raw_public or ""

# SMTP connection mode: port 465 often uses implicit SSL; 587 typically uses STARTTLS.
SMTP_USE_SSL = _bool_env("SMTP_USE_SSL", False) or _bool_env("EMAIL_USE_SSL", False)
SMTP_USE_TLS = _bool_env("SMTP_USE_TLS", True)

# WhatsApp configuration (using Twilio or similar service)
WHATSAPP_ACCOUNT_SID = os.getenv("WHATSAPP_ACCOUNT_SID", "")
WHATSAPP_AUTH_TOKEN = os.getenv("WHATSAPP_AUTH_TOKEN", "")
WHATSAPP_FROM_NUMBER = os.getenv("WHATSAPP_FROM_NUMBER", "")

# AI Agent Configuration (Phase 2)
# Note: Detailed AI agent configuration is in app.ai_agent.config
# These are basic environment variable references for main config
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./vector_store")
