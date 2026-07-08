import random

TEMPLATES = {
    "electrical_hazard": [
        "There is a live wire hanging near {landmark}, very dangerous for pedestrians.",
        "An exposed electric wire near {landmark} has been sparking since {duration}.",
        "The transformer near {landmark} is making loud noises and sparking, worried about a fire.",
    ],
    "water_supply": [
        "No water supply near {landmark} for {duration}. The whole neighbourhood is affected.",
        "Sewage is overflowing onto the street near {landmark}, terrible smell for {duration}.",
        "A water pipeline burst near {landmark}, wasting water for {duration}.",
    ],
    "health_hazard": [
        "Stagnant water near {landmark} is breeding mosquitoes, worried about a dengue outbreak.",
        "Garbage rotting near {landmark} for {duration}, foul smell and health risk for children.",
        "A stray dog near {landmark} bit someone, residents are scared to walk there.",
    ],
    "roads_infra": [
        "A big pothole near {landmark} caused an accident yesterday.",
        "The road near {landmark} has caved in, very risky for two-wheelers at night.",
        "The footpath near {landmark} is broken, elderly people keep falling.",
    ],
    "streetlight": [
        "The streetlight near {landmark} has been off for {duration}, the road is pitch dark at night.",
        "No street light near {landmark} for {duration}, women feel unsafe walking home.",
    ],
    "drainage": [
        "The drain near {landmark} is blocked, waterlogging every time it rains.",
        "Severe waterlogging near {landmark} for {duration}, cannot walk on the road.",
    ],
    "garbage": [
        "The garbage bin near {landmark} is overflowing for {duration}, nobody has collected it.",
        "Waste has not been collected near {landmark} for {duration}, piling up on the street.",
    ],
    "noise": [
        "Loudspeaker noise near {landmark} every night, unable to sleep.",
        "Construction noise near {landmark} starting very early morning for {duration}.",
    ],
    "other": [
        "There is a civic issue near {landmark} that needs attention, ongoing for {duration}.",
    ],
}

DURATIONS = ["2 days", "3 days", "5 days", "a week", "10 days", "2 weeks", "since last month"]

BENGALI_SAMPLES = {
    "streetlight": "{landmark}-এর কাছে রাস্তার আলো {duration} ধরে বন্ধ, রাতে খুব অন্ধকার থাকে।",
    "water_supply": "{landmark}-এর কাছে {duration} ধরে জল সরবরাহ নেই, পুরো এলাকা সমস্যায় আছে।",
    "garbage": "{landmark}-এর কাছে আবর্জনার স্তূপ জমে আছে {duration} ধরে, দুর্গন্ধ ছড়াচ্ছে।",
    "drainage": "{landmark}-এর কাছে জল জমে আছে {duration} ধরে, রাস্তা দিয়ে হাঁটা যাচ্ছে না।",
}

HINDI_SAMPLES = {
    "streetlight": "{landmark} के पास स्ट्रीट लाइट {duration} से बंद है, रात में बहुत अंधेरा रहता है।",
    "water_supply": "{landmark} के पास {duration} से पानी की सप्लाई नहीं आ रही है, पूरा इलाका परेशान है।",
    "garbage": "{landmark} के पास {duration} से कचरा जमा है, बदबू फैल रही है।",
    "roads_infra": "{landmark} के पास सड़क में बड़ा गड्ढा है, कल एक दुर्घटना हो गई।",
}


def render_text(category, landmark, language="en"):
    duration = random.choice(DURATIONS)
    if language == "bn" and category in BENGALI_SAMPLES:
        return BENGALI_SAMPLES[category].format(landmark=landmark, duration=duration)
    if language == "hi" and category in HINDI_SAMPLES:
        return HINDI_SAMPLES[category].format(landmark=landmark, duration=duration)
    template = random.choice(TEMPLATES.get(category, TEMPLATES["other"]))
    return template.format(landmark=landmark, duration=duration)
