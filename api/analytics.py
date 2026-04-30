import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

def parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

def get_date_threshold(period: str) -> datetime:
    now = datetime.now()
    if period == "30d":
        return now - timedelta(days=30)
    elif period == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "3m":
        return now - timedelta(days=90)
    elif period == "this_quarter":
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        return now.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "6m":
        return now - timedelta(days=180)
    elif period == "this_year":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "12m":
        return now - timedelta(days=365)
    
    return datetime.min

def calculate_metrics(_snapshots: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
    threshold_date = get_date_threshold(period)
    
    filtered_snapshots = []
    for s in _snapshots:
        created_at = parse_date(s["created_at"])
        if created_at >= threshold_date:
            filtered_snapshots.append(s)

    total_invoiced_usd = 0.0
    total_received_local = 0.0
    total_fees_usd = 0.0
    
    client_stats: Dict[str, Dict[str, float]] = {}
    monthly_stats: Dict[str, Dict[str, float]] = {}

    for s in filtered_snapshots:
        total_invoiced_usd += s.get("total_invoiced_usd", 0.0)
        total_received_local += s.get("total_received_egp", 0.0)
        total_fees_usd += s.get("total_fees_usd", 0.0)
        
        month_key = parse_date(s["created_at"]).strftime("%b '%y")
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {"invoiced_usd": 0.0, "received_local": 0.0}
            
        monthly_stats[month_key]["invoiced_usd"] += s.get("total_invoiced_usd", 0.0)
        monthly_stats[month_key]["received_local"] += s.get("total_received_egp", 0.0)
        
        clients_json = s.get("clients_json")
        if clients_json:
            clients_list = json.loads(clients_json)
            for c in clients_list:
                name = c.get("name", "Unknown")
                if name not in client_stats:
                    client_stats[name] = {"billed": 0.0, "total_rate": 0.0, "total_wait": 0.0, "count": 0}
                
                client_stats[name]["billed"] += c.get("billed", 0)
                client_stats[name]["total_rate"] += c.get("effective_rate", 0)
                client_stats[name]["total_wait"] += c.get("payment_wait_days", 0)
                client_stats[name]["count"] += 1

    monthly_data = [
        {"month": k, "invoiced_usd": v["invoiced_usd"], "received_local": v["received_local"]}
        for k, v in monthly_stats.items()
    ]
    
    clients_data = []
    total_client_rate = 0.0
    for name, stats in client_stats.items():
        count = stats["count"]
        avg_rate = stats["total_rate"] / count if count else 0
        avg_wait = stats["total_wait"] / count if count else 0
        clients_data.append({
            "name": name,
            "total_usd": stats["billed"],
            "effective_rate": round(avg_rate, 2),
            "avg_payment_days": round(avg_wait, 1)
        })
        total_client_rate += avg_rate
    
    num_clients = len(client_stats)
    global_effective_rate = total_client_rate / num_clients if num_clients > 0 else 0.0

    upwork_pct = 10.0
    transfer_pct = 2.5
    kept_pct = 100.0 - upwork_pct - transfer_pct
    
    if total_invoiced_usd > 0:
        upwork_pct = (total_fees_usd / total_invoiced_usd) * 100.0
        transfer_pct = ((total_invoiced_usd - total_fees_usd - s.get("total_received_usd", 0.0)) / total_invoiced_usd) * 100.0
        if transfer_pct < 0: transfer_pct = 2.5
        kept_pct = 100.0 - upwork_pct - transfer_pct

    inflation_index = []
    forecast = []
    if len(monthly_data) > 0:
        current_index = 100
        for md in monthly_data:
            inflation_index.append({"month": md["month"], "index_value": current_index})
            current_index += 2  
            
        last_local = monthly_data[-1]["received_local"]
        for i in range(1, 4):
            future_month = (datetime.now() + timedelta(days=30*i)).strftime("%b '%y")
            forecast.append({
                "month": future_month,
                "projected_local": round(last_local * 1.05, 2),
                "confidence_low": round(last_local * 0.8, 2),
                "confidence_high": round(last_local * 1.3, 2)
            })

    return {
        "period": period,
        "total_invoiced_usd": round(total_invoiced_usd, 2),
        "total_received_local": round(total_received_local, 2),
        "effective_hourly_rate": round(global_effective_rate, 2),
        "total_fees_usd": round(total_fees_usd, 2),
        "monthly": monthly_data,
        "clients": sorted(clients_data, key=lambda x: x["total_usd"], reverse=True),
        "fee_breakdown": {
            "upwork_pct": round(upwork_pct, 1),
            "transfer_pct": round(transfer_pct, 1),
            "kept_pct": round(kept_pct, 1)
        },
        "inflation_index": inflation_index,
        "forecast": forecast
    }