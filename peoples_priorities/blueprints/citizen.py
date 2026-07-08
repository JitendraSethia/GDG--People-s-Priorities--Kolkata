from flask import Blueprint, abort, render_template

from ..db import get_db
from ..models import get_grievance_by_ticket
from ..seed_data.categories import CATEGORIES
from ..seed_data.wards import WARD_NAMES

citizen_bp = Blueprint("citizen", __name__)


@citizen_bp.route("/")
def landing():
    return render_template("citizen/landing.html")


@citizen_bp.route("/complaints")
def complaints_hub():
    return render_template("citizen/complaints_hub.html")


@citizen_bp.route("/report")
def intake_form():
    return render_template("citizen/intake_form.html", wards=WARD_NAMES, categories=CATEGORIES)


@citizen_bp.route("/report/confirmation/<ticket_id>")
def confirmation(ticket_id):
    grievance = get_grievance_by_ticket(get_db(), ticket_id)
    if grievance is None:
        abort(404)
    return render_template("citizen/confirmation.html", grievance=grievance)


@citizen_bp.route("/status")
def status_check():
    return render_template("citizen/status_check.html")


@citizen_bp.route("/completed")
def completed():
    return render_template("citizen/completed.html", wards=WARD_NAMES)
