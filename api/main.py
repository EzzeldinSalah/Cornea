import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
import time
import jwt
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Response, Query
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
import pulse
from pulse_data import MARKET_DATA, COUNTRY_DATA, WORKING_WINDOWS, VALID_EXP_BRACKETS
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


# ── Auth Models ──────────────────────────────────────────────────────────────

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


# ── Auth Endpoints ────────────────────────────────────────────────────────────

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


# ── Settings & Avatar ─────────────────────────────────────────────────────────

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


# ── Analytics & Account ───────────────────────────────────────────────────────

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


# ── Log / Diff / Blame ────────────────────────────────────────────────────────

@app.get("/api/log")
def get_log(user_id: int = Depends(get_current_user)):
    snapshots = [database.snapshot_usd_payload(s) for s in database.get_snapshots(user_id)]
    for s in snapshots:
        if s.get("clients_json"):
            s["clients"] = json.loads(s["clients_json"])
            del s["clients_json"]
    return {"snapshots": snapshots}


@app.get("/api/diff")
def get_diff_api(base: int = Query(None), compare: int = Query(None), user_id: int = Depends(get_current_user)):
    return get_diff(user_id, base, compare)


@app.post("/api/diff/insight")
def get_diff_insight_api(diff_data: dict, user_id: int = Depends(get_current_user)):
    from coach import generate_diff_insight
    insight = generate_diff_insight(diff_data, user_id)
    return {"insight": insight}


@app.get("/api/blame")
def get_blame_api(user_id: int = Depends(get_current_user)):
    return get_blame(user_id)


# ── Sources & Merge ───────────────────────────────────────────────────────────

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
        "sources": sources_list,
    }


@app.post("/api/merge/commit")
def commit_merge_api(user_id: int = Depends(get_current_user)):
    success = database.commit_transactions_to_snapshot(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="No unmerged transactions to commit.")
    return {"status": "success"}


# ── Pulse ─────────────────────────────────────────────────────────────────────

class PulseRequest(BaseModel):
    job_title: str          # must match a key in MARKET_DATA (e.g. "react-developer")
    years_experience: str   # must be one of VALID_EXP_BRACKETS (e.g. "1-3")
    country: str            # must match a key in COUNTRY_DATA (e.g. "egypt")
    current_rate: Optional[float] = None  # user's current hourly rate in USD, optional


