# pulse_data.py
# Fully hardcoded data source for Pulse.
# No AI required. No external market API required.
# This file contains:
# 1. Market rate data
# 2. Country / currency / cost-of-living data
# 3. Static FX rates
# 4. Working windows
# 5. Fully hardcoded narrative content for UI rendering

# =========================================================
# MARKET DATA
# =========================================================

MARKET_DATA = {
    "react-developer": {
        "label": "React Developer",
        "0-1": {"floor": 10, "median": 15, "target": 20, "demand": "High", "saturation": "High", "timing_signal": "Hold"},
        "1-3": {"floor": 18, "median": 25, "target": 35, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 30, "median": 45, "target": 60, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 55, "median": 75, "target": 100, "demand": "Medium", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 90, "median": 120, "target": 150, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
    },

    "full-stack-developer": {
        "label": "Full Stack Developer",
        "0-1": {"floor": 12, "median": 18, "target": 25, "demand": "High", "saturation": "High", "timing_signal": "Hold"},
        "1-3": {"floor": 22, "median": 32, "target": 45, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 40, "median": 55, "target": 75, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 65, "median": 90, "target": 120, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 100, "median": 140, "target": 180, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
    },

    "mobile-app-developer": {
        "label": "Mobile App Developer",
        "0-1": {"floor": 15, "median": 20, "target": 28, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "1-3": {"floor": 25, "median": 35, "target": 50, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 45, "median": 60, "target": 80, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 70, "median": 95, "target": 125, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
        "10+": {"floor": 100, "median": 140, "target": 175, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
    },

    "ui-ux-designer": {
        "label": "UI/UX Designer",
        "0-1": {"floor": 10, "median": 15, "target": 22, "demand": "High", "saturation": "High", "timing_signal": "Caution"},
        "1-3": {"floor": 18, "median": 28, "target": 40, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 35, "median": 50, "target": 70, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 60, "median": 80, "target": 110, "demand": "Medium", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 90, "median": 120, "target": 160, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
    },

    "graphic-designer": {
        "label": "Graphic Designer",
        "0-1": {"floor": 8, "median": 12, "target": 18, "demand": "Medium", "saturation": "High", "timing_signal": "Caution"},
        "1-3": {"floor": 15, "median": 22, "target": 32, "demand": "Medium", "saturation": "High", "timing_signal": "Hold"},
        "3-5": {"floor": 25, "median": 38, "target": 55, "demand": "Medium", "saturation": "Medium", "timing_signal": "Hold"},
        "5-10": {"floor": 45, "median": 65, "target": 90, "demand": "Medium", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 75, "median": 100, "target": 130, "demand": "Low", "saturation": "Low", "timing_signal": "Hold"},
    },

    "brand-identity-designer": {
        "label": "Brand Identity Designer",
        "0-1": {"floor": 15, "median": 20, "target": 30, "demand": "Medium", "saturation": "High", "timing_signal": "Caution"},
        "1-3": {"floor": 25, "median": 35, "target": 50, "demand": "Medium", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 45, "median": 60, "target": 85, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 75, "median": 100, "target": 130, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
        "10+": {"floor": 110, "median": 150, "target": 200, "demand": "Low", "saturation": "Low", "timing_signal": "Hold"},
    },

    "video-editor": {
        "label": "Video Editor",
        "0-1": {"floor": 10, "median": 15, "target": 20, "demand": "High", "saturation": "High", "timing_signal": "Caution"},
        "1-3": {"floor": 18, "median": 25, "target": 35, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 30, "median": 45, "target": 60, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 55, "median": 75, "target": 100, "demand": "Medium", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 80, "median": 110, "target": 140, "demand": "Medium", "saturation": "Low", "timing_signal": "Hold"},
    },

    "data-analyst": {
        "label": "Data Analyst",
        "0-1": {"floor": 12, "median": 20, "target": 28, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "1-3": {"floor": 22, "median": 35, "target": 50, "demand": "High", "saturation": "Medium", "timing_signal": "Act Now"},
        "3-5": {"floor": 40, "median": 58, "target": 80, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "5-10": {"floor": 65, "median": 90, "target": 120, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
        "10+": {"floor": 100, "median": 135, "target": 175, "demand": "High", "saturation": "Low", "timing_signal": "Act Now"},
    },

    "seo-content-writer": {
        "label": "SEO Content Writer",
        "0-1": {"floor": 8, "median": 12, "target": 18, "demand": "Medium", "saturation": "High", "timing_signal": "Caution"},
        "1-3": {"floor": 15, "median": 22, "target": 30, "demand": "Medium", "saturation": "High", "timing_signal": "Hold"},
        "3-5": {"floor": 25, "median": 35, "target": 50, "demand": "Medium", "saturation": "Medium", "timing_signal": "Act Now"},
        "5-10": {"floor": 40, "median": 55, "target": 75, "demand": "Low", "saturation": "Low", "timing_signal": "Hold"},
        "10+": {"floor": 60, "median": 80, "target": 100, "demand": "Low", "saturation": "Low", "timing_signal": "Hold"},
    },
}

# =========================================================
# COUNTRIES
# =========================================================

COUNTRY_DATA = {
    "egypt": {
        "label": "Egypt",
        "currency": "EGP",
        "col_reference_usd": 500,
        "col_label": "middle-class household in Cairo"
    },
    "saudi-arabia": {
        "label": "Saudi Arabia",
        "currency": "SAR",
        "col_reference_usd": 2200,
        "col_label": "mid-range household in Riyadh"
    },
    "uae": {
        "label": "UAE",
        "currency": "AED",
        "col_reference_usd": 3500,
        "col_label": "mid-range household in Dubai"
    },
    "qatar": {
        "label": "Qatar",
        "currency": "QAR",
        "col_reference_usd": 3000,
        "col_label": "mid-range household in Doha"
    },
    "kuwait": {
        "label": "Kuwait",
        "currency": "KWD",
        "col_reference_usd": 2800,
        "col_label": "mid-range household in Kuwait City"
    },
    "jordan": {
        "label": "Jordan",
        "currency": "JOD",
        "col_reference_usd": 1100,
        "col_label": "mid-range household in Amman"
    },
    "morocco": {
        "label": "Morocco",
        "currency": "MAD",
        "col_reference_usd": 600,
        "col_label": "mid-range household in Casablanca"
    },
    "tunisia": {
        "label": "Tunisia",
        "currency": "TND",
        "col_reference_usd": 500,
        "col_label": "mid-range household in Tunis"
    },
}

# =========================================================
# STATIC FX RATES
# =========================================================

STATIC_FX = {
    "EGP": 48.5, # Updated slightly closer to recent market figures
    "SAR": 3.75,
    "AED": 3.67,
    "QAR": 3.64,
    "KWD": 0.31,
    "JOD": 0.71,
    "MAD": 10.05,
    "TND": 3.12,
}

# =========================================================
# WORKING WINDOWS
# =========================================================

WORKING_WINDOWS = [
    {
        "market": "US East Coast",
        "client_hours": "9 AM – 12 PM EST",
        "egypt_local": "4 PM – 7 PM",
        "note": "Strong proposal and reply window."
    },
    {
        "market": "US West Coast",
        "client_hours": "9 AM – 12 PM PST",
        "egypt_local": "7 PM – 10 PM",
        "note": "Good for startup and tech clients."
    },
    {
        "market": "UK / Europe",
        "client_hours": "9 AM – 12 PM GMT",
        "egypt_local": "11 AM – 2 PM",
        "note": "Best overlap with Arab timezone."
    },
]

VALID_EXP_BRACKETS = ["0-1", "1-3", "3-5", "5-10", "10+"]

# =========================================================
# FULLY HARDCODED UI TEXT CONTENT
# =========================================================

TEXT_LIBRARY = {
    "High": {
        "demand_explanation":
            "Client demand is strong. Buyers are actively searching and budgets remain available. Strong positioning and fast responses can convert quickly."
    },
    "Medium": {
        "demand_explanation":
            "Demand is stable but selective. Good opportunities exist, but clients compare more options before hiring."
    },
    "Low": {
        "demand_explanation":
            "Demand is softer than usual. Winning work requires stronger specialization, better proof, and sharper positioning."
    },
}

SATURATION_LIBRARY = {
    "High": {
        "specialization_pivots":
            "Generalist competition is heavy. Move into a niche service, measurable outcomes, or a specific industry to reduce comparison pressure."
    },
    "Medium": {
        "specialization_pivots":
            "Competition exists but can be beaten with proof of results, faster communication, and a focused offer."
    },
    "Low": {
        "specialization_pivots":
            "Competition is relatively light. This is a good environment to push premium positioning and stronger rates."
    },
}

TIMING_LIBRARY = {
    "Act Now":
        "Market conditions currently favor action. Strong demand or lower competition creates a good moment to raise rates or reposition.",
    "Hold":
        "Conditions look stable. Maintain quality, improve proof, and make gradual moves rather than aggressive jumps.",
    "Caution":
        "This market segment is crowded or soft right now. Improve differentiation before pushing pricing aggressively.",
}

CLIENT_PERSPECTIVE_TEMPLATE = """
Below floor pricing often signals inexperience, desperation, or inconsistent quality.

Median pricing signals competence and a reasonable expectation of professional delivery.

Target pricing or above signals confidence, expertise, stronger systems, and measurable outcomes.
""".strip()

ACTION_TEMPLATE = """
1. Improve your portfolio with results, not just visuals.
2. Raise pricing gradually instead of staying static.
3. Bid during high-value client hours consistently.
4. Narrow your offer into a specific niche.
5. Track conversion rate, not just proposal count.
""".strip()


def get_hardcoded_sections(role_label, exp_bracket, market_rates, demand, saturation, timing_signal):
    target = market_rates["target"]

    return {
        "demand_explanation": TEXT_LIBRARY[demand]["demand_explanation"],
        "specialization_pivots": SATURATION_LIBRARY[saturation]["specialization_pivots"],
        "what_it_takes":
            f"Clients paying ${target}/hr expect reliable communication, clean execution, ownership of problems, and professional delivery without hand-holding.",
        "timing_explanation": TIMING_LIBRARY[timing_signal],
        "client_perspective": CLIENT_PERSPECTIVE_TEMPLATE,
        "positioning_brief":
            f"As a {role_label} in the {exp_bracket} bracket, your biggest opportunity is moving away from generic competition and toward specialized value. Pricing alone will not save weak positioning.",
        "action_layer": ACTION_TEMPLATE,
    }