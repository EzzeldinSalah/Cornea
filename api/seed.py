import json
import random
import sqlite3
from datetime import datetime, timedelta

from passlib.context import CryptContext
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

import database


CLIENT_NAMES = [
    "Omar Elmasry",
    "Nour Tech",
    "Amina Sol",
    "Atlas Ventures",
    "Rana Malik",
    "BrightLabs",
    "Mona Zidane",
    "Northwind Co",
]

SESSION_SEEDS = [
    (
        "April Review",
        [
            ("user", "What changed since last month?"),
            ("assistant", "Your net income rose, but transfer fees also increased. Focus on fewer, higher-paying clients."),
            ("user", "Which client is the slowest?"),
            ("assistant", "Your slowest payer is Northwind Co. Average delay is over 30 days."),
        ],
    ),
    (
        "Pricing Strategy",
        [
            ("user", "Am I charging enough?"),
            ("assistant", "Your effective rate is below your top month. Push rates by 10-15% on new contracts."),
            ("user", "What would be a fair target?"),
            ("assistant", "Aim for an effective rate above $45/hr based on your recent averages."),
        ],
    ),
    (
        "Client Mix",
        [
            ("user", "Why did last month feel tight?"),
            ("assistant", "Two clients had late payments and your income dropped. Reduce exposure to slow payers."),
            ("user", "Who should I replace?"),
            ("assistant", "Replace your lowest effective-rate client first; it drags the average down."),
        ],
    ),
    (
        "Cash Flow",
        [
            ("user", "How stable is my cash flow?"),
            ("assistant", "You have high variance. Add at least one stable monthly retainer."),
            ("user", "What metric should I watch?"),
            ("assistant", "Track average payment wait and target under 14 days."),
        ],
    ),
    (
        "Monthly Goals",
        [
            ("user", "Set a realistic target for next month."),
            ("assistant", "Based on your best month, aim for $2,400 invoiced with fast-paying clients."),
            ("user", "What if I miss it?"),
            ("assistant", "If you miss, re-balance client mix rather than adding low-rate work."),
        ],
    ),
]


def ensure_demo_user(conn):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_context.hash("demo1234")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id = 1")
    row = c.fetchone()
    if row:
        c.execute(
            "UPDATE users SET email = ?, password_hash = ?, google_id = NULL WHERE id = 1",
            ("demo@cornea.app", password_hash),
        )
    else:
        c.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (1, "demo@cornea.app", password_hash, datetime.now().isoformat()),
        )
    conn.commit()


def seed_snapshots(conn):
    c = conn.cursor()
    c.execute("DELETE FROM snapshots WHERE user_id = 1")
    try:
        c.execute("DELETE FROM monthly_summaries WHERE user_id = 1")
    except sqlite3.OperationalError:
        try:
            c.execute("DELETE FROM monthly_summaries")
        except sqlite3.OperationalError:
            pass

    now = datetime.now()
    start_date = now - timedelta(days=30 * 14)
    total_snapshots = 40
    step_days = int((30 * 14) / total_snapshots)

    bad_month_index = 3
    great_month_index = 10

    for i in range(total_snapshots):
        created_at = start_date + timedelta(days=step_days * i)
        month_index = (created_at.year - start_date.year) * 12 + (created_at.month - start_date.month)

        if month_index == bad_month_index:
            invoiced = random.randint(200, 650)
            wait_min, wait_max = 35, 61
        elif month_index == great_month_index:
            invoiced = random.randint(2200, 2800)
            wait_min, wait_max = 3, 12
        else:
            invoiced = random.randint(700, 2200)
            wait_min, wait_max = 7, 45

        source = random.choices(
            ["upwork", "freelancer", "manual"],
            weights=[0.6, 0.25, 0.15],
            k=1,
        )[0]

        fee_pct = 0.2 if source == "upwork" else 0.1 if source == "freelancer" else 0.0
        fees = round(invoiced * fee_pct, 2)
        received_usd = round(invoiced - fees, 2)

        client_count = random.randint(2, 4)
        clients = random.sample(CLIENT_NAMES, k=client_count)
        weights = [random.random() for _ in range(client_count)]
        weight_sum = sum(weights)

        client_data = []
        for idx, client_name in enumerate(clients):
            billed = round(invoiced * (weights[idx] / weight_sum), 2)
            effective_rate = round(random.uniform(18, 70), 2)
            payment_wait_days = random.randint(wait_min, wait_max)
            client_data.append({
                "name": client_name,
                "billed": billed,
                "effective_rate": effective_rate,
                "payment_wait_days": payment_wait_days,
            })

        c.execute(
            """
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
            """,
            (
                created_at.strftime("%Y-%m-%dT%H:%M:%S"),
                created_at.strftime("%Y-%m-%dT%H:%M:%S"),
                invoiced,
                fees,
                received_usd,
                json.dumps(client_data),
                1,
                source,
                f"seed-1-{i}",
            ),
        )

    conn.commit()


def seed_sessions(conn):
    c = conn.cursor()
    c.execute("SELECT id FROM coach_sessions WHERE user_id = 1")
    session_ids = [row[0] for row in c.fetchall()]
    c.execute("DELETE FROM coach_sessions WHERE user_id = 1")
    for sid in session_ids:
        try:
            c.execute("DELETE FROM message_store WHERE session_id = ?", (str(sid),))
        except sqlite3.OperationalError:
            pass

    c.execute("SELECT MAX(id) FROM coach_sessions")
    max_id = c.fetchone()[0]
    next_id = 1 if max_id is None else max_id + 1

    session_ids_to_seed = []
    for title, messages in SESSION_SEEDS:
        session_id = next_id
        next_id += 1
        c.execute(
            "INSERT INTO coach_sessions (id, title, user_id) VALUES (?, ?, ?)",
            (session_id, title, 1),
        )
        session_ids_to_seed.append((session_id, messages))

    conn.commit()
    conn.close()

    # Now use SQLAlchemy (via LangChain) with no raw conn holding a lock
    for session_id, messages in session_ids_to_seed:
        history = SQLChatMessageHistory(str(session_id), "sqlite:///cornea.db")
        for role, text in messages:
            if role == "user":
                history.add_message(HumanMessage(content=text))
            else:
                history.add_message(AIMessage(content=text))


def seed_settings(conn):
    database.upsert_user_settings(1, {
        "display_name": "Demo User",
        "primary_currency": "EGP",
        "primary_language": "English",
        "coach_language": "mixed",
        "coach_tone": "Balanced",
        "notify_weekly_digest": True,
        "notify_slow_month": True,
        "notify_late_payment": True,
        "notify_exchange_rate": True,
    })


def main():
    database.init_db()
    conn = database.get_connection()
    ensure_demo_user(conn)
    seed_settings(conn)
    seed_snapshots(conn)
    conn.close()
    # seed_sessions manages its own conn lifecycle (closes before SQLAlchemy writes)
    conn2 = database.get_connection()
    seed_sessions(conn2)

    print("Seed complete")
    print("- User: demo@cornea.app / demo1234 (id=1)")
    print("- Snapshots: 40 across 14 months")
    print("- Coach sessions: 5 with messages")


if __name__ == "__main__":
    main()
