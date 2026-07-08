import json
import random
from datetime import datetime, timedelta

from faker import Faker

from ..clustering import recluster_all
from ..urgency import compute_urgency
from .templates_text import render_text
from .wards import WARD_NAMES, jitter_coordinates, landmark_coordinates, random_landmark

fake = Faker("en_IN")

CATEGORY_WEIGHTS = {
    "roads_infra": 20, "streetlight": 15, "water_supply": 15, "garbage": 15,
    "drainage": 12, "health_hazard": 10, "electrical_hazard": 6, "noise": 5, "other": 2,
}
LANGUAGE_CHOICES = ["en", "bn", "hi"]
LANGUAGE_WEIGHTS = [85, 10, 5]
STATUS_CHOICES = ["resolved", "in_progress", "acknowledged", "submitted", "rejected"]
STATUS_WEIGHTS = [38, 24, 20, 15, 3]

# Planted duplicate storms so the clustering feature has real signal to find —
# see Peoples_Priorities_Build_Plan.pdf section 8 (Synthetic Data Strategy).
PLANTED_STORMS = [
    {"ward": "Salt Lake", "category": "streetlight", "count": 35},
    {"ward": "Behala", "category": "water_supply", "count": 25},
    {"ward": "Shyambazar", "category": "garbage", "count": 20},
]

# A handful of small "critical storms" — repeated severe reports at one landmark
# — so urgency scoring visibly spans the full low->critical range in the demo
# (via category severity + risk keywords + the cluster affected-count bonus),
# and so officials see duplicate clustering apply to genuinely dangerous issues
# too, not just potholes and garbage.
PLANTED_CRITICAL_INCIDENTS = [
    {
        "ward": "New Town",
        "category": "electrical_hazard",
        "count": 6,
        "variants": [
            "An exposed live wire near {landmark} caught fire and nearly electrocuted a passer-by — "
            "extremely dangerous, children walk past here on the way to school every morning. This has "
            "been going on for 8 days.",
            "There is a live wire sparking and catching fire near {landmark}, right next to where children "
            "wait for the school bus. Reported multiple times over the last 9 days with no action.",
            "Urgent: a live wire near {landmark} burst into fire yesterday. Children study at the school "
            "right next to it. This is the third such fire in 8 days.",
        ],
    },
    {
        "ward": "Jadavpur",
        "category": "roads_infra",
        "count": 5,
        "variants": [
            "The same pothole near {landmark} caused a fatal accident — a child died on the spot. Residents "
            "have complained about it for 8 days and are demanding urgent, immediate repair.",
            "Another accident at the pothole near {landmark} today, a child was badly hurt. We have been "
            "reporting this for 9 days, urgent action needed immediately.",
            "This pothole near {landmark} has now caused a second fatal accident in 8 days. A child died. "
            "Immediate, urgent repair is needed before more lives are lost.",
        ],
    },
    {
        "ward": "Tollygunge",
        "category": "health_hazard",
        "count": 5,
        "variants": [
            "Three children near {landmark} have been hospitalised with dengue over the past 8 days, "
            "stagnant water everywhere is breeding mosquitoes — an outbreak is starting, please act urgently.",
            "A dengue outbreak is spreading near {landmark}, several children hospitalised in the last 9 "
            "days. Stagnant water breeding mosquitoes everywhere, urgent fumigation needed.",
            "More children have caught dengue near {landmark} in the past 8 days — this is becoming an "
            "outbreak. Stagnant water needs urgent clearing.",
        ],
    },
    {
        "ward": "Garia",
        "category": "electrical_hazard",
        "count": 5,
        "variants": [
            "A transformer near {landmark} caught fire and is now a live wire hazard sparking right next to "
            "a school gate — children were nearby, this is an emergency. Happening for 8 days.",
            "The transformer near {landmark} keeps catching fire, live wires hanging dangerously close to "
            "where children play. Emergency repair needed, reported over 9 days.",
            "Live wires from the damaged transformer near {landmark} caught fire again today, right by the "
            "school gate. Emergency — this has continued for 8 days.",
        ],
    },
]

STATUS_SEQUENCE = ["submitted", "acknowledged", "in_progress", "resolved"]
STATUS_NOTES = {
    "acknowledged": "Reviewed by ward office.",
    "in_progress": "Work order issued to field team.",
    "resolved": "Issue fixed and verified on-site.",
}


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _build_status_chain(created_at, final_status):
    chain = [("submitted", created_at, "Grievance received.")]
    if final_status == "rejected":
        rejected_at = created_at + timedelta(hours=random.uniform(4, 72))
        chain.append(("rejected", rejected_at, "Reviewed and closed — not actionable or a duplicate."))
        return chain, rejected_at

    final_index = STATUS_SEQUENCE.index(final_status)
    current_time = created_at
    for step in STATUS_SEQUENCE[1: final_index + 1]:
        current_time = current_time + timedelta(hours=random.uniform(6, 96))
        chain.append((step, current_time, STATUS_NOTES[step]))
    return chain, current_time


