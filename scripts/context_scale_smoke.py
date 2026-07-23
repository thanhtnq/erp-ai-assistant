"""
Smoke test for session-scoped chat/result context at multi-user scale.

This is intentionally separate from the normal unit suite so it can be run on
local/server when checking deployment capacity without making CI slower.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _connect(path: Path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _create_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            company_id TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE INDEX idx_chat_history_session_scope
        ON chat_history(user_id, company_id, session_id, id DESC)
    """)
    conn.execute("""
        CREATE TABLE chat_result_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            company_id TEXT NOT NULL DEFAULT '',
            session_id TEXT NOT NULL DEFAULT '',
            source_query TEXT NOT NULL DEFAULT '',
            shape TEXT NOT NULL DEFAULT '',
            row_count INTEGER NOT NULL DEFAULT 0,
            columns_json TEXT NOT NULL DEFAULT '[]',
            chartable INTEGER NOT NULL DEFAULT 0,
            default_chart TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX idx_chat_result_context_scope
        ON chat_result_context(user_id, company_id, session_id, id DESC)
    """)
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--messages", type=int, default=4)
    args = parser.parse_args()

    import api.chat as chat

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "chat_scale.db"
        conn = _connect(db_path)
        try:
            _create_schema(conn)
        finally:
            conn.close()

        start = time.perf_counter()
        conn = _connect(db_path)
        try:
            now = "2026-07-23T00:00:00"
            history_rows = []
            result_rows = []
            for idx in range(args.users):
                user_id = f"user{idx}"
                session_id = f"sess{idx}"
                for msg_idx in range(args.messages):
                    history_rows.append((user_id, "companyA", "user", f"question {idx}-{msg_idx}", now, session_id))
                    history_rows.append((user_id, "companyA", "assistant", f"answer {idx}-{msg_idx}", now, session_id))
                result_rows.append(
                    (
                        user_id,
                        "companyA",
                        session_id,
                        "top customers",
                        "table",
                        2,
                        '["Customer","Amount"]',
                        1,
                        "bar",
                        now,
                    )
                )
            conn.executemany("""
                INSERT INTO chat_history (user_id, company_id, role, content, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, history_rows)
            conn.executemany("""
                INSERT INTO chat_result_context
                    (user_id, company_id, session_id, source_query, shape, row_count,
                     columns_json, chartable, default_chart, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, result_rows)
            conn.commit()
        finally:
            conn.close()

        original_get_chat_conn = chat.get_chat_conn

        def get_conn():
            return _connect(db_path)

        chat.get_chat_conn = get_conn
        try:

            target = args.users // 2
            rows, has_more = chat.get_session_history(f"user{target}", "companyA", f"sess{target}", limit=args.messages * 2 + 2)
            result_context = chat.get_latest_result_context(f"user{target}", "companyA", f"sess{target}")
        finally:
            chat.get_chat_conn = original_get_chat_conn

        elapsed = time.perf_counter() - start
        contents = [dict(row)["content"] for row in rows]
        expected_first = f"question {target}-0"
        expected_last = f"answer {target}-{args.messages - 1}"
        assert not has_more, "target session unexpectedly paginated"
        assert contents[0] == expected_first, f"cross-session leak or ordering bug: {contents[:3]}"
        assert contents[-1] == expected_last, f"cross-session leak or ordering bug: {contents[-3:]}"
        assert result_context.get("chartable") == 1, "latest result context was not chartable"

    print(
        f"OK users={args.users} messages_per_user={args.messages} "
        f"rows_checked={len(rows)} elapsed_sec={elapsed:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
