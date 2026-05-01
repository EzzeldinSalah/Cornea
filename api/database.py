import sqlite3
import json
from datetime import datetime, timedelta
import random

DB_FILE = "cornea.db"

SNAPSHOT_COLUMNS = [
    "id",
    "created_at",
    "upwork_sync_date",
    "total_invoiced_usd",
    "total_fees_usd",
    "total_received_usd",
    "clients_json",
    "user_id",
    "source",
    "platform_transaction_id",
]

SNAPSHOT_DEFAULTS = {
    "id": "NULL",
    "created_at": "NULL",
    "upwork_sync_date": "NULL",
    "total_invoiced_usd": "0",
    "total_fees_usd": "0",
    "total_received_usd": "0",
    "clients_json": "NULL",
    "user_id": "1",
    "source": "'upwork'",
    "platform_transaction_id": "NULL",
}

OBSOLETE_SNAPSHOT_COLUMNS = {
    "egp_rate_at_date",
    "total_received_egp",
    "currency_code",
    "local_rate",
}


def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def migrate_snapshots_to_usd_only(cursor):
    cursor.execute("PRAGMA table_info(snapshots)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if not existing_columns.intersection(OBSOLETE_SNAPSHOT_COLUMNS):
        return

    cursor.execute("ALTER TABLE snapshots RENAME TO snapshots_legacy")
    cursor.execute("""
    CREATE TABLE snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        upwork_sync_date TEXT,
        total_invoiced_usd REAL,
        total_fees_usd REAL,
        total_received_usd REAL,
        clients_json TEXT,
        user_id INTEGER NOT NULL DEFAULT 1,
        source TEXT DEFAULT 'upwork',
        platform_transaction_id TEXT
    )
    """)

    select_exprs = [
        column if column in existing_columns else SNAPSHOT_DEFAULTS[column]
        for column in SNAPSHOT_COLUMNS
    ]
    cursor.execute(
        f"""
        INSERT INTO snapshots ({", ".join(SNAPSHOT_COLUMNS)})
        SELECT {", ".join(select_exprs)}
        FROM snapshots_legacy
        """
    )
    cursor.execute("DROP TABLE snapshots_legacy")


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
	        clients_json TEXT,
	        user_id INTEGER NOT NULL DEFAULT 1,
	        source TEXT DEFAULT 'upwork',
	        platform_transaction_id TEXT
	    )
	    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS coach_sessions (
        id INTEGER PRIMARY KEY,
        title TEXT,
        user_id INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS message_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        message TEXT
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS income_sources (
        id TEXT PRIMARY KEY,
        platform TEXT,
        name TEXT,
        status TEXT,
        last_sync TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        date TEXT,
        source TEXT,
        client_description TEXT,
        amount_usd REAL,
        amount_local REAL,
        platform_fee REAL,
        net_received REAL,
        user_id INTEGER,
        committed BOOLEAN DEFAULT 0,
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

    try:
        c.execute("ALTER TABLE snapshots ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE snapshots ADD COLUMN source TEXT DEFAULT 'upwork'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE snapshots ADD COLUMN platform_transaction_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE coach_sessions ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass

    migrate_snapshots_to_usd_only(c)

    conn.commit()
    conn.close()


def generate_mock_data(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM snapshots WHERE user_id = ?", (user_id,))
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

        client_data = []
        for _ in range(random.randint(1, 3)):
            client_data.append({
                "name": random.choice(clients),
                "billed": random.randint(300, 800),
                "effective_rate": random.randint(10, 30),
                "payment_wait_days": random.randint(10, 50),
            })

        c.execute("""
        INSERT INTO snapshots (
            created_at,
            upwork_sync_date,
            total_invoiced_usd,
            total_fees_usd,
            total_received_usd,
            clients_json,
            user_id,
            source,
            platform_transaction_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date_str,
            date_str,
            invoiced,
            fees,
            received_usd,
            json.dumps(client_data),
            user_id,
            "upwork",
            f"mock-{user_id}-{i}",
        ))

    conn.commit()
    conn.close()


def get_snapshots(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM snapshots WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def snapshot_usd_payload(snapshot: dict):
    return {key: snapshot.get(key) for key in SNAPSHOT_COLUMNS if key in snapshot}


def clear_snapshots(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM snapshots WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def create_session(title: str, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM coach_sessions")
    max_id = c.fetchone()[0]
    new_id = 0 if max_id is None else max_id + 1

    c.execute(
        "INSERT INTO coach_sessions (id, title, user_id) VALUES (?, ?, ?)",
        (new_id, title, user_id),
    )
    conn.commit()
    conn.close()
    return {"id": new_id, "title": title}


def get_coach_sessions(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM coach_sessions WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def rename_session(session_id: int, new_title: str, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE coach_sessions SET title = ? WHERE id = ? AND user_id = ?",
        (new_title, session_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_session(session_id: int, user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM coach_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
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
    c.execute("DELETE FROM snapshots WHERE user_id = ?", (user_id,))
    c.execute("SELECT id FROM coach_sessions WHERE user_id = ?", (user_id,))
    session_ids = [row[0] for row in c.fetchall()]
    c.execute("DELETE FROM coach_sessions WHERE user_id = ?", (user_id,))
    for sid in session_ids:
        try:
            c.execute("DELETE FROM message_store WHERE session_id = ?", (str(sid),))
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

    c.execute("SELECT * FROM snapshots WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    snapshots = [snapshot_usd_payload(dict(row)) for row in c.fetchall()]

    c.execute("SELECT * FROM coach_sessions WHERE user_id = ? ORDER BY id", (user_id,))
    sessions = [dict(row) for row in c.fetchall()]

    conn.close()

    return {
        "user": user_data,
        "settings": settings_data,
        "snapshots": snapshots,
        "coach_sessions": sessions,
    }


def get_coach_session_by_id(session_id: int, user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM coach_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


# --- MERGE & TRANSACTIONS ---

def get_income_sources(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM income_sources WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    
    # If no sources exist, create default ones
    if not rows:
        default_sources = [
            ("upwork_1", "Upwork", "Upwork Global", "connected", datetime.now().isoformat()),
            ("freelancer_1", "Freelancer", "Freelancer.com", "not connected", None),
            ("mostaql_1", "Mostaql", "Mostaql Account", "connected", datetime.now().isoformat())
        ]
        for src_id, plat, name, status, last_sync in default_sources:
            c.execute(
                "INSERT INTO income_sources (id, platform, name, status, last_sync, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                (src_id, plat, name, status, last_sync, user_id)
            )
        conn.commit()
        c.execute("SELECT * FROM income_sources WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        
    conn.close()
    return [dict(row) for row in rows]

def add_manual_transaction(user_id: int, data: dict):
    import uuid
    conn = get_connection()
    c = conn.cursor()
    
    tx_id = str(uuid.uuid4())
    date = data.get("date", datetime.now().isoformat())
    source = data.get("source_label", "Manual")
    desc = data.get("description", "Manual Entry")
    amt = float(data.get("amount", 0))
    
    # Simple fee deduction for manual (0%) or platforms
    fee_pct = 0.0
    if "Khamsat" in source or "Mostaql" in source:
        fee_pct = 0.20
        
    fee = amt * fee_pct
    net = amt - fee
    local_amt = 0 # UI calculates local equivalent if 0
    
    c.execute("""
    INSERT INTO transactions 
    (id, date, source, client_description, amount_usd, amount_local, platform_fee, net_received, user_id, committed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (tx_id, date, source, desc, amt, local_amt, fee, net, user_id))
    
    conn.commit()
    conn.close()
    return tx_id

def get_uncommitted_transactions(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE user_id = ? AND committed = 0 ORDER BY date DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def commit_transactions_to_snapshot(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM transactions WHERE user_id = ? AND committed = 0", (user_id,))
    uncommitted = c.fetchall()
    
    if not uncommitted:
        conn.close()
        return False
        
    total_invoiced = sum(row["amount_usd"] for row in uncommitted)
    total_fees = sum(row["platform_fee"] for row in uncommitted)
    total_received = sum(row["net_received"] for row in uncommitted)
    
    clients = []
    for row in uncommitted:
        clients.append({
            "name": row["client_description"],
            "billed": row["amount_usd"],
            "effective_rate": 0, # Placeholder
            "payment_wait_days": 0, # Placeholder
        })
        
    date_str = datetime.now().isoformat()
    
    c.execute("""
    INSERT INTO snapshots (
        created_at, upwork_sync_date, total_invoiced_usd, total_fees_usd, 
        total_received_usd, clients_json, user_id, source, platform_transaction_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, date_str, total_invoiced, total_fees, total_received, json.dumps(clients), user_id, "merged", f"merge-{date_str}"))
    
    c.execute("UPDATE transactions SET committed = 1 WHERE user_id = ? AND committed = 0", (user_id,))
    
    conn.commit()
    conn.close()
    return True

def sync_source_mock(source_id: str, user_id: int):
    import uuid
    import random
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT platform, name FROM income_sources WHERE id = ? AND user_id = ?", (source_id, user_id))
    src = c.fetchone()
    if not src:
        conn.close()
        return False
        
    platform, name = src
    date_str = datetime.now().isoformat()
    
    # Generate 1-3 random transactions
    for _ in range(random.randint(1, 3)):
        tx_id = str(uuid.uuid4())
        amt = random.randint(100, 1000)
        fee = amt * 0.10
        net = amt - fee
        desc = f"Client Project {random.randint(100, 999)}"
        c.execute("""
        INSERT INTO transactions 
        (id, date, source, client_description, amount_usd, amount_local, platform_fee, net_received, user_id, committed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (tx_id, date_str, platform, desc, amt, 0, fee, net, user_id))
        
    c.execute("UPDATE income_sources SET last_sync = ? WHERE id = ? AND user_id = ?", (date_str, source_id, user_id))
    
    conn.commit()
    conn.close()
    return True