def _weighted_category():
    return random.choices(list(CATEGORY_WEIGHTS.keys()), weights=list(CATEGORY_WEIGHTS.values()), k=1)[0]


def _random_language():
    return random.choices(LANGUAGE_CHOICES, weights=LANGUAGE_WEIGHTS, k=1)[0]


def _random_status():
    return random.choices(STATUS_CHOICES, weights=STATUS_WEIGHTS, k=1)[0]


def _random_created_at(max_days_ago=90, min_days_ago=0):
    return datetime.now() - timedelta(days=random.uniform(min_days_ago, max_days_ago))


def _build_row(ward, category, language, created_at, landmark=None, text_override=None):
    landmark = landmark or random_landmark(ward)
    text = text_override.format(landmark=landmark) if text_override else render_text(category, landmark, language)
    lat, lng = landmark_coordinates(ward, landmark)
    lat, lng = jitter_coordinates(lat, lng, meters=40)

    urgency = compute_urgency(category, text, affected_count=1, language=language)
    status = _random_status()
    chain, last_time = _build_status_chain(created_at, status)
    updated_at = last_time if status != "submitted" else created_at

    summary = text if len(text) <= 140 else text[:137] + "..."

    return {
        "citizen_name": fake.name(),
        "citizen_phone": fake.phone_number(),
        "raw_text": text,
        "language": language,
        "category": category,
        "summary": summary,
        "urgency": urgency,
        "status": status,
        "ward": ward,
        "latitude": lat,
        "longitude": lng,
        "affected_count": 1,
        "created_at": _iso(created_at),
        "updated_at": _iso(updated_at),
        "status_chain": [(s, _iso(t), note) for s, t, note in chain],
    }


def _insert_row(db, row):
    cursor = db.execute(
        """INSERT INTO grievances
           (ticket_id, citizen_name, citizen_phone, raw_text, language, category, summary,
            urgency_score, urgency_level, urgency_reasons, status, ward, latitude, longitude,
            affected_count, safety_risk, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "PENDING", row["citizen_name"], row["citizen_phone"], row["raw_text"], row["language"],
            row["category"], row["summary"], row["urgency"]["score"], row["urgency"]["level"],
            json.dumps(row["urgency"]["reasons"]), row["status"], row["ward"], row["latitude"], row["longitude"],
            row["affected_count"], int(row["urgency"]["safety_risk"]), row["created_at"], row["updated_at"],
        ),
    )
    grievance_id = cursor.lastrowid
    db.execute("UPDATE grievances SET ticket_id = ? WHERE id = ?", (f"PP-{grievance_id:06d}", grievance_id))
    for status, changed_at, note in row["status_chain"]:
        db.execute(
            "INSERT INTO status_history (grievance_id, status, note, changed_at) VALUES (?, ?, ?, ?)",
            (grievance_id, status, note, changed_at),
        )
    return grievance_id


def generate(db, n=330):
    rows = []

    for storm in PLANTED_STORMS:
        landmark = random_landmark(storm["ward"])
        for _ in range(storm["count"]):
            created_at = _random_created_at(max_days_ago=20, min_days_ago=0)
            rows.append(_build_row(storm["ward"], storm["category"], _random_language(), created_at, landmark=landmark))

    for incident in PLANTED_CRITICAL_INCIDENTS:
        landmark = random_landmark(incident["ward"])
        for _ in range(incident["count"]):
            created_at = _random_created_at(max_days_ago=14, min_days_ago=0)
            variant = random.choice(incident["variants"])
            rows.append(_build_row(
                incident["ward"], incident["category"], "en", created_at,
                landmark=landmark, text_override=variant,
            ))

    for _ in range(max(0, n - len(rows))):
        ward = random.choice(WARD_NAMES)
        created_at = _random_created_at(max_days_ago=90)
        rows.append(_build_row(ward, _weighted_category(), _random_language(), created_at))

    random.shuffle(rows)
    for row in rows:
        _insert_row(db, row)
    db.commit()

    touched_clusters = recluster_all(db)
    return _summarize(db, len(rows), touched_clusters)


def _summarize(db, total, touched_clusters):
    def counts(column):
        return {
            r[column]: r["n"]
            for r in db.execute(f"SELECT {column}, COUNT(*) AS n FROM grievances GROUP BY {column}").fetchall()
        }

    cluster_sizes = db.execute(
        """SELECT cluster_id, COUNT(*) AS n FROM grievances
           WHERE cluster_id IS NOT NULL GROUP BY cluster_id ORDER BY n DESC LIMIT 10"""
    ).fetchall()

    return {
        "total": total,
        "by_ward": counts("ward"),
        "by_category": counts("category"),
        "by_status": counts("status"),
        "by_urgency_level": counts("urgency_level"),
        "cluster_count": len(touched_clusters),
        "clustered_rows": db.execute(
            "SELECT COUNT(*) AS n FROM grievances WHERE cluster_id IS NOT NULL"
        ).fetchone()["n"],
        "top_clusters": [(r["cluster_id"], r["n"]) for r in cluster_sizes],
    }
