"""(Re)seed the sqlite DB with FAKE PII so the SQLi tool has data to leak."""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import config  # noqa: E402


def main() -> None:
    os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, "
        "password TEXT, ssn TEXT, credit_card TEXT, role TEXT)"
    )
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
    conn.close()
    print(f"seeded {config.DB_PATH} with fake PII")


if __name__ == "__main__":
    main()
