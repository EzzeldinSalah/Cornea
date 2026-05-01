import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
import time
import jwt
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

import database
import coach
import analytics
from utils.functions import get_diff, get_blame, currency_exchange_converter

app = FastAPI(title="Cornea API")

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-dev")
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("PUBLIC_GOOGLE_CLIENT_ID")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[int]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None

@app.on_event("startup")
def startup_event():
    database.init_db()

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    hashed_pwd = get_password_hash(req.password)
    user_id = database.create_user_with_password(req.email, hashed_pwd)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email already registered")
    token = create_access_token(data={"sub": req.email, "user_id": user_id})
    return {"token": token}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = database.get_user_by_email(req.email)
    if not user or not user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(data={"sub": user["email"], "user_id": user["id"]})
    return {"token": token}


@app.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            req.credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        google_id = idinfo.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")
        user_id = database.upsert_google_user(email, google_id)
        token = create_access_token(data={"sub": email, "user_id": user_id})
        return {"token": token}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")


@app.put("/api/auth/password")
def change_password(req: ChangePasswordRequest, user_id: int = Depends(get_current_user)):
    user = database.get_user_by_id(user_id)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="No password set (Google-only account)")
    if not verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    database.update_user_password(user_id, get_password_hash(req.new_password))
    return {"status": "success"}

class UserSettings(BaseModel):
    display_name: str = ""
    avatar_url: str = ""
    primary_language: str = "English"
    primary_currency: str = "USD"
    secondary_currency_display: bool = True
    coach_language: str = "mixed"
    coach_tone: str = "Balanced"
    notify_weekly_digest: bool = True
    notify_slow_month: bool = True
    notify_late_payment: bool = True
    notify_exchange_rate: bool = False


@app.get("/api/settings")
def get_settings(user_id: int = Depends(get_current_user)):
    settings = database.get_user_settings(user_id)
    user = database.get_user_by_id(user_id)
    email = user["email"] if user else ""
    if not settings:
        data = UserSettings().model_dump()
        data["email"] = email
        return data
    settings["email"] = email
    return settings


@app.put("/api/settings")
def update_settings(settings: UserSettings, user_id: int = Depends(get_current_user)):
    database.upsert_user_settings(user_id, settings.model_dump())
    return {"status": "success"}


