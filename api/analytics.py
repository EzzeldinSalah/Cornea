import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

import database


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def get_date_threshold(period: str) -> datetime:
    now = datetime.now()
    if period == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "this_quarter":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        return now.replace(
            month=quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    if period == "this_year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if period in {"all_time", "custom"}:
        return datetime.min

    period_map = {
        "30d": 30,
        "3m": 90,
        "90d": 90,
        "6m": 180,
        "180d": 180,
        "12m": 365,
        "1y": 365,
    }
    if period in period_map:
        return now - timedelta(days=period_map[period])
    return datetime.min


def calculate_metrics(user_id: int, period: str) -> Dict[str, Any]:
    snapshots = database.get_snapshots(user_id)
    threshold_date = get_date_threshold(period)

    filtered_snapshots = []
    for s in snapshots:
        created_at = parse_date(s["created_at"])
        if created_at >= threshold_date:
            filtered_snapshots.append(s)

    filtered_snapshots.sort(key=lambda s: parse_date(s["created_at"]))

    total_invoiced_usd = 0.0
    total_received_usd = 0.0
    total_fees_usd = 0.0
    total_transfer_usd = 0.0

    client_stats: Dict[str, Dict[str, float]] = {}
    monthly_stats: Dict[str, Dict[str, float]] = {}
    timeline_map: Dict[str, List[Dict[str, Any]]] = {}

    total_rate_weighted = 0.0
    total_billed_weight = 0.0

    for s in filtered_snapshots:
        invoiced = s.get("total_invoiced_usd", 0.0)
        fees = s.get("total_fees_usd", 0.0)
        received_usd = s.get("total_received_usd", 0.0)

        total_invoiced_usd += invoiced
        total_received_usd += received_usd
        total_fees_usd += fees
        total_transfer_usd += max(invoiced - fees - received_usd, 0.0)

        created_at = parse_date(s["created_at"])
        month_key = created_at.strftime("%Y-%m")
        month_label = created_at.strftime("%b '%y")
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "month": month_label,
                "month_key": month_key,
                "invoiced_usd": 0.0,
                "received_usd": 0.0,
                "rate_weighted_sum": 0.0,
                "billed_sum": 0.0,
            }

        monthly_stats[month_key]["invoiced_usd"] += invoiced
        monthly_stats[month_key]["received_usd"] += received_usd

        clients_json = s.get("clients_json")
        if clients_json:
            clients_list = json.loads(clients_json)
            for c in clients_list:
                name = c.get("name", "Unknown")
                billed = float(c.get("billed", 0) or 0)
                rate = float(c.get("effective_rate", 0) or 0)
                wait_days = float(c.get("payment_wait_days", 0) or 0)

                if name not in client_stats:
                    client_stats[name] = {
                        "billed": 0.0,
                        "total_rate": 0.0,
                        "total_wait": 0.0,
                        "count": 0,
                    }

                client_stats[name]["billed"] += billed
                client_stats[name]["total_rate"] += rate
                client_stats[name]["total_wait"] += wait_days
                client_stats[name]["count"] += 1

                monthly_stats[month_key]["rate_weighted_sum"] += rate * billed
                monthly_stats[month_key]["billed_sum"] += billed

                total_rate_weighted += rate * billed
                total_billed_weight += billed

                timeline_map.setdefault(name, []).append({
                    "date": s["created_at"],
                    "wait_days": wait_days,
                })

    monthly_data = sorted(monthly_stats.values(), key=lambda x: x["month_key"])
    for md in monthly_data:
        billed_sum = md["billed_sum"]
        md["effective_rate"] = round(md["rate_weighted_sum"] / billed_sum, 2) if billed_sum else 0.0

    clients_data = []
    for name, stats in client_stats.items():
        count = stats["count"]
        avg_rate = stats["total_rate"] / count if count else 0
        avg_wait = stats["total_wait"] / count if count else 0
        clients_data.append({
            "name": name,
            "total_usd": stats["billed"],
            "effective_rate": round(avg_rate, 2),
            "avg_payment_days": round(avg_wait, 1),
        })

    global_effective_rate = (
        total_rate_weighted / total_billed_weight if total_billed_weight > 0 else 0.0
    )

    upwork_pct = (total_fees_usd / total_invoiced_usd) * 100.0 if total_invoiced_usd > 0 else 0.0
    transfer_pct = (total_transfer_usd / total_invoiced_usd) * 100.0 if total_invoiced_usd > 0 else 0.0
    kept_pct = max(100.0 - upwork_pct - transfer_pct, 0.0)

    best_month = max(monthly_data, key=lambda x: x["received_usd"], default=None)
    worst_month = min(monthly_data, key=lambda x: x["received_usd"], default=None)

    inflation_rate_pct = float(os.getenv("INFLATION_RATE_PCT", "2"))
    inflation_index = []
    current_index = 100.0
    for md in monthly_data:
        inflation_index.append({"month": md["month"], "index_value": round(current_index, 2)})
        current_index *= 1 + (inflation_rate_pct / 100.0)

    growth_rate = float(os.getenv("FORECAST_GROWTH_RATE", "1.05"))
    # TODO: replace with real model post-hackathon
    forecast = []
    if monthly_data:
        # Forecast based on last month's USD
        last_usd = monthly_data[-1]["received_usd"]
        for i in range(1, 4):
            future_month = (datetime.now() + timedelta(days=30 * i)).strftime("%b '%y")
            projected_usd = last_usd * (growth_rate ** i)
            forecast.append({
                "month": future_month,
                "projected_usd": round(projected_usd, 2),
                "confidence_low_usd": round(projected_usd * 0.8, 2),
                "confidence_high_usd": round(projected_usd * 1.3, 2),
            })

    timeline = []
    for name, entries in timeline_map.items():
        entries.sort(key=lambda e: parse_date(e["date"]))
        timeline.append({"name": name, "entries": entries})

    return {
        "period": period,
        "total_invoiced_usd": round(total_invoiced_usd, 2),
        "total_received_usd": round(total_received_usd, 2),
        "effective_hourly_rate": round(global_effective_rate, 2),
        "total_fees_usd": round(total_fees_usd, 2),
        "monthly": monthly_data,
        "clients": sorted(clients_data, key=lambda x: x["total_usd"], reverse=True),
        "fee_breakdown": {
            "upwork_pct": round(upwork_pct, 1),
            "transfer_pct": round(transfer_pct, 1),
            "kept_pct": round(kept_pct, 1),
        },
        "inflation_index": inflation_index,
        "forecast": forecast,
        "timeline": timeline,
        "best_month": {
            "month": best_month["month"],
            "income_usd": round(best_month["received_usd"], 2),
            "effective_rate": best_month.get("effective_rate", 0.0),
        } if best_month else None,
        "worst_month": {
            "month": worst_month["month"],
            "income_usd": round(worst_month["received_usd"], 2),
            "effective_rate": worst_month.get("effective_rate", 0.0),
        } if worst_month else None,
    }
