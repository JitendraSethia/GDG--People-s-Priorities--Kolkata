import base64
import os
import re

from flask import current_app

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
_DATA_URL_PATTERN = re.compile(r"^data:image/(\w+);base64,(.+)$", re.DOTALL)


def _extension_for(filename, default="jpg"):
    if not filename or "." not in filename:
        return default
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext if ext in ALLOWED_EXTENSIONS else default


def save_photo(file_storage, ticket_id):
    """Save an uploaded (multipart) photo. Returns the URL path to serve it."""
    ext = _extension_for(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported photo type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{ticket_id}.{ext}"
    file_storage.save(os.path.join(upload_dir, filename))
    return f"/uploads/{filename}"


def save_photo_base64(data_url_or_raw_b64, ticket_id, mime_hint=None):
    """Save a base64-encoded photo (e.g. from the Capacitor Camera plugin's
    resultType: 'base64'). Accepts either a data: URL or raw base64 payload.
    """
    match = _DATA_URL_PATTERN.match(data_url_or_raw_b64)
    if match:
        image_format, payload = match.group(1).lower(), match.group(2)
    else:
        image_format, payload = (mime_hint or "jpeg").lower(), data_url_or_raw_b64

    ext = _extension_for(f"photo.{image_format}")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported photo type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{ticket_id}.{ext}"
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(base64.b64decode(payload))
    return f"/uploads/{filename}"
