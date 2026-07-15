"""Validate the read-only ERP view required by the scheduled fraud engine."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.services.erp_db import get_erp_conn

REQUIRED = {
    "masterfn", "companyfn", "transaction_id", "user_id", "occurred_at",
    "created_at", "amount", "discount", "refund_count", "void_count",
    "invoice_modifications", "metadata",
}


def main() -> int:
    view = os.getenv("FRAUD_TRANSACTION_VIEW", "fraud_transaction_source")
    if not view.replace("_", "").isalnum():
        print("ERROR: invalid FRAUD_TRANSACTION_VIEW name")
        return 2
    conn = get_erp_conn(); cur = conn.cursor()
    try:
        cur.execute("""SELECT column_name FROM information_schema.columns
                       WHERE table_schema=current_schema() AND table_name=%s""", (view,))
        actual = {row[0] for row in cur.fetchall()}
        missing = sorted(REQUIRED - actual)
        if missing:
            print(f"ERROR: {view} is missing columns: {', '.join(missing)}")
            return 1
        cur.execute(f"SELECT COUNT(*) FROM {view}")
        print(f"OK: {view} contract valid; rows={cur.fetchone()[0]}")
        return 0
    finally:
        cur.close(); conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
