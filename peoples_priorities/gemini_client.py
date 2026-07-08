import json
import re

from flask import current_app

from .seed_data.categories import CATEGORY_CODES, RISK_KEYWORDS, category_label, guess_category
from .urgency import extract_recency_days

_BENGALI_RANGE = re.compile(r"[ঀ-৿]")
_DEVANAGARI_RANGE = re.compile(r"[ऀ-ॿ]")

_AFFECTED_COUNT_PATTERN = re.compile(
    r"(\d+)\s*(people|residents|families|households|of us|persons)", re.IGNORECASE
)
_CROWD_PHRASES = ["whole neighbourhood", "whole neighborhood", "entire street", "many of us", "everyone here"]

_SYSTEM_PROMPT = f"""You are a civic grievance triage assistant for a citizen-to-government platform in
Kolkata, India. Classify the citizen's complaint below.

Allowed category codes (choose exactly one): {", ".join(CATEGORY_CODES)}

Return a JSON object with these fields:
- category: one of the allowed category codes above
- summary: a clean one-sentence English summary (max 140 characters)
- detected_language: "en", "bn", or "hi"
- translated_text: the complaint translated to English (or the original text if already English)
- safety_risk: true if there is an immediate safety/health danger (fire, exposed live wire, accident,
  disease outbreak), else false
- affected_count_estimate: your best-guess integer number of people affected (default 1 if unclear)
- recency_days: integer number of days the issue has reportedly persisted (0 if not mentioned)
"""


def detect_language(text):
    if _BENGALI_RANGE.search(text):
        return "bn"
    if _DEVANAGARI_RANGE.search(text):
        return "hi"
    return "en"


def _estimate_affected_count(text_lower):
    match = _AFFECTED_COUNT_PATTERN.search(text_lower)
    if match:
        return max(1, int(match.group(1)))
    if any(phrase in text_lower for phrase in _CROWD_PHRASES):
        return 15
    return 1


def _safety_risk_from_keywords(text_lower):
    return any(
        group["safety_risk"] and any(term in text_lower for term in group["terms"])
        for group in RISK_KEYWORDS
    )


def rule_based_classify(raw_text, language_hint=None):
    language = language_hint or detect_language(raw_text)
    text_lower = raw_text.lower()
    category = guess_category(text_lower)
    recency_days = extract_recency_days(text_lower) or 0

    translated_text = raw_text
    translation_note = None
    if language != "en":
        translation_note = "Translation unavailable in offline mode."

    summary = raw_text.strip()
    if len(summary) > 140:
        summary = summary[:137] + "..."

    return {
        "category": category,
        "category_label": category_label(category),
        "summary": summary,
        "detected_language": language,
        "translated_text": translated_text,
        "translation_note": translation_note,
        "safety_risk": _safety_risk_from_keywords(text_lower),
        "affected_count_estimate": _estimate_affected_count(text_lower),
        "recency_days": recency_days,
        "source": "rule_based",
    }


def _call_gemini(raw_text, config):
    from google import genai
    from google.genai import types

    # Explicit timeout so a slow/hanging Gemini call during a live demo fails
    # fast into the rule-based fallback rather than stalling the citizen's
    # submission indefinitely.
    http_options = types.HttpOptions(timeout=12000)

    if config["USE_VERTEX_AI"]:
        client = genai.Client(
            vertexai=True,
            project=config["GOOGLE_CLOUD_PROJECT"],
            location=config["GOOGLE_CLOUD_LOCATION"],
            http_options=http_options,
        )
    else:
        client = genai.Client(api_key=config["GEMINI_API_KEY"], http_options=http_options)

    response_schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": CATEGORY_CODES},
            "summary": {"type": "string"},
            "detected_language": {"type": "string", "enum": ["en", "bn", "hi"]},
            "translated_text": {"type": "string"},
            "safety_risk": {"type": "boolean"},
            "affected_count_estimate": {"type": "integer"},
            "recency_days": {"type": "integer"},
        },
        "required": [
            "category", "summary", "detected_language", "translated_text",
            "safety_risk", "affected_count_estimate", "recency_days",
        ],
    }

    response = client.models.generate_content(
        model=config["GEMINI_MODEL"],
        contents=f"{_SYSTEM_PROMPT}\n\nComplaint:\n{raw_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )
    return json.loads(response.text)


def classify_grievance(raw_text, language_hint=None):
    config = current_app.config
    if not config.get("GEMINI_ENABLED"):
        return rule_based_classify(raw_text, language_hint)

    try:
        result = _call_gemini(raw_text, config)
        result["category_label"] = category_label(result["category"])
        result["translation_note"] = None
        result["source"] = "gemini"
        return result
    except Exception as exc:  # noqa: BLE001 - any failure must fall back, not crash the submission
        current_app.logger.warning("Gemini classification failed, using rule-based fallback: %s", exc)
        return rule_based_classify(raw_text, language_hint)