@app.post("/api/avatar")
async def upload_avatar(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    content = await file.read()
    mime = file.content_type
    database.save_user_avatar(user_id, content, mime)

    avatar_url = f"/api/avatar/{user_id}?t={int(time.time())}"
    settings = database.get_user_settings(user_id) or {}
    settings["avatar_url"] = avatar_url
    database.upsert_user_settings(user_id, settings)
    return {"avatar_url": avatar_url}


@app.get("/api/avatar/{uid}")
def get_avatar(uid: int):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT avatar_blob, avatar_mime FROM user_settings WHERE user_id = ?", (uid,))
    row = c.fetchone()
    conn.close()

    if row and row["avatar_blob"]:
        return Response(content=row["avatar_blob"], media_type=row["avatar_mime"])
    raise HTTPException(status_code=404, detail="Avatar not found")

@app.get("/api/analytics")
def get_analytics(period: str = "30d", user_id: int = Depends(get_current_user)):
    try:
        metrics = analytics.calculate_metrics(user_id, period)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/account")
def delete_account(user_id: int = Depends(get_current_user)):
    database.delete_user(user_id)
    return {"status": "success"}


@app.delete("/api/snapshots")
def clear_all_snapshots(user_id: int = Depends(get_current_user)):
    database.clear_snapshots(user_id)
    return {"status": "success"}


@app.get("/api/export")
def export_data(user_id: int = Depends(get_current_user)):
    return JSONResponse(content=database.export_user_data(user_id))


@app.post("/api/sync/mock")
def sync_mock_data(user_id: int = Depends(get_current_user)):
    database.generate_mock_data(user_id)
    return {"status": "Mock data generated successfully"}


@app.get("/api/exchange-rate")
def get_exchange_rate(currency: str):
    """Returns the live exchange rate for the given currency relative to USD."""
    rate = currency_exchange_converter("usd", currency)
    return {
        "currency": currency.upper(),
        "rate": rate,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/log")
def get_log(user_id: int = Depends(get_current_user)):
    snapshots = [database.snapshot_usd_payload(s) for s in database.get_snapshots(user_id)]
    for s in snapshots:
        if s.get("clients_json"):
            s["clients"] = json.loads(s["clients_json"])
            del s["clients_json"]

    return {
        "snapshots": snapshots
    }


@app.get("/api/diff")
def get_diff_api(user_id: int = Depends(get_current_user)):
    return get_diff(user_id)


@app.get("/api/blame")
def get_blame_api(user_id: int = Depends(get_current_user)):
    return get_blame(user_id)


# --- MERGE APIs ---

@app.get("/api/sources")
def get_sources_api(user_id: int = Depends(get_current_user)):
    return database.get_income_sources(user_id)

@app.post("/api/sources/{source_id}/sync")
def sync_source_api(source_id: str, user_id: int = Depends(get_current_user)):
    success = database.sync_source_mock(source_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "success"}

class ManualTransaction(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    date: str
    source_label: str

@app.post("/api/transactions/manual")
def add_manual_transaction_api(req: ManualTransaction, user_id: int = Depends(get_current_user)):
    database.add_manual_transaction(user_id, req.model_dump())
    return {"status": "success"}

@app.get("/api/merge/timeline")
def get_merge_timeline_api(user_id: int = Depends(get_current_user)):
    return database.get_uncommitted_transactions(user_id)

@app.get("/api/merge/reconciliation")
def get_merge_reconciliation_api(user_id: int = Depends(get_current_user)):
    uncommitted = database.get_uncommitted_transactions(user_id)
    total_usd = sum(t["amount_usd"] for t in uncommitted)
    total_fees = sum(t["platform_fee"] for t in uncommitted)
    total_local = sum(t["amount_local"] for t in uncommitted)
    
    kept_pct = 0
    if total_usd > 0:
        kept_pct = ((total_usd - total_fees) / total_usd) * 100
        
    sources_dict = {}
    for t in uncommitted:
        sources_dict[t["source"]] = sources_dict.get(t["source"], 0) + t["amount_usd"]
        
    sources_list = [{"name": k, "contribution_usd": v} for k, v in sources_dict.items()]
    
    return {
        "total_usd": total_usd,
        "total_local": total_local,
        "total_fees": total_fees,
        "kept_percentage": kept_pct,
        "sources": sources_list
    }

@app.post("/api/merge/commit")
def commit_merge_api(user_id: int = Depends(get_current_user)):
    success = database.commit_transactions_to_snapshot(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="No unmerged transactions to commit.")
    return {"status": "success"}

# --- COACH APIs ---

class CoachRequest(BaseModel):
    message: str
    session_id: str

class SessionCreateRequest(BaseModel):
    title: str

class SessionRenameRequest(BaseModel):
    title: str


@app.post("/api/coach")
def chat_with_coach(req: CoachRequest, user_id: int = Depends(get_current_user)):
    user_settings = database.get_user_settings(user_id) or {}
    coach_language = user_settings.get("coach_language", "mixed")
    coach_tone = user_settings.get("coach_tone", "Balanced")

    snapshots = database.get_snapshots(user_id)
    if not snapshots:
        context_str = "No data available."
    else:
        latest = snapshots[0]
        context_str = (
            f"Latest income: {latest['total_received_usd']} USD."
        )

    reply = coach.generate_coach_response(
        context_str,
        req.message,
        req.session_id,
        coach_language=coach_language,
        coach_tone=coach_tone,
        user_id=user_id,
    )
    return {"reply": reply}


@app.get("/api/coach/sessions")
def get_coach_sessions(user_id: int = Depends(get_current_user)):
    return database.get_coach_sessions(user_id)


@app.post("/api/coach/sessions")
def create_coach_session(req: SessionCreateRequest, user_id: int = Depends(get_current_user)):
    return database.create_session(req.title, user_id)


@app.put("/api/coach/sessions/{session_id}")
def rename_coach_session(session_id: int, req: SessionRenameRequest, user_id: int = Depends(get_current_user)):
    database.rename_session(session_id, req.title, user_id)
    return {"status": "success"}


@app.delete("/api/coach/sessions/{session_id}")
def delete_coach_session(session_id: int, user_id: int = Depends(get_current_user)):
    database.delete_session(session_id, user_id)
    return {"status": "success"}


@app.get("/api/coach/sessions/{session_id}/messages")
def get_coach_session_messages(session_id: int, user_id: int = Depends(get_current_user)):
    session = database.get_coach_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": coach.get_formatted_history(str(session_id))}
