"""
Smoke test for session-scoped history and deletion behavior.

Usage:
    python debug/test_session_history.py
"""

from __future__ import annotations

import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.chat import (
    create_session,
    delete_session,
    delete_recent_conversation,
    get_session_history,
    save_message,
)
from api.database import get_chat_conn


def assert_true(cond: bool, message: str):
    if not cond:
        raise AssertionError(message)


def main() -> int:
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    company_id = f"test_company_{uuid.uuid4().hex[:8]}"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"

    try:
        create_session(user_id, company_id, session_id, title="Smoke test session")

        for idx in range(7):
          # alternate user / assistant rows so the session looks realistic
            save_message(
                user_id,
                company_id,
                "user" if idx % 2 == 0 else "assistant",
                f"message {idx + 1}",
                session_id=session_id,
            )

        rows, has_more = get_session_history(user_id, company_id, session_id, limit=5)
        assert_true(len(rows) == 5, f"Expected 5 rows, got {len(rows)}")
        assert_true(has_more is True, "Expected has_more=True for a 7-row session")
        assert_true(rows[0]["content"] == "message 3", f"Expected oldest loaded message 3, got {rows[0]['content']}")
        assert_true(rows[-1]["content"] == "message 7", f"Expected newest loaded message 7, got {rows[-1]['content']}")

        older_rows, older_more = get_session_history(
            user_id,
            company_id,
            session_id,
            limit=5,
            before_id=rows[0]["id"],
        )
        assert_true(len(older_rows) == 2, f"Expected 2 older rows, got {len(older_rows)}")
        assert_true(older_more is False, "Expected has_more=False for the older slice")

        # Separate cleanup test for delete_recent_conversation.
        delete_test_session = f"{session_id}_delete"
        create_session(user_id, company_id, delete_test_session, title="Delete smoke test")
        save_message(user_id, company_id, "user", "delete anchor", session_id=delete_test_session)
        save_message(user_id, company_id, "assistant", "delete reply", session_id=delete_test_session)
        save_message(user_id, company_id, "user", "next turn", session_id=delete_test_session)
        save_message(user_id, company_id, "assistant", "next reply", session_id=delete_test_session)

        conn = get_chat_conn()
        anchor_row = conn.execute(
            """
            SELECT id FROM chat_history
            WHERE user_id=? AND company_id=? AND session_id=? AND role='user'
            ORDER BY id ASC LIMIT 1
            """,
            (user_id, company_id, delete_test_session),
        ).fetchone()
        conn.close()
        assert_true(anchor_row is not None, "Could not find delete anchor row")

        deleted = delete_recent_conversation(user_id, company_id, int(anchor_row["id"]))
        assert_true(deleted == 2, f"Expected to delete 2 rows, got {deleted}")

        conn = get_chat_conn()
        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM chat_history WHERE user_id=? AND company_id=? AND session_id=?",
            (user_id, company_id, delete_test_session),
        ).fetchone()["n"]
        conn.close()
        assert_true(remaining == 2, f"Expected 2 remaining rows after delete, got {remaining}")

        delete_session(user_id=user_id, company_id=company_id, session_id=session_id)
        delete_session(user_id=user_id, company_id=company_id, session_id=delete_test_session)

        print("OK: session history pagination and delete behavior passed.")
        return 0
    finally:
        try:
            delete_session(user_id=user_id, company_id=company_id, session_id=session_id)
        except Exception:
            pass
        try:
            delete_session(user_id=user_id, company_id=company_id, session_id=f"{session_id}_delete")
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
