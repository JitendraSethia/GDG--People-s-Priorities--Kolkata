CATEGORIES = {
    "electrical_hazard": {
        "label": "Electrical Hazard",
        "base_severity": 40,
        "keywords": [
            "live wire", "exposed wire", "electric pole", "sparking",
            "transformer", "short circuit", "electric shock",
        ],
    },
    "water_supply": {
        "label": "Water Supply & Sewage",
        "base_severity": 35,
        "keywords": [
            "no water", "water supply", "sewage", "drain overflow",
            "pipeline burst", "contaminated water", "water shortage",
        ],
    },
    "health_hazard": {
        "label": "Public Health Hazard",
        "base_severity": 35,
        "keywords": [
            "dengue", "mosquito", "stagnant water", "outbreak",
            "garbage rotting", "foul smell", "stray dog", "rabid",
        ],
    },
    "roads_infra": {
        "label": "Roads & Infrastructure",
        "base_severity": 30,
        "keywords": [
            "pothole", "broken road", "road caved", "footpath damaged",
            "bridge crack", "manhole open", "road collapsed",
        ],
    },
    "streetlight": {
        "label": "Streetlight",
        "base_severity": 25,
        "keywords": ["streetlight", "street light", "dark street", "lamp post", "no light"],
    },
    "drainage": {
        "label": "Drainage & Waterlogging",
        "base_severity": 25,
        "keywords": ["waterlogging", "drain blocked", "flooding", "clogged drain"],
    },
    "garbage": {
        "label": "Garbage & Sanitation",
        "base_severity": 20,
        "keywords": ["garbage", "trash", "overflowing bin", "waste not collected", "dustbin"],
    },
    "noise": {
        "label": "Noise & Nuisance",
        "base_severity": 10,
        "keywords": ["loudspeaker", "noise", "construction noise", "loud music"],
    },
    "other": {
        "label": "Other",
        "base_severity": 10,
        "keywords": [],
    },
}

CATEGORY_CODES = list(CATEGORIES.keys())

# Ordered strongest-first; each group's terms are checked against lowercased
# grievance text. `safety_risk` groups drive the safety_risk flag shown to
# officials, independent of the numeric bonus they contribute.
RISK_KEYWORDS = [
    {"weight": 20, "safety_risk": True,
     "terms": ["fire", "collapsed", "collapse", "gas leak", "building crack"]},
    {"weight": 15, "safety_risk": True,
     "terms": ["live wire", "electrocuted", "electric shock", "sparking wire"]},
    {"weight": 15, "safety_risk": True,
     "terms": ["accident", "died", "death", "killed", "hit by"]},
    {"weight": 10, "safety_risk": False,
     "terms": ["dengue", "outbreak", "malaria", "epidemic"]},
    {"weight": 10, "safety_risk": False,
     "terms": ["child", "children", "school", "elderly", "hospital"]},
    {"weight": 5, "safety_risk": False,
     "terms": ["urgent", "emergency", "immediately"]},
]


def category_label(category_code):
    return CATEGORIES.get(category_code, CATEGORIES["other"])["label"]


def guess_category(text_lower):
    best_code = "other"
    best_hits = 0
    for code, info in CATEGORIES.items():
        hits = sum(1 for kw in info["keywords"] if kw in text_lower)
        if hits > best_hits:
            best_hits = hits
            best_code = code
    return best_code
