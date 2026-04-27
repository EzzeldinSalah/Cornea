from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import database
import coach
import json
import currency_exchange_api

app = FastAPI(title="Cornea API")

@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/api/auth/upwork")
def start_oauth():
    return {"url": "https://www.upwork.com/ab/account-security/oauth2/authorize?client_id=MOCK&redirect_uri=http://localhost:8000/api/auth/callback&response_type=code"}

@app.get("/api/auth/callback")
def oauth_callback(code: str):
    return {"status": "success", "token": "mock_token_123"}

@app.post("/api/sync/mock")
def sync_mock_data():
    database.generate_mock_data()
    return {"status": "Mock data generated successfully"}

@app.get("/api/log")
def get_log():
    snapshots = database.get_snapshots()
    for s in snapshots:
        if s.get("clients_json"):
            s["clients"] = json.loads(s["clients_json"])
            del s["clients_json"]
            
    try:
        live_rate = currency_exchange_api.currency_exchange_converter('usd', 'egp')
    except Exception:
        live_rate = None
        
    return {"snapshots": snapshots, "live_rate": live_rate}

@app.get("/api/diff")
def get_diff():
    snapshots = database.get_snapshots()
    if len(snapshots) < 2:
        return {"error": "Not enough data for diff"}
    now = snapshots[0]
    past = snapshots[1]
    
    try:
        live_rate = currency_exchange_api.currency_exchange_converter('usd', 'egp')
    except Exception:
        # fallback to historical rate if API fails
        live_rate = now["egp_rate_at_date"]
    
    diff_val = {
        "income_delta_usd": now["total_received_usd"] - past["total_received_usd"],
        "income_delta_egp": (now["total_received_usd"] * live_rate) - past["total_received_egp"],
        "egp_rate_change": live_rate - past["egp_rate_at_date"]
    }
    return diff_val

@app.get("/api/blame")
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

class CoachRequest(BaseModel):
    message: str

@app.post("/api/coach")
def chat_with_coach(req: CoachRequest):
    snapshots = database.get_snapshots()
    if not snapshots:
         context_str = "No data available."
    else:
         latest = snapshots[0]
         try:
             live_rate = currency_exchange_api.currency_exchange_converter('usd', 'egp')
             current_egp_value = latest['total_received_usd'] * live_rate
             context_str = f"Latest income: {latest['total_received_usd']} USD / {current_egp_value} EGP (Calculated using the LIVE EGP exchange rate of {live_rate}). The historical rate when they invoiced was {latest['egp_rate_at_date']}"
         except Exception:
             context_str = f"Latest income: {latest['total_received_usd']} USD / {latest['total_received_egp']} EGP. EGP rate: {latest['egp_rate_at_date']}"
         
    reply = coach.generate_coach_response(context_str, req.message)
    return {"reply": reply}
