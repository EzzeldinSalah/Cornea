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
    conn.commit()
    conn.close()

def generate_mock_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM snapshots")
    if c.fetchone()[0] > 0:
        return
    
    clients = ["TechCorp LLC", "Ahmad Hassan", "Global Solutions", "Acme Corp"]
    
    base_date = datetime.now() - timedelta(days=180)
    for i in range(1, 25):
        date_str = (base_date + timedelta(days=i*7)).strftime("%Y-%m-%dT%H:%M:%S")
        month_str = (base_date + timedelta(days=i*7)).strftime("%Y-%m")
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
                "payment_wait_days": random.randint(10, 50)
            })
            
        c.execute("""
        INSERT INTO snapshots (created_at, upwork_sync_date, total_invoiced_usd, total_fees_usd, 
                               total_received_usd, egp_rate_at_date, total_received_egp, clients_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, date_str, invoiced, fees, received_usd, egp_rate, received_egp, json.dumps(client_data)))
    
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
        pass # message_store might not exist yet if langchain hasn't initialized it
    conn.commit()
    conn.close()
