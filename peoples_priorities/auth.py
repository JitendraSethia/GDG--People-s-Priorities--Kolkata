import hmac
from functools import wraps

from flask import current_app, jsonify, redirect, request, session, url_for

SESSION_FLAG = "official_authenticated"


def passcode_matches(candidate):
    expected = current_app.config["OFFICIAL_PASSCODE"]
    return hmac.compare_digest((candidate or "").encode(), expected.encode())


def is_official():
    return bool(session.get(SESSION_FLAG))


def log_in_official():
    session[SESSION_FLAG] = True
    session.permanent = True


def log_out_official():
    session.pop(SESSION_FLAG, None)


def safe_next_url(target):
    # Only allow same-site absolute paths — no scheme, no host, no
    # protocol-relative "//evil.com".
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


def official_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if is_official():
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "unauthorized", "message": "Officials login required."}), 401
        return redirect(url_for("official.login", next=request.full_path.rstrip("?")))

    return wrapped
