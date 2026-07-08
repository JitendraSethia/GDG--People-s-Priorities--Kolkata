import random

WARDS = {
    "Salt Lake": {
        "centroid": (22.5805, 88.4172),
        "landmarks": [
            "Sector 1 Market", "Karunamoyee Bus Stand", "Central Park",
            "City Centre 1", "Sector 5 IT Park", "AJ Block Crossing",
        ],
    },
    "New Town": {
        "centroid": (22.5849, 88.4642),
        "landmarks": [
            "Eco Park Gate 1", "Akankha More", "DLF IT Park",
            "Unitech More", "City Centre 2", "Biswa Bangla Sarani",
        ],
    },
    "Behala": {
        "centroid": (22.4986, 88.3151),
        "landmarks": [
            "Behala Chowrasta", "Silpara Crossing", "Sakher Bazar",
            "Thakurpukur More", "Parnashree", "James Long Sarani",
        ],
    },
    "Shyambazar": {
        "centroid": (22.5978, 88.3714),
        "landmarks": [
            "Shyambazar Five Point Crossing", "Kashi Bose Lane",
            "Hatibagan Market", "R.G. Kar Road", "Bagbazar Ghat", "Vivekananda Road",
        ],
    },
    "Jadavpur": {
        "centroid": (22.4990, 88.3712),
        "landmarks": [
            "Jadavpur 8B Bus Stand", "Baghajatin Station Road", "Jadavpur University Gate",
            "Ramgarh Crossing", "Sulekha More", "Regent Estate",
        ],
    },
    "Ballygunge": {
        "centroid": (22.5300, 88.3667),
        "landmarks": [
            "Gariahat Crossing", "Ballygunge Phanri", "Deshapriya Park",
            "Rashbehari Crossing", "Lake Market", "Sarat Bose Road",
        ],
    },
    "Tollygunge": {
        "centroid": (22.5008, 88.3426),
        "landmarks": [
            "Tollygunge Phanri", "Karunamoyee More South", "Netaji Nagar",
            "Ajoy Nagar", "Nepal Bhattacharya Street", "Tollygunge Metro Crossing",
        ],
    },
    "Garia": {
        "centroid": (22.4599, 88.3928),
        "landmarks": [
            "Garia Station Road", "Narendrapur More", "Kamalgazi Crossing",
            "Boral Main Road", "Garia Bazar", "Panchasayar",
        ],
    },
}

WARD_NAMES = list(WARDS.keys())


def landmark_coordinates(ward, landmark):
    lat, lng = WARDS[ward]["centroid"]
    index = WARDS[ward]["landmarks"].index(landmark)
    lat_offset = ((index % 3) - 1) * 0.006
    lng_offset = ((index // 3) - 1) * 0.006
    return round(lat + lat_offset, 6), round(lng + lng_offset, 6)


def jitter_coordinates(lat, lng, meters=40):
    delta = meters / 111_000
    return (
        round(lat + random.uniform(-delta, delta), 6),
        round(lng + random.uniform(-delta, delta), 6),
    )


def random_landmark(ward):
    return random.choice(WARDS[ward]["landmarks"])


def nearest_ward(lat, lng):
    """Rule-based ward lookup from a citizen's GPS coordinates — nearest ward
    centroid wins. Replaces asking citizens to know their official ward name.
    """
    from ..clustering import haversine_meters

    best_ward, best_distance = None, float("inf")
    for ward, info in WARDS.items():
        clat, clng = info["centroid"]
        distance = haversine_meters(lat, lng, clat, clng)
        if distance < best_distance:
            best_distance = distance
            best_ward = ward
    return best_ward, best_distance
