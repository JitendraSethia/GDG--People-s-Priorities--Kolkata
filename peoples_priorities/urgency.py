import re

from .seed_data.categories import CATEGORIES, RISK_KEYWORDS

_DURATION_PATTERN = re.compile(r"(\d+)\s*(day|days|week|weeks)", re.IGNORECASE)


def _category_severity(category):
    return CATEGORIES.get(category, CATEGORIES["other"])["base_severity"]


def _keyword_bonus(text_lower):
    total = 0
    safety_risk = False
    hits = []
    for group in RISK_KEYWORDS:
        term = next((t for t in group["terms"] if t in text_lower), None)
        if term:
            total += group["weight"]
            safety_risk = safety_risk or group["safety_risk"]
            hits.append((group["weight"], term))
    return min(total, 30), safety_risk, hits


def _affected_bonus(affected_count):
    if affected_count >= 50:
        return 20
    if affected_count >= 30:
        return 15
    if affected_count >= 15:
        return 10
    if affected_count >= 5:
        return 5
    return 0


def extract_recency_days(text_lower):
    match = _DURATION_PATTERN.search(text_lower)
    if match:
        amount = int(match.group(1))
        return amount * 7 if match.group(2).startswith("week") else amount
    if "month" in text_lower:
        return 30
    if re.search(r"\ba week\b", text_lower):
        return 7
    if re.search(r"\ba day\b|\byesterday\b", text_lower):
        return 1
    return None


def _recency_bonus(days):
    if days is None:
        return 0
    if days >= 8:
        return 10
    if days >= 4:
        return 6
    if days >= 2:
        return 3
    return 0


def _level_for(score):
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def compute_urgency(category, raw_text, affected_count=1, language="en"):
    text_lower = (raw_text or "").lower()

    severity = _category_severity(category)
    label = CATEGORIES.get(category, CATEGORIES["other"])["label"]
    reasons = [f"{label} carries a baseline severity of {severity}/40"]

    keyword_score, safety_risk, hits = _keyword_bonus(text_lower)
    for weight, term in sorted(hits, key=lambda h: -h[0]):
        reasons.append(f"Mentions '{term}' (+{weight})")

    affected_score = _affected_bonus(affected_count)
    if affected_score:
        reasons.append(f"Affects an estimated {affected_count} residents (+{affected_score})")

    recency_days = extract_recency_days(text_lower)
    recency_score = _recency_bonus(recency_days)
    if recency_score:
        reasons.append(f"Unresolved for {recency_days} days (+{recency_score})")

    score = max(0, min(100, severity + keyword_score + affected_score + recency_score))

    return {
        "score": score,
        "level": _level_for(score),
        "reasons": reasons,
        "safety_risk": safety_risk,
    }
