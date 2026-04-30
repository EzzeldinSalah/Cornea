from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import database
import coach
import json
from utils.functions import get_diff, get_blame, currency_exchange_converter
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
        live_rate = currency_exchange_converter('usd', 'egp')
    except Exception:
        live_rate = None
        
    return {"snapshots": snapshots, "live_rate": live_rate}

@app.get("/api/diff")
def get_diff_api():
    return get_diff()

@app.get("/api/blame")
def get_blame_api():
    return get_blame()

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
             live_rate = currency_exchange_converter('usd', 'egp')
             current_egp_value = latest['total_received_usd'] * live_rate
             context_str = f"Latest income: {latest['total_received_usd']} USD / {current_egp_value} EGP (Calculated using the LIVE EGP exchange rate of {live_rate}). The historical rate when they invoiced was {latest['egp_rate_at_date']}"
         except Exception:
             context_str = f"Latest income: {latest['total_received_usd']} USD / {latest['total_received_egp']} EGP. EGP rate: {latest['egp_rate_at_date']}"
         
    reply = coach.generate_coach_response(req.message, session_id="1")
    return {"reply": reply}
