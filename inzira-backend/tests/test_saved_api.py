"""Quick local check for /me/saved without live HTTP auth."""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import main

DB = ROOT / "inzira_local.db"


def inspect_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("tables:", [r[0] for r in cur.fetchall()])
    cur.execute("PRAGMA table_info(saved_sites)")
    print("saved_sites:", [r[1] for r in cur.fetchall()])
    cur.execute("PRAGMA table_info(push_subscriptions)")
    print("push_subscriptions:", [r[1] for r in cur.fetchall()])
    cur.execute("SELECT id, email FROM users LIMIT 5")
    print("users:", cur.fetchall())
    conn.close()


def test_with_mock_user():
    client = TestClient(main.app)
    user_id = sqlite3.connect(DB).execute("SELECT id FROM users LIMIT 1").fetchone()
    if not user_id:
        print("No users in DB — skip mock test")
        return

    uid = user_id[0]
    original = main.get_current_user

    def fake_user(request):
        from main import AuthUser, USER_ROLE_YOUTH

        row = sqlite3.connect(DB).execute(
            "SELECT id, firebase_uid, email, phone_e164, display_name, role FROM users WHERE id=?",
            (uid,),
        ).fetchone()
        return AuthUser(
            id=row[0],
            firebase_uid=row[1],
            email=row[2],
            phone_e164=row[3],
            display_name=row[4],
            role=row[5] or USER_ROLE_YOUTH,
        )

    main.get_current_user = fake_user
    try:
        r = client.get("/me")
        print("GET /me:", r.status_code, r.text[:200])
        r = client.get("/me/saved")
        print("GET /me/saved:", r.status_code, r.text[:200])
        r = client.post(
            "/me/saved",
            json={"url": "https://example.com/test", "title": "Example"},
        )
        print("POST /me/saved:", r.status_code, r.text[:200])
        r = client.put("/me/saved/example.com/notify", json={"enabled": True})
        print("PUT notify:", r.status_code, r.text[:200])
        r = client.post(
            "/me/push/subscribe",
            json={
                "endpoint": "https://push.test/endpoint",
                "keys": {"p256dh": "abc", "auth": "def"},
            },
        )
        print("POST push/subscribe:", r.status_code, r.text[:200])
    finally:
        main.get_current_user = original


if __name__ == "__main__":
    inspect_db()
    test_with_mock_user()
