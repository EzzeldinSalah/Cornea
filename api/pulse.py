# pulse.py
# Fully hardcoded Pulse generation layer.
# No AI.
# No Gemini.
# No API keys.
# No dotenv.
# No LangChain.
#
# This file keeps the SAME function name used by main.py:
# generate_pulse_ai_sections(...)
#
# So you can replace your old pulse.py with this file directly.

from pulse_data import get_hardcoded_sections


def generate_pulse_ai_sections(
    role_label: str,
    exp_bracket: str,
    country_label: str,
    market_rates: dict,
    demand: str,
    saturation: str,
    timing_signal: str,
    current_rate: float | None,
    coach_language: str,
    coach_tone: str,
) -> dict:
    """
    Returns Pulse narrative sections using only hardcoded data.

    Output format stays identical to old AI version:
    {
        "demand_explanation": str,
        "specialization_pivots": str,
        "what_it_takes": str,
        "timing_explanation": str,
        "client_perspective": str,
        "positioning_brief": str,
        "action_layer": str,
    }
    """

    try:
        # Base hardcoded content from pulse_data.py
        sections = get_hardcoded_sections(
            role_label=role_label,
            exp_bracket=exp_bracket,
            market_rates=market_rates,
            demand=demand,
            saturation=saturation,
            timing_signal=timing_signal,
        )

        # ---------------------------------------
        # Personal pricing comparison
        # ---------------------------------------
        if current_rate is not None:
            median = market_rates["median"]

            if current_rate < median:
                compare_text = (
                    f" Your current rate (${current_rate}/hr) is below the market "
                    f"median (${median}/hr). This usually means underpricing or weak positioning."
                )

            elif current_rate > median:
                compare_text = (
                    f" Your current rate (${current_rate}/hr) is above the market "
                    f"median (${median}/hr). Clients will expect stronger proof and premium execution."
                )

            else:
                compare_text = (
                    f" Your current rate matches the market median (${median}/hr)."
                )

            sections["positioning_brief"] += compare_text

        # ---------------------------------------
        # Tone handling
        # ---------------------------------------
        sections = _apply_tone(sections, coach_tone)

        # ---------------------------------------
        # Language handling
        # ---------------------------------------
        sections = _apply_language(
            sections,
            coach_language,
            role_label,
            country_label
        )

        return sections

    except Exception as e:
        fallback = f"Market analysis unavailable. ({e})"

        return {
            "demand_explanation": fallback,
            "specialization_pivots": fallback,
            "what_it_takes": fallback,
            "timing_explanation": fallback,
            "client_perspective": fallback,
            "positioning_brief": fallback,
            "action_layer": fallback,
        }


# ==================================================
# TONE SYSTEM
# ==================================================

def _apply_tone(sections: dict, tone: str) -> dict:

    if tone == "Blunt":
        sections["positioning_brief"] += (
            " Staying generic and cheap will keep you replaceable."
        )

    elif tone == "Gentle":
        sections["positioning_brief"] += (
            " With steady improvement and stronger positioning, growth is realistic."
        )

    else:  # Balanced
        sections["positioning_brief"] += (
            " The smartest next move is focused improvement with measurable proof."
        )

    return sections


# ==================================================
# LANGUAGE SYSTEM
# ==================================================

def _apply_language(
    sections: dict,
    coach_language: str,
    role_label: str,
    country_label: str,
) -> dict:

    if coach_language == "arabic":
        sections["positioning_brief"] = (
            f"أنت تعمل في مجال {role_label} داخل سوق {country_label}. "
            + sections["positioning_brief"]
        )

    elif coach_language == "mixed":
        sections["positioning_brief"] = (
            f"As a {role_label} freelancer in {country_label}, "
            + sections["positioning_brief"]
        )

    # english = unchanged

    return sections