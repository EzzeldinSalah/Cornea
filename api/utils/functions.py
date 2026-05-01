import json
import logging
import os
import time

import httpx

import database
from fastapi import HTTPException
from dotenv import load_dotenv
from pathlib import Path

from langchain_core.tools import tool

from utils.upwork import search_upwork_jobs

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

CURRENCY_EXCHANGE_API_URL: str = os.getenv("CURRENCY_EXCHANGE_API_URL", "")

EXCHANGE_RATE_CACHE = {}
EXCHANGE_CACHE_TTL_SECONDS = 60 * 60
ACTIVE_USER_ID = None


def set_active_user_id(user_id: int | None):
    global ACTIVE_USER_ID
    ACTIVE_USER_ID = user_id


def currency_exchange_converter(base_currency: str, target_currency: str):
    base = base_currency.lower()
    target = target_currency.lower()
    cache_key = f"{base}:{target}"

    if base == target:
        return 1.0

    now = time.time()
    cached = EXCHANGE_RATE_CACHE.get(cache_key)
    if cached and now - cached["timestamp"] < EXCHANGE_CACHE_TTL_SECONDS:
        return cached["rate"]

    primary_url = (
        CURRENCY_EXCHANGE_API_URL
        or f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json"
    )
    fallback_url = f"https://latest.currency-api.pages.dev/v1/currencies/{base}.json"

    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(primary_url)
            res.raise_for_status()
            data = res.json()
    except Exception as exc:
        logging.warning(f"Primary exchange API failed: {exc}. Trying fallback.")
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(fallback_url)
                res.raise_for_status()
                data = res.json()
        except Exception as exc2:
            if cached:
                logging.warning("Fallback exchange API failed; using cached value.")
                return cached["rate"]
            raise HTTPException(status_code=503, detail="Exchange rate unavailable.")

    rate = float(data[base][target])
    EXCHANGE_RATE_CACHE[cache_key] = {"rate": rate, "timestamp": now}
    return rate

def get_diff(user_id: int):
    snapshots = database.get_snapshots(user_id)
    if not snapshots or len(snapshots) < 2:
        return None

    now = snapshots[0]
    past = snapshots[1]

    # Compute difference purely in USD. Frontend will convert.
    diff_invoiced_usd = now["total_invoiced_usd"] - past["total_invoiced_usd"]
    diff_fees_usd = now["total_fees_usd"] - past["total_fees_usd"]
    diff_received_usd = now["total_received_usd"] - past["total_received_usd"]

    return {
        "diff_invoiced_usd": round(diff_invoiced_usd, 2),
        "diff_fees_usd": round(diff_fees_usd, 2),
        "diff_received_usd": round(diff_received_usd, 2),
        "now_received_usd": round(now["total_received_usd"], 2),
        "past_received_usd": round(past["total_received_usd"], 2),
    }

def get_blame(user_id: int):
    snapshots = database.get_snapshots(user_id)
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
            "total_billed_usd": stats["billed"],
            "avg_effective_rate": stats["effective_rate_sum"] / stats["count"],
            "avg_payment_wait": stats["payment_wait_sum"] / stats["count"]
        })

    return results


@tool
def get_income_diff() -> dict:
    """Compare the two most recent income snapshots and return the change in
    USD income. Call this when the user asks about how their income shifted
    recently. Takes no arguments."""
    if ACTIVE_USER_ID is None:
        return {"error": "User context missing"}
    return get_diff(ACTIVE_USER_ID)


@tool
def get_client_blame() -> list:
    """Return per-client aggregate stats across all snapshots: total billed,
    average effective hourly rate, and average payment wait in days. Call
    this when the user asks which clients are slow, which underpay, or wants
    a client-by-client breakdown. Takes no arguments."""
    if ACTIVE_USER_ID is None:
        return []
    return get_blame(ACTIVE_USER_ID)


COACH_TOOLS = [get_income_diff, get_client_blame, search_upwork_jobs]
COACH_TOOLS_BY_NAME = {t.name: t for t in COACH_TOOLS}
