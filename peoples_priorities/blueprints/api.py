from flask import Blueprint, current_app, jsonify, request

from .. import models
from ..auth import official_required
from ..clustering import find_cluster_match_for_new, recompute_cluster_urgency
from ..db import get_db
from ..gemini_client import classify_grievance
from ..chatbot import answer as chatbot_answer
from ..seed_data.categories import CATEGORIES
from ..seed_data.wards import WARD_NAMES, nearest_ward
from ..uploads import save_photo, save_photo_base64
from ..urgency import compute_urgency
from ..validation import is_valid_name, is_valid_phone

api_bp = Blueprint("api", __name__)


@api_bp.get("/meta")
def meta():
    return jsonify({
        "wards": WARD_NAMES,
        "categories": [{"code": code, "label": info["label"]} for code, info in CATEGORIES.items()],
        "maps_api_key_present": current_app.config["MAPS_ENABLED"],
        "gemini_enabled": current_app.config["GEMINI_ENABLED"],
    })


@api_bp.get("/wards/nearest")
def wards_nearest():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    if lat is None or lng is None:
        return jsonify({"error": "invalid_request", "message": "lat and lng are required"}), 400
    ward, distance = nearest_ward(lat, lng)
    return jsonify({"ward": ward, "distance_meters": round(distance, 1)})


@api_bp.get("/grievances")
def list_grievances():
    db = get_db()
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 50, type=int), 200)
    collapse = request.args.get("cluster", "true").lower() != "false"

    result = models.list_grievances(
        db,
        ward=request.args.get("ward"),
        category=request.args.get("category"),
        status=request.args.get("status"),
        urgency_level=request.args.get("urgency_level"),
        min_urgency=request.args.get("min_urgency", type=int),
        q=request.args.get("q"),
        collapse_clusters=collapse,
        sort=request.args.get("sort", "urgency_desc"),
        page=page,
        page_size=page_size,
    )
    return jsonify(result)


@api_bp.get("/grievances/<ticket_id>")
def grievance_detail(ticket_id):
    db = get_db()
    grievance = models.get_grievance_by_ticket(db, ticket_id)
    if grievance is None:
        return jsonify({"error": "not_found", "message": f"No grievance with ticket_id {ticket_id}"}), 404
    return jsonify(grievance)


@api_bp.get("/stats")
def stats():
    db = get_db()
    result = models.get_stats(
        db,
        ward=request.args.get("ward"),
        days=request.args.get("days", 90, type=int),
    )
    return jsonify(result)


@api_bp.get("/wards/<ward>/planning")
def ward_planning(ward):
    if ward not in WARD_NAMES:
        return jsonify({"error": "not_found", "message": f"Unknown ward {ward}"}), 404
    db = get_db()
    result = models.get_ward_planning(db, ward, weeks=request.args.get("weeks", 12, type=int))
    return jsonify(result)


@api_bp.get("/completed")
def completed():
    db = get_db()
    result = models.get_completed(
        db,
        ward=request.args.get("ward"),
        category=request.args.get("category"),
        days=request.args.get("days", 90, type=int),
        page=request.args.get("page", 1, type=int),
        page_size=min(request.args.get("page_size", 20, type=int), 100),
    )
    return jsonify(result)


@api_bp.post("/grievances")
def submit_grievance():
    form = request.form
    raw_text = (form.get("raw_text") or "").strip()
    citizen_name = (form.get("citizen_name") or "").strip() or None
    citizen_phone = (form.get("citizen_phone") or "").strip() or None

    try:
        latitude = float(form["latitude"]) if form.get("latitude") else None
        longitude = float(form["longitude"]) if form.get("longitude") else None
    except ValueError:
        latitude = longitude = None

    if not raw_text:
        return jsonify({"error": "invalid_request", "message": "raw_text is required"}), 400
    if latitude is None or longitude is None:
        return jsonify({
            "error": "invalid_request",
            "message": "Location is required — please enable GPS and try again.",
        }), 400
    if not is_valid_name(citizen_name):
        return jsonify({"error": "invalid_request", "message": "Name can only contain letters."}), 400
    if not is_valid_phone(citizen_phone):
        return jsonify({"error": "invalid_request", "message": "Please enter a valid 10-digit mobile number."}), 400

    ward, _distance = nearest_ward(latitude, longitude)

    classification = classify_grievance(raw_text, language_hint=form.get("language"))

    urgency = compute_urgency(
        classification["category"],
        classification.get("translated_text") or raw_text,
        affected_count=classification["affected_count_estimate"],
        language=classification["detected_language"],
    )

    db = get_db()
    candidate = {
        "id": None,
        "ward": ward,
        "category": classification["category"],
        "raw_text": raw_text,
        "language": classification["detected_language"],
        "latitude": latitude,
        "longitude": longitude,
    }
    cluster_id, matched = find_cluster_match_for_new(db, candidate)
    if cluster_id and matched["cluster_id"] is None:
        db.execute("UPDATE grievances SET cluster_id = ? WHERE id = ?", (cluster_id, matched["id"]))

    ticket_id, grievance_id = models.insert_grievance(
        db,
        citizen_name=citizen_name,
        citizen_phone=citizen_phone,
        raw_text=raw_text,
        language=classification["detected_language"],
        category=classification["category"],
        summary=classification["summary"],
        urgency=urgency,
        ward=ward,
        latitude=latitude,
        longitude=longitude,
        cluster_id=cluster_id,
        affected_count=classification["affected_count_estimate"],
    )

    photo_file = request.files.get("photo")
    photo_base64 = form.get("photo_base64")
    try:
        if photo_file and photo_file.filename:
            models.set_photo_path(db, grievance_id, save_photo(photo_file, ticket_id))
        elif photo_base64:
            models.set_photo_path(db, grievance_id, save_photo_base64(photo_base64, ticket_id))
    except ValueError as exc:
        current_app.logger.warning("Photo upload rejected for %s: %s", ticket_id, exc)

    if cluster_id:
        db.execute("UPDATE grievances SET cluster_id = ? WHERE id = ?", (cluster_id, grievance_id))
        db.commit()
        recompute_cluster_urgency(db, cluster_id)
        db.commit()

    final = models.get_grievance_by_ticket(db, ticket_id)
    return jsonify({
        "ticket_id": ticket_id,
        "ward": ward,
        "category": final["category"],
        "category_label": classification["category_label"],
        "urgency_level": final["urgency_level"],
        "urgency_score": final["urgency_score"],
        "is_cluster": bool(cluster_id),
        "message": "Grievance received. Use your ticket ID to track status.",
    }), 201


@api_bp.patch("/grievances/<ticket_id>/status")
@official_required
def update_grievance_status(ticket_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in models.VALID_STATUSES:
        return jsonify({"error": "invalid_request", "message": f"status must be one of {models.VALID_STATUSES}"}), 400

    db = get_db()
    updated = models.update_status(db, ticket_id, status, payload.get("note"))
    if not updated:
        return jsonify({"error": "not_found", "message": f"No grievance with ticket_id {ticket_id}"}), 404

    return jsonify(models.get_grievance_by_ticket(db, ticket_id))


@api_bp.post("/chatbot")
def chatbot():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "invalid_request", "message": "message is required"}), 400

    db = get_db()
    reply, grievance = chatbot_answer(db, message, payload.get("ticket_id"))
    return jsonify({"reply": reply, "grievance": grievance})
