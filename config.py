import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key")

    OFFICIAL_PASSCODE = os.environ.get("OFFICIAL_PASSCODE", "kolkata2026").strip()
    # The officials app loads over cleartext http:// from the LAN IP, so the
    # session cookie must not be Secure-only; Lax still blocks cross-site sends.
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "grievances.db")
    )

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    USE_VERTEX_AI = os.environ.get("USE_VERTEX_AI", "false").lower() == "true"
    GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-south1")
    GEMINI_ENABLED = bool(GEMINI_API_KEY) or (USE_VERTEX_AI and bool(GOOGLE_CLOUD_PROJECT))

    MAPS_API_KEY = os.environ.get("MAPS_API_KEY", "").strip()
    MAPS_ENABLED = bool(MAPS_API_KEY)

    POLL_INTERVAL_MS = int(os.environ.get("POLL_INTERVAL_MS", "5000"))

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB — one photo per submission
