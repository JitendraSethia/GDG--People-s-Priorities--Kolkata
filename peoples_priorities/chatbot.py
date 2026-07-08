import re

from . import models
from .seed_data.categories import category_label

_TICKET_PATTERN = re.compile(r"PP-\d{6}", re.IGNORECASE)

_STATUS_LABELS = {
    "submitted": "submitted and waiting to be reviewed",
    "acknowledged": "acknowledged by the officials",
    "in_progress": "being worked on",
    "resolved": "resolved",
    "rejected": "reviewed and closed",
}


def _extract_ticket(message, ticket_id):
    if ticket_id:
        return ticket_id.strip().upper()
    match = _TICKET_PATTERN.search(message or "")
    return match.group(0).upper() if match else None


def answer(db, message, ticket_id=None):
    ticket = _extract_ticket(message, ticket_id)
    if not ticket:
        return "Please share your ticket ID (looks like PP-000123) so I can check its status.", None

    grievance = models.get_grievance_by_ticket(db, ticket)
    if grievance is None:
        return f"I couldn't find a grievance with ticket ID {ticket}. Please double-check the ID.", None

    status_label = _STATUS_LABELS.get(grievance["status"], grievance["status"])
    reply_lines = [
        f"Ticket {grievance['ticket_id']} ({category_label(grievance['category'])}) "
        f"is currently {status_label}."
    ]

    history = grievance.get("status_history") or []
    if history and history[-1].get("note"):
        reply_lines.append(f"Latest update: {history[-1]['note']}")

    member_count = len(grievance.get("cluster_members") or []) + 1
    if member_count > 1:
        reply_lines.append(
            f"This is part of a wider issue affecting an estimated "
            f"{grievance['affected_count']} residents in {grievance['ward']}."
        )

    if "why" in (message or "").lower() and grievance.get("urgency_reasons"):
        reply_lines.append("Urgency reasons: " + "; ".join(grievance["urgency_reasons"]))

    return " ".join(reply_lines), grievance
