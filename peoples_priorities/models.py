import json
import uuid

from .seed_data.categories import CATEGORIES, category_label

VALID_STATUSES = ["submitted", "acknowledged", "in_progress", "resolved", "rejected"]
OPEN_STATUSES = ["submitted", "acknowledged", "in_progress"]


def serialize_grievance(row, member_count=None):
    d = dict(row)
    d["urgency_reasons"] = json.loads(d["urgency_reasons"]) if d.get("urgency_reasons") else []
    d["safety_risk"] = bool(d.get("safety_risk", 0))
    d["category_label"] = category_label(d["category"])
    if member_count is not None:
        d["member_count"] = member_count
        d["is_cluster"] = member_count > 1
    return d


def _build_filters(ward=None, category=None, status=None, urgency_level=None, min_urgency=None, q=None, alias="g"):
    clauses = []
    params = []
    if ward:
        clauses.append(f"{alias}.ward = ?")
        params.append(ward)
    if category:
        clauses.append(f"{alias}.category = ?")
        params.append(category)
    if status:
        clauses.append(f"{alias}.status = ?")
        params.append(status)
    if urgency_level:
        clauses.append(f"{alias}.urgency_level = ?")
        params.append(urgency_level)
    if min_urgency is not None:
        clauses.append(f"{alias}.urgency_score >= ?")
        params.append(min_urgency)
    if q:
        clauses.append(f"({alias}.raw_text LIKE ? OR {alias}.summary LIKE ? OR {alias}.ticket_id LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    return clauses, params


_SORT_COLUMNS = {
    "urgency_desc": "g.urgency_score DESC, g.created_at DESC",
    "urgency_asc": "g.urgency_score ASC, g.created_at DESC",
    "newest": "g.created_at DESC",
    "oldest": "g.created_at ASC",
}


def list_grievances(db, ward=None, category=None, status=None, urgency_level=None,
                     min_urgency=None, q=None, collapse_clusters=True,
                     sort="urgency_desc", page=1, page_size=50):
    clauses, params = _build_filters(ward, category, status, urgency_level, min_urgency, q)
    order_by = _SORT_COLUMNS.get(sort, _SORT_COLUMNS["urgency_desc"])
    offset = (page - 1) * page_size

    if collapse_clusters:
        where_sql = " AND ".join(clauses) if clauses else "1=1"
        base = f"""
            FROM grievances g
            LEFT JOIN (
                SELECT cluster_id, COUNT(*) AS member_count, MIN(id) AS representative_id
                FROM grievances WHERE cluster_id IS NOT NULL GROUP BY cluster_id
            ) c ON g.cluster_id = c.cluster_id
            WHERE (g.cluster_id IS NULL OR g.id = c.representative_id) AND {where_sql}
        """
        count_row = db.execute(f"SELECT COUNT(*) AS n {base}", params).fetchone()
        rows = db.execute(
            f"SELECT g.*, COALESCE(c.member_count, 1) AS member_count {base} "
            f"ORDER BY {order_by} LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        results = [serialize_grievance(r, member_count=r["member_count"]) for r in rows]
    else:
        where_sql = " AND ".join(clauses) if clauses else "1=1"
        count_row = db.execute(f"SELECT COUNT(*) AS n FROM grievances g WHERE {where_sql}", params).fetchone()
        rows = db.execute(
            f"SELECT g.* FROM grievances g WHERE {where_sql} ORDER BY {order_by} LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        results = [serialize_grievance(r) for r in rows]

    return {"count": count_row["n"], "page": page, "page_size": page_size, "results": results}


def get_grievance_by_ticket(db, ticket_id):
    row = db.execute("SELECT * FROM grievances WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if row is None:
        return None
    grievance = dict(row)
    grievance["cluster_members"] = []
    if grievance["cluster_id"]:
        member_rows = db.execute(
            "SELECT ticket_id, citizen_name, raw_text, created_at FROM grievances "
            "WHERE cluster_id = ? AND ticket_id != ? ORDER BY created_at ASC",
            (grievance["cluster_id"], ticket_id),
        ).fetchall()
        grievance["cluster_members"] = [dict(r) for r in member_rows]

    history_rows = db.execute(
        "SELECT status, note, changed_at FROM status_history WHERE grievance_id = ? ORDER BY changed_at ASC",
        (grievance["id"],),
    ).fetchall()
    grievance["status_history"] = [dict(r) for r in history_rows]

    return serialize_grievance(grievance, member_count=len(grievance["cluster_members"]) + 1)


def add_status_history(db, grievance_id, status, note=None):
    db.execute(
        "INSERT INTO status_history (grievance_id, status, note) VALUES (?, ?, ?)",
        (grievance_id, status, note),
    )


def insert_grievance(db, *, citizen_name, citizen_phone, raw_text, language, category,
                      summary, urgency, ward, latitude, longitude, cluster_id, affected_count):
    placeholder_ticket = f"TMP-{uuid.uuid4().hex[:10]}"
    cursor = db.execute(
        """INSERT INTO grievances
           (ticket_id, citizen_name, citizen_phone, raw_text, language, category, summary,
            urgency_score, urgency_level, urgency_reasons, ward, latitude, longitude,
            cluster_id, affected_count, safety_risk)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            placeholder_ticket, citizen_name, citizen_phone, raw_text, language, category, summary,
            urgency["score"], urgency["level"], json.dumps(urgency["reasons"]), ward, latitude, longitude,
            cluster_id, affected_count, int(urgency["safety_risk"]),
        ),
    )
    grievance_id = cursor.lastrowid
    ticket_id = f"PP-{grievance_id:06d}"
    db.execute("UPDATE grievances SET ticket_id = ? WHERE id = ?", (ticket_id, grievance_id))
    add_status_history(db, grievance_id, "submitted", "Grievance received.")
    db.commit()
    return ticket_id, grievance_id


def set_photo_path(db, grievance_id, photo_path):
    db.execute(
        "UPDATE grievances SET photo_path = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
        (photo_path, grievance_id),
    )
    db.commit()


def update_status(db, ticket_id, status, note=None):
    row = db.execute("SELECT id FROM grievances WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if row is None:
        return False
    db.execute(
        "UPDATE grievances SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
        (status, row["id"]),
    )
    add_status_history(db, row["id"], status, note)
    db.commit()
    return True


def get_stats(db, ward=None, days=90):
    clauses, params = _build_filters(ward=ward)
    where_sql = " AND ".join(clauses) if clauses else "1=1"

    total_open = db.execute(
        f"SELECT COUNT(*) AS n FROM grievances g WHERE {where_sql} AND status IN ({','.join('?' * len(OPEN_STATUSES))})",
        params + OPEN_STATUSES,
    ).fetchone()["n"]

    total_resolved = db.execute(
        f"SELECT COUNT(*) AS n FROM grievances g WHERE {where_sql} AND status = 'resolved'", params
    ).fetchone()["n"]

    avg_resolution_hours = db.execute(
        f"""SELECT AVG((julianday(updated_at) - julianday(created_at)) * 24) AS hours
            FROM grievances g WHERE {where_sql} AND status = 'resolved'""",
        params,
    ).fetchone()["hours"]

    by_urgency_level = {
        r["urgency_level"]: r["n"]
        for r in db.execute(
            f"SELECT urgency_level, COUNT(*) AS n FROM grievances g WHERE {where_sql} GROUP BY urgency_level", params
        ).fetchall()
    }
    by_category = {
        r["category"]: r["n"]
        for r in db.execute(
            f"SELECT category, COUNT(*) AS n FROM grievances g WHERE {where_sql} GROUP BY category", params
        ).fetchall()
    }
    by_ward = {
        r["ward"]: r["n"]
        for r in db.execute(
            f"SELECT ward, COUNT(*) AS n FROM grievances g WHERE {where_sql} GROUP BY ward", params
        ).fetchall()
    }

    trend_rows = db.execute(
        f"""SELECT date(created_at) AS day, COUNT(*) AS n FROM grievances g
            WHERE {where_sql} AND julianday('now') - julianday(created_at) <= ?
            GROUP BY day ORDER BY day ASC""",
        params + [days],
    ).fetchall()

    return {
        "total_open": total_open,
        "total_resolved": total_resolved,
        "avg_resolution_hours": round(avg_resolution_hours, 1) if avg_resolution_hours else None,
        "by_urgency_level": by_urgency_level,
        "by_category": by_category,
        "by_ward": by_ward,
        "trend": [{"date": r["day"], "count": r["n"]} for r in trend_rows],
    }


def get_ward_planning(db, ward, weeks=12):
    days = weeks * 7
    category_rows = db.execute(
        """SELECT category, COUNT(*) AS n, AVG(urgency_score) AS avg_urgency
           FROM grievances WHERE ward = ? GROUP BY category ORDER BY n DESC""",
        (ward,),
    ).fetchall()

    top_issues = []
    for row in category_rows[:3]:
        first_half = db.execute(
            """SELECT COUNT(*) AS n FROM grievances
               WHERE ward = ? AND category = ?
                 AND julianday('now') - julianday(created_at) BETWEEN ? AND ?""",
            (ward, row["category"], days / 2, days),
        ).fetchone()["n"]
        second_half = db.execute(
            """SELECT COUNT(*) AS n FROM grievances
               WHERE ward = ? AND category = ?
                 AND julianday('now') - julianday(created_at) < ?""",
            (ward, row["category"], days / 2),
        ).fetchone()["n"]
        if second_half > first_half:
            trend_direction = "rising"
        elif second_half < first_half:
            trend_direction = "falling"
        else:
            trend_direction = "flat"
        top_issues.append({
            "category": row["category"],
            "label": CATEGORIES.get(row["category"], CATEGORIES["other"])["label"],
            "count": row["n"],
            "avg_urgency": round(row["avg_urgency"], 1),
            "trend_direction": trend_direction,
        })

    trend_rows = db.execute(
        """SELECT strftime('%Y-W%W', created_at) AS period, COUNT(*) AS n
           FROM grievances
           WHERE ward = ? AND julianday('now') - julianday(created_at) <= ?
           GROUP BY period ORDER BY period ASC""",
        (ward, days),
    ).fetchall()

    cluster_rows = db.execute(
        """SELECT g.cluster_id, g.category, g.affected_count, g.urgency_score,
                  MAX(g.urgency_level) AS urgency_level,
                  MIN(g.summary) AS sample_summary, MIN(g.raw_text) AS sample_text
           FROM grievances g
           WHERE g.ward = ? AND g.cluster_id IS NOT NULL AND g.status != 'resolved'
           GROUP BY g.cluster_id
           ORDER BY g.affected_count DESC LIMIT 10""",
        (ward,),
    ).fetchall()

    return {
        "ward": ward,
        "top_issues": top_issues,
        "trend": [{"period": r["period"], "count": r["n"]} for r in trend_rows],
        "open_clusters": [
            {
                "cluster_id": r["cluster_id"],
                "category": r["category"],
                "category_label": category_label(r["category"]),
                "affected_count": r["affected_count"],
                "urgency_score": r["urgency_score"],
                "urgency_level": r["urgency_level"],
                "sample_summary": r["sample_summary"] or r["sample_text"],
            }
            for r in cluster_rows
        ],
    }


def get_completed(db, ward=None, category=None, days=90, page=1, page_size=20):
    clauses, params = _build_filters(ward=ward, category=category, alias="g")
    clauses.append("g.status = 'resolved'")
    clauses.append("julianday('now') - julianday(g.created_at) <= ?")
    params.append(days)
    where_sql = " AND ".join(clauses)
    offset = (page - 1) * page_size

    count_row = db.execute(f"SELECT COUNT(*) AS n FROM grievances g WHERE {where_sql}", params).fetchone()
    avg_row = db.execute(
        f"""SELECT AVG((julianday(g.updated_at) - julianday(g.created_at)) * 24) AS hours
            FROM grievances g WHERE {where_sql}""",
        params,
    ).fetchone()

    rows = db.execute(
        f"""SELECT g.ticket_id, g.category, g.ward, g.summary, g.raw_text, g.photo_path,
                   g.updated_at AS resolved_at,
                   (julianday(g.updated_at) - julianday(g.created_at)) * 24 AS resolution_hours
            FROM grievances g WHERE {where_sql}
            ORDER BY g.updated_at DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset],
    ).fetchall()

    return {
        "count": count_row["n"],
        "page": page,
        "page_size": page_size,
        "avg_resolution_hours": round(avg_row["hours"], 1) if avg_row["hours"] else None,
        "results": [
            {
                "ticket_id": r["ticket_id"],
                "category": r["category"],
                "category_label": category_label(r["category"]),
                "ward": r["ward"],
                "summary": r["summary"] or r["raw_text"],
                "photo_path": r["photo_path"],
                "resolved_at": r["resolved_at"],
                "resolution_hours": round(r["resolution_hours"], 1),
            }
            for r in rows
        ],
    }