@app.post("/api/pulse")
def get_pulse(req: PulseRequest, user_id: Optional[int] = Depends(get_optional_user)):
    """
    Main Pulse endpoint. Accepts the three core inputs plus an optional current rate.
    Returns the full structured report: data sections computed here, AI sections
    generated by pulse.py.

    Works for both authenticated and anonymous users. When authenticated, reads
    coach_language and coach_tone from the user's settings so the AI brief matches
    their Coach page preferences.
    """

    # --- 1. Validate inputs against the curated dataset ---
    role_key = req.job_title.lower().strip()
    if role_key not in MARKET_DATA:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported job title: '{req.job_title}'. "
                   f"Supported values: {list(MARKET_DATA.keys())}"
        )

    exp_key = req.years_experience.strip()
    if exp_key not in VALID_EXP_BRACKETS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid experience bracket: '{req.years_experience}'. "
                   f"Must be one of: {VALID_EXP_BRACKETS}"
        )

    country_key = req.country.lower().strip()
    if country_key not in COUNTRY_DATA:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported country: '{req.country}'. "
                   f"Supported values: {list(COUNTRY_DATA.keys())}"
        )

    # --- 2. Pull structured data from the curated dataset ---
    role_data = MARKET_DATA[role_key]
    bracket_data = role_data[exp_key]
    country_data = COUNTRY_DATA[country_key]

    market_rates = {
        "floor":  bracket_data["floor"],
        "median": bracket_data["median"],
        "target": bracket_data["target"],
    }
    demand        = bracket_data["demand"]
    saturation    = bracket_data["saturation"]
    timing_signal = bracket_data["timing_signal"]

    # --- 3. Fetch reference exchange rate (static) ---
    try:
        live_rate = currency_exchange_converter('usd', country_data["currency"].lower())
    except Exception:
        live_rate = None  # report will show USD only, no local conversion

    # --- 4. Compute rate ranges in local currency ---
    def to_local(usd_amount: float) -> float | None:
        if live_rate is None:
            return None
        return round(usd_amount * live_rate, 2)

    rate_ranges = {
        "floor":  {"usd": market_rates["floor"],  "local": to_local(market_rates["floor"])},
        "median": {"usd": market_rates["median"], "local": to_local(market_rates["median"])},
        "target": {"usd": market_rates["target"], "local": to_local(market_rates["target"])},
    }

    # --- 5. Compute Position Indicator ---
    position_indicator = None
    position_gap_pct = None
    if req.current_rate is not None:
        median = market_rates["median"]
        gap_pct = ((req.current_rate - median) / median) * 100
        position_gap_pct = round(gap_pct, 1)
        if gap_pct < -20:
            position_indicator = "Underpriced"
        elif gap_pct > 20:
            position_indicator = "Premium"
        else:
            position_indicator = "Market-Aligned"

    # --- 6. Compute Purchasing Power (monthly income scenarios) ---
    workloads = {
        "conservative": {"hours_per_month": 40,  "label": "Conservative (10 hrs/week)"},
        "typical":      {"hours_per_month": 80,  "label": "Typical (20 hrs/week)"},
        "optimistic":   {"hours_per_month": 120, "label": "Optimistic (30 hrs/week)"},
    }
    purchasing_power = {}
    for workload_key, workload in workloads.items():
        h = workload["hours_per_month"]
        purchasing_power[workload_key] = {
            "label": workload["label"],
            "floor_usd":  round(market_rates["floor"]  * h, 2),
            "median_usd": round(market_rates["median"] * h, 2),
            "target_usd": round(market_rates["target"] * h, 2),
            "floor_local":  to_local(market_rates["floor"]  * h),
            "median_local": to_local(market_rates["median"] * h),
            "target_local": to_local(market_rates["target"] * h),
        }

    col_reference = {
        "amount_usd": country_data["col_reference_usd"],
        "label": country_data["col_label"],
        "amount_local": to_local(country_data["col_reference_usd"]),
    }

    # --- 7. Read user settings for AI tone/language (if logged in) ---
    coach_language = "mixed"
    coach_tone = "Balanced"
    if user_id:
        user_settings = database.get_user_settings(user_id)
        if user_settings:
            coach_language = user_settings.get("coach_language", "mixed")
            coach_tone = user_settings.get("coach_tone", "Balanced")

    # --- 8. Call AI for all narrative/interpretive sections ---
    ai_sections = pulse.generate_pulse_ai_sections(
        role_label=role_data["label"],
        exp_bracket=exp_key,
        country_label=country_data["label"],
        market_rates=market_rates,
        demand=demand,
        saturation=saturation,
        timing_signal=timing_signal,
        current_rate=req.current_rate,
        coach_language=coach_language,
        coach_tone=coach_tone,
    )

    # --- 9. Assemble and return the full response ---
    return {
        "inputs": {
            "job_title":        role_key,
            "job_title_label":  role_data["label"],
            "years_experience": exp_key,
            "country":          country_key,
            "country_label":    country_data["label"],
            "currency":         country_data["currency"],
            "current_rate":     req.current_rate,
        },
        "position_indicator": {
            "status":       position_indicator,
            "gap_pct":      position_gap_pct,
            "current_rate": req.current_rate,
            "median":       market_rates["median"],
        },
        "rate_ranges": rate_ranges,
        "personal_positioning": {
            "current_rate": req.current_rate,
            "median":       market_rates["median"],
            "gap_pct":      position_gap_pct,
            "status":       position_indicator,
        },
        "market_demand": {
            "level":       demand,
            "explanation": ai_sections["demand_explanation"],
        },
        "competitor_density": {
            "saturation":            saturation,
            "specialization_pivots": ai_sections["specialization_pivots"],
        },
        "purchasing_power": {
            "scenarios":     purchasing_power,
            "col_reference": col_reference,
            "live_rate":     live_rate,
            "currency":      country_data["currency"],
        },
        "working_windows":   WORKING_WINDOWS,
        "what_it_takes":     ai_sections["what_it_takes"],
        "client_perspective": ai_sections["client_perspective"],
        "market_timing": {
            "signal":      timing_signal,
            "explanation": ai_sections["timing_explanation"],
        },
        "action_layer":      ai_sections["action_layer"],
        "positioning_brief": ai_sections["positioning_brief"],
    }


@app.get("/api/pulse/meta")
def get_pulse_meta():
    """
    Returns the valid input options for the Pulse form.
    No auth required — this is static reference data.
    """
    return {
        "roles": [
            {"key": key, "label": data["label"]}
            for key, data in MARKET_DATA.items()
        ],
        "countries": [
            {"key": key, "label": data["label"], "currency": data["currency"]}
            for key, data in COUNTRY_DATA.items()
        ],
        "experience_brackets": VALID_EXP_BRACKETS,
    }


# ── Coach ─────────────────────────────────────────────────────────────────────

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
        context_str = f"Latest income: {latest['total_received_usd']} USD."

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