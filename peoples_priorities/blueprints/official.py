from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)

from ..auth import (
    is_official,
    log_in_official,
    log_out_official,
    official_required,
    passcode_matches,
    safe_next_url,
)
from ..seed_data.wards import WARD_NAMES
from ..seed_data.categories import CATEGORIES

official_bp = Blueprint("official", __name__, template_folder="../templates")


@official_bp.route("/")
def home():
    return redirect(url_for("official.map_view"))


@official_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if passcode_matches(request.form.get("passcode")):
            log_in_official()
            target = safe_next_url(request.args.get("next"))
            return redirect(target or url_for("official.map_view"))
        error = "Incorrect passcode. Please try again."
    elif is_official():
        return redirect(url_for("official.map_view"))
    return render_template("official/login.html", error=error)


@official_bp.route("/logout")
def logout():
    log_out_official()
    return redirect(url_for("official.login"))


@official_bp.route("/map")
@official_required
def map_view():
    return render_template(
        "official/map_view.html",
        wards=WARD_NAMES,
        maps_api_key=current_app.config["MAPS_API_KEY"],
        maps_enabled=current_app.config["MAPS_ENABLED"],
        active="map",
    )


@official_bp.route("/dashboard")
@official_required
def dashboard():
    return render_template(
        "official/dashboard.html", wards=WARD_NAMES, categories=CATEGORIES,
        active="dashboard",
    )


@official_bp.route("/planning")
@official_required
def planning_view():
    return render_template("official/planning_view.html", wards=WARD_NAMES, active="planning")
