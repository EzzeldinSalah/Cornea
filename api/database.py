import sqlite3
import json
from datetime import datetime, timedelta
import random

DB_FILE = "cornea.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        upwork_sync_date TEXT,
        total_invoiced_usd REAL,
        total_fees_usd REAL,
        total_received_usd REAL,
        egp_rate_at_date REAL,
        total_received_egp REAL,
        clients_json TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS monthly_summaries (
        month TEXT PRIMARY KEY,
        invoiced_usd REAL,
        received_egp REAL,
        avg_payment_wait_days REAL,
        top_client TEXT,
        worst_client TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS coach_sessions (
        id INTEGER PRIMARY KEY,
        title TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        google_id TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        display_name TEXT,
        avatar_url TEXT,
        primary_language TEXT DEFAULT 'English',
        primary_currency TEXT DEFAULT 'USD',
        secondary_currency_display BOOLEAN DEFAULT 1,
        coach_language TEXT DEFAULT 'mixed',
        coach_tone TEXT DEFAULT 'Balanced',
        notify_weekly_digest BOOLEAN DEFAULT 1,
        notify_slow_month BOOLEAN DEFAULT 1,
        notify_late_payment BOOLEAN DEFAULT 1,
        notify_exchange_rate BOOLEAN DEFAULT 0,
        avatar_blob BLOB,
        avatar_mime TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    try:
        c.execute("ALTER TABLE user_settings ADD COLUMN avatar_blob BLOB")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE user_settings ADD COLUMN avatar_mime TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def generate_mock_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM snapshots")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    clients = ["TechCorp LLC", "Ahmad Hassan", "Global Solutions", "Acme Corp"]
    base_date = datetime.now() - timedelta(days=180)

    for i in range(1, 25):
        date_str = (base_date + timedelta(days=i * 7)).strftime("%Y-%m-%dT%H:%M:%S")
        invoiced = random.randint(800, 2000)
        fees = invoiced * 0.10
        received_usd = invoiced - fees
        egp_rate = random.uniform(47.0, 50.0)
        received_egp = received_usd * egp_rate

        client_data = []
        for _ in range(random.randint(1, 3)):
            client_data.append({
                "name": random.choice(clients),
                "billed": random.randint(300, 800),
                "effective_rate": random.randint(10, 30),
                "payment_wait_days": random.randint(10, 50),
            })

        c.execute("""
        INSERT INTO snapshots (created_at, upwork_sync_date, total_invoiced_usd, total_fees_usd,
                               total_received_usd, egp_rate_at_date, total_received_egp, clients_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, date_str, invoiced, fees, received_usd, egp_rate, received_egp,
              json.dumps(client_data)))

    conn.commit()
    conn.close()


def get_snapshots():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM snapshots ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_snapshots():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM snapshots")
    conn.commit()
    conn.close()


def create_session(title: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM coach_sessions")
    max_id = c.fetchone()[0]
    new_id = 0 if max_id is None else max_id + 1

    c.execute("INSERT INTO coach_sessions (id, title) VALUES (?, ?)", (new_id, title))
    conn.commit()
    conn.close()
    return {"id": new_id, "title": title}


def get_coach_sessions():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM coach_sessions ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def rename_session(session_id: int, new_title: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE coach_sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM coach_sessions WHERE id = ?", (session_id,))
    try:
        c.execute("DELETE FROM message_store WHERE session_id = ?", (str(session_id),))
    except sqlite3.OperationalError:
        pass  # message_store is created by LangChain on first use
    conn.commit()
    conn.close()


def get_user_by_email(email: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user_with_password(email: str, password_hash: str):
    conn = get_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    try:
        c.execute("INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                  (email, password_hash, created_at))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    finally:
        conn.close()
    return user_id


def upsert_google_user(email: str, google_id: str):
    conn = get_connection()
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE users SET google_id = ? WHERE id = ?", (google_id, row[0]))
        user_id = row[0]
    else:
        c.execute("INSERT INTO users (email, google_id, created_at) VALUES (?, ?, ?)",
                  (email, google_id, created_at))
        user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id


def update_user_password(user_id: int, new_password_hash: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM coach_sessions")
    try:
        c.execute("DELETE FROM message_store")
    except sqlite3.OperationalError:
        pass
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_settings(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    if "avatar_blob" in data:
        del data["avatar_blob"]
    return data


def upsert_user_settings(user_id: int, settings: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))

    cols = [
        'display_name', 'avatar_url', 'primary_language', 'primary_currency',
        'secondary_currency_display', 'coach_language', 'coach_tone',
        'notify_weekly_digest', 'notify_slow_month', 'notify_late_payment',
        'notify_exchange_rate',
    ]
    defaults = {
        'primary_language': 'English', 'primary_currency': 'USD',
        'secondary_currency_display': True, 'coach_language': 'mixed',
        'coach_tone': 'Balanced', 'notify_weekly_digest': True,
        'notify_slow_month': True, 'notify_late_payment': True,
        'notify_exchange_rate': False,
    }
    values = [settings.get(col, defaults.get(col)) for col in cols]

    if c.fetchone():
        set_clause = ", ".join(f"{col} = ?" for col in cols)
        c.execute(f"UPDATE user_settings SET {set_clause} WHERE user_id = ?", (*values, user_id))
    else:
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        c.execute(
            f"INSERT INTO user_settings (user_id, {col_names}) VALUES (?, {placeholders})",
            (user_id, *values),
        )

    conn.commit()
    conn.close()


def save_user_avatar(user_id: int, blob: bytes, mime: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE user_settings SET avatar_blob = ?, avatar_mime = ? WHERE user_id = ?",
                  (blob, mime, user_id))
    else:
        c.execute("INSERT INTO user_settings (user_id, avatar_blob, avatar_mime) VALUES (?, ?, ?)",
                  (user_id, blob, mime))
    conn.commit()
    conn.close()


def export_user_data(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    user_data = dict(user) if user else {}

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    settings = c.fetchone()
    settings_data = {}
    if settings:
        settings_data = dict(settings)
        if "avatar_blob" in settings_data:
            del settings_data["avatar_blob"]

    c.execute("SELECT * FROM snapshots ORDER BY created_at DESC")
    snapshots = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM coach_sessions ORDER BY id")
    sessions = [dict(row) for row in c.fetchall()]

    conn.close()

    return {
        "user": user_data,
        "settings": settings_data,
        "snapshots": snapshots,
        "coach_sessions": sessions,
    }
