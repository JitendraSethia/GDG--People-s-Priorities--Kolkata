import re
import unicodedata

# Letter categories (any script) + combining marks (Mn/Mc/Me) — Indic scripts
# like Bengali/Devanagari form ordinary letters out of a base consonant plus
# vowel-sign/virama combining marks, which Unicode classifies as Marks, not
# Letters. A letters-only check would reject nearly every real Bengali/Hindi
# name, which would directly undercut this app's multilingual support.
_ALLOWED_NAME_CATEGORIES = {"Ll", "Lu", "Lt", "Lm", "Lo", "Mn", "Mc", "Me"}
_ALLOWED_NAME_SEPARATORS = {" ", "'", "-"}

# Indian mobile numbers: optional +91/91/0 prefix, then 10 digits starting 6-9.
PHONE_PATTERN = re.compile(r"^(?:\+91|91|0)?[6-9]\d{9}$")


def is_valid_name(name):
    if not name:
        return True
    name = name.strip()
    if not name:
        return False
    return all(
        ch in _ALLOWED_NAME_SEPARATORS or unicodedata.category(ch) in _ALLOWED_NAME_CATEGORIES
        for ch in name
    )


def is_valid_phone(phone):
    return bool(PHONE_PATTERN.match(phone.strip().replace(" ", ""))) if phone else True
