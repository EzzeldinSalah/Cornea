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
    try:
        sections = get_hardcoded_sections(
            role_label=role_label,
            exp_bracket=exp_bracket,
            market_rates=market_rates,
            demand=demand,
            saturation=saturation,
            timing_signal=timing_signal,
        )

        if current_rate is not None:
            median = market_rates["median"]

            if current_rate < median:
                rate_comparison = (
                    f" Your current rate (${current_rate}/hr) is below the market "
                    f"median (${median}/hr). This usually means underpricing or weak positioning."
                )

            elif current_rate > median:
                rate_comparison = (
                    f" Your current rate (${current_rate}/hr) is above the market "
                    f"median (${median}/hr). Clients will expect stronger proof and premium execution."
                )

            else:
                rate_comparison = (
                    f" Your current rate matches the market median (${median}/hr)."
                )

            sections["positioning_brief"] += rate_comparison

        sections = _apply_tone(sections, coach_tone)
        sections = _apply_language(
            sections,
            coach_language,
            role_label,
            country_label,
        )

        return sections

    except Exception as error:
        fallback = f"Market analysis unavailable. ({error})"

        return {
            "demand_explanation": fallback,
            "specialization_pivots": fallback,
            "what_it_takes": fallback,
            "timing_explanation": fallback,
            "client_perspective": fallback,
            "positioning_brief": fallback,
            "action_layer": fallback,
        }


def _apply_tone(sections: dict, tone: str) -> dict:
    if tone == "Blunt":
        sections["positioning_brief"] += (
            " Staying generic and cheap will keep you replaceable."
        )

    elif tone == "Gentle":
        sections["positioning_brief"] += (
            " With steady improvement and stronger positioning, growth is realistic."
        )

    else:
        sections["positioning_brief"] += (
            " The smartest next move is focused improvement with measurable proof."
        )

    return sections


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

    return sections
