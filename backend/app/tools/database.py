"""sql_query tool — SQL injection + sensitive data disclosure.

  * SAST: raw string-formatted SQL, no parameterization.
  * LLM02: seeded table holds fake PII / payment data the agent will return.

All rows are FAKE TEST DATA. The DB is (re)seeded from data/seed.py.
"""
from __future__ import annotations

import os
import sqlite3

from app import config


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    _ensure_seed(conn)
    return conn


def _ensure_seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY, username TEXT, email TEXT, "
        "password TEXT, ssn TEXT, credit_card TEXT, role TEXT)"
    )
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
            [
                (1, "alice", "alice@example.com", "Password1!", "111-11-1111",
                 "4111111111111111", "user"),
                (2, "bob", "bob@example.com", "hunter2", "222-22-2222",
                 "5500005555555559", "user"),
                (3, "admin", "admin@example.com", "SuperSecret123!", "999-99-9999",
                 "340000000000009", "admin"),
            ],
        )
        conn.commit()


def run(arguments: dict) -> str:
    user_input = str(arguments.get("input", ""))

    # If the caller supplied raw SQL, run it verbatim; otherwise build a query
    # by string interpolation (classic SQLi sink).
    if user_input.strip().lower().startswith("select"):
        query = user_input
    else:
        # e.g. input "alice" -> injectable lookup
        query = f"SELECT * FROM users WHERE username = '{user_input}'"  # nosec

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(query)  # intentional SQLi sink (no params)
        rows = cur.fetchall()
        return f"query: {query}\nrows: {rows}"
    except Exception as exc:  # verbose DB errors leak schema (info disclosure)
        return f"SQL error for query [{query}]: {exc}"
    finally:
        conn.close()
