import json
import math
import re
import uuid

from .seed_data.wards import WARDS

_STOPWORDS = {
    "the", "a", "an", "is", "are", "near", "for", "of", "to", "in", "on",
    "at", "and", "has", "have", "been", "since", "very", "this", "that",
    "it", "its", "with", "no", "not", "we", "our", "us", "i", "my", "worried",
}
_WORD_PATTERN = re.compile(r"[a-zA-Z]+")

GEO_RADIUS_METERS = 150
TEXT_SIMILARITY_THRESHOLD = 0.25
RECENCY_WINDOW_DAYS = 45


def _tokenize(text):
    words = _WORD_PATTERN.findall(text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def haversine_meters(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return float("inf")
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _mentioned_landmark(text, ward):
    text_lower = text.lower()
    for landmark in WARDS.get(ward, {}).get("landmarks", []):
        if landmark.lower() in text_lower:
            return landmark
    return None


def new_cluster_id():
    return f"CL-{uuid.uuid4().hex[:8]}"


def find_cluster_match(candidate, existing_reports):
    """candidate/existing_reports are dicts with: id, ward, category, raw_text,
    language, latitude, longitude, cluster_id. Returns (cluster_id, matched_report)
    or (None, None) if nothing matches.
    """
    is_english = candidate.get("language", "en") == "en"
    candidate_tokens = _tokenize(candidate["raw_text"]) if is_english else set()
    candidate_landmark = _mentioned_landmark(candidate["raw_text"], candidate["ward"])

    best_match = None
    best_score = -1.0

    for report in existing_reports:
        if report["id"] == candidate.get("id"):
            continue
        if report["ward"] != candidate["ward"] or report["category"] != candidate["category"]:
            continue

        distance = haversine_meters(
            candidate.get("latitude"), candidate.get("longitude"),
            report.get("latitude"), report.get("longitude"),
        )
        geo_match = distance <= GEO_RADIUS_METERS

        landmark_match = (
            candidate_landmark is not None
            and candidate_landmark == _mentioned_landmark(report["raw_text"], report["ward"])
        )

        text_similarity = 0.0
        if is_english and report.get("language", "en") == "en":
            text_similarity = _jaccard(candidate_tokens, _tokenize(report["raw_text"]))
        text_match = text_similarity >= TEXT_SIMILARITY_THRESHOLD

        if not (geo_match or landmark_match or text_match):
            continue

        score = text_similarity + (0.5 if landmark_match else 0) + (0.25 if geo_match else 0)
        if score > best_score:
            best_score = score
            best_match = report

    if best_match is None:
        return None, None
    cluster_id = best_match["cluster_id"] or new_cluster_id()
    return cluster_id, best_match


def recompute_cluster_urgency(db, cluster_id):
    from . import urgency as urgency_module

    rows = db.execute(
        "SELECT id, category, raw_text, language FROM grievances WHERE cluster_id = ?",
        (cluster_id,),
    ).fetchall()
    if not rows:
        return
    member_count = len(rows)

    # Score every member (not an arbitrary "representative") and keep the worst
    # case — if even one report in the cluster describes a live wire or an
    # accident, the whole cluster must inherit that urgency, not average it away.
    result = None
    for row in rows:
        candidate_result = urgency_module.compute_urgency(
            row["category"], row["raw_text"], member_count, row["language"]
        )
        if result is None or candidate_result["score"] > result["score"]:
            result = candidate_result
    # Deliberately does NOT touch updated_at: that column tracks status
    # changes (used for resolution-time reporting), and recomputing urgency
    # after a cluster merge is not a status change. Stamping it to "now" here
    # previously corrupted resolution-time stats for every resolved grievance
    # that happened to be in a cluster.
    db.execute(
        """UPDATE grievances
           SET affected_count = ?, urgency_score = ?, urgency_level = ?,
               urgency_reasons = ?, safety_risk = ?
           WHERE cluster_id = ?""",
        (
            member_count, result["score"], result["level"],
            json.dumps(result["reasons"]), int(result["safety_risk"]), cluster_id,
        ),
    )


def find_cluster_match_for_new(db, candidate):
    rows = db.execute(
        """SELECT id, ward, category, raw_text, language, latitude, longitude, cluster_id
           FROM grievances
           WHERE ward = ? AND category = ?
             AND julianday('now') - julianday(created_at) <= ?""",
        (candidate["ward"], candidate["category"], RECENCY_WINDOW_DAYS),
    ).fetchall()
    existing = [dict(row) for row in rows]
    return find_cluster_match(candidate, existing)


def recluster_all(db):
    rows = db.execute(
        """SELECT id, ward, category, raw_text, language, latitude, longitude,
                  cluster_id, created_at
           FROM grievances ORDER BY created_at ASC"""
    ).fetchall()

    processed = []
    touched_clusters = set()

    for row in rows:
        candidate = dict(row)
        cluster_id, matched = find_cluster_match(candidate, processed)
        if cluster_id:
            if matched["cluster_id"] is None:
                db.execute("UPDATE grievances SET cluster_id = ? WHERE id = ?", (cluster_id, matched["id"]))
                matched["cluster_id"] = cluster_id
            db.execute("UPDATE grievances SET cluster_id = ? WHERE id = ?", (cluster_id, candidate["id"]))
            candidate["cluster_id"] = cluster_id
            touched_clusters.add(cluster_id)
        processed.append(candidate)

    db.commit()
    for cluster_id in touched_clusters:
        recompute_cluster_urgency(db, cluster_id)
    db.commit()
    return touched_clusters
