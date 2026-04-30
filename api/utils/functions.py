import json
import database
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_core.tools import tool

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

CURRENCY_EXCHANGE_API_URL: str = os.getenv("CURRENCY_EXCHANGE_API_URL")

# LOL I don't know how it works 😂🥀✌🏻
def currency_exchange_converter(x: str, y: str):
    res = requests.get(CURRENCY_EXCHANGE_API_URL)
    return res.json()[x][y]

def get_diff():
    snapshots = database.get_snapshots()
    if len(snapshots) < 2:
        return {"error": "Not enough data for diff"}
    now = snapshots[0]
    past = snapshots[1]
    
    try:
        live_rate = currency_exchange_converter('usd', 'egp')
    except Exception:
        live_rate = now["egp_rate_at_date"]
    
    diff_val = {
        "income_delta_usd": now["total_received_usd"] - past["total_received_usd"],
        "income_delta_egp": (now["total_received_usd"] * live_rate) - past["total_received_egp"],
        "egp_rate_change": live_rate - past["egp_rate_at_date"]
    }
    return diff_val

def get_blame():
    snapshots = database.get_snapshots()
    client_stats = {}
    for s in snapshots:
        if s.get("clients_json"):
            clients = json.loads(s["clients_json"])
            for c in clients:
                name = c["name"]
                if name not in client_stats:
                    client_stats[name] = {"billed": 0, "effective_rate_sum": 0, "payment_wait_sum": 0, "count": 0}
                client_stats[name]["billed"] += c["billed"]
                client_stats[name]["effective_rate_sum"] += c["effective_rate"]
                client_stats[name]["payment_wait_sum"] += c["payment_wait_days"]
                client_stats[name]["count"] += 1
                
    results = []
    for name, stats in client_stats.items():
        results.append({
            "name": name,
            "total_billed": stats["billed"],
            "avg_effective_rate": stats["effective_rate_sum"] / stats["count"],
            "avg_payment_wait": stats["payment_wait_sum"] / stats["count"]
        })

    return results


@tool
def get_income_diff() -> dict:
    """Compare the two most recent income snapshots and return the change in
    USD income, EGP income (using the current live exchange rate), and the
    EGP/USD rate movement. Call this when the user asks about how their
    income or the exchange rate has shifted recently. Takes no arguments."""
    return get_diff()


@tool
def get_client_blame() -> list:
    """Return per-client aggregate stats across all snapshots: total billed,
    average effective hourly rate, and average payment wait in days. Call
    this when the user asks which clients are slow, which underpay, or wants
    a client-by-client breakdown. Takes no arguments."""
    return get_blame()


COACH_TOOLS = [get_income_diff, get_client_blame]
COACH_TOOLS_BY_NAME = {t.name: t for t in COACH_TOOLS}

