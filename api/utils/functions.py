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
    except Exception as error:
        logging.warning(f"Primary exchange API failed: {error}. Trying fallback.")
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(fallback_url)
                res.raise_for_status()
                data = res.json()
        except Exception:
            if cached:
                logging.warning("Fallback exchange API failed; using cached value.")
                return cached["rate"]
            raise HTTPException(status_code=503, detail="Exchange rate unavailable.")

    try:
        rate = float(data[base][target])
    except (KeyError, TypeError, ValueError):
        if cached:
            return cached["rate"]
        raise HTTPException(status_code=503, detail="Exchange rate unavailable.")

    EXCHANGE_RATE_CACHE[cache_key] = {"rate": rate, "timestamp": now}
    return rate


def get_diff(user_id: int, base_id: int = None, compare_id: int = None):
    snapshots = database.get_snapshots(user_id)
    if not snapshots or len(snapshots) < 2:
        return {"error": "Need at least two snapshots to compute a diff."}

    base_snap = None
    compare_snap = None

    if (base_id is None) != (compare_id is None):
        return {"error": "Select both base and compare snapshots."}

    if base_id is not None:
        base_snap = next((s for s in snapshots if s["id"] == base_id), None)
        compare_snap = next((s for s in snapshots if s["id"] == compare_id), None)
        if not base_snap or not compare_snap:
            return {"error": "Selected snapshots were not found."}

    if not base_snap or not compare_snap:
        base_snap = snapshots[1]
        compare_snap = snapshots[0]

    def process_snapshot(snap):
        clients = []
        if snap.get("clients_json"):
            try:
                raw_clients = json.loads(snap["clients_json"])
            except (json.JSONDecodeError, TypeError):
                raw_clients = []
            for c in raw_clients:
                clients.append({
                    "name": c.get("name", "Unknown"),
                    "billed": float(c.get("billed", 0)),
                    "effective_rate": float(c.get("effective_rate", 0)),
                    "wait_days": float(c.get("payment_wait_days", 0)),
                })

        avg_wait = sum(c["wait_days"] for c in clients) / len(clients) if clients else 0.0
        total_billed = sum(c["billed"] for c in clients)
        eff_rate = sum(c["effective_rate"] * c["billed"] for c in clients) / total_billed if total_billed > 0 else 0.0

        return {
            "id": snap["id"],
            "date": snap["created_at"],
            "source": snap.get("source", "Unknown"),
            "invoiced_usd": float(snap["total_invoiced_usd"]),
            "fees_usd": float(snap["total_fees_usd"]),
            "received_usd": float(snap["total_received_usd"]),
            "effective_rate": round(eff_rate, 2),
            "avg_payment_wait": round(avg_wait, 1),
            "clients": clients,
        }

    base = process_snapshot(base_snap)
    compare = process_snapshot(compare_snap)

    delta = {
        "invoiced_usd": round(compare["invoiced_usd"] - base["invoiced_usd"], 2),
        "fees_usd": round(compare["fees_usd"] - base["fees_usd"], 2),
        "received_usd": round(compare["received_usd"] - base["received_usd"], 2),
        "effective_rate": round(compare["effective_rate"] - base["effective_rate"], 2),
        "avg_payment_wait": round(compare["avg_payment_wait"] - base["avg_payment_wait"], 1),
        "client_count": len(compare["clients"]) - len(base["clients"]),
    }

    return {
        "base": base,
        "compare": compare,
        "delta": delta,
    }


def get_blame(user_id: int):
    snapshots = database.get_snapshots(user_id)
    client_stats = {}
    for s in snapshots:
        if s.get("clients_json"):
            try:
                clients = json.loads(s["clients_json"])
            except (json.JSONDecodeError, TypeError):
                clients = []
            for c in clients:
                name = c["name"]
                if name not in client_stats:
                    client_stats[name] = {
                        "billed": 0,
                        "effective_rate_sum": 0,
                        "payment_wait_sum": 0,
                        "count": 0,
                    }
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
            "avg_payment_wait": stats["payment_wait_sum"] / stats["count"],
        })

    return results


@tool(description="Compare the two most recent income snapshots and return the change in USD income.")
def get_income_diff() -> dict:
    if ACTIVE_USER_ID is None:
        return {"error": "User context missing"}
    return get_diff(ACTIVE_USER_ID)


@tool(description="Return per-client aggregate stats across all snapshots.")
def get_client_blame() -> list:
    if ACTIVE_USER_ID is None:
        return []
    return get_blame(ACTIVE_USER_ID)


COACH_TOOLS = [get_income_diff, get_client_blame, search_upwork_jobs]
COACH_TOOLS_BY_NAME = {t.name: t for t in COACH_TOOLS}
