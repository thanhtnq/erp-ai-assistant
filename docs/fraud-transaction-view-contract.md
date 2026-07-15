# Fraud Transaction Source Contract

The scheduled fraud engine intentionally reads a normalized, read-only PostgreSQL view.
ERP audit columns differ between deployments, so the view must be mapped and approved by
the ERP/database owner instead of embedding guessed source columns in application code.

## Required columns

| Column | Type | Meaning |
|---|---|---|
| `masterfn`, `companyfn` | text | Mandatory tenant scope |
| `transaction_id` | text | Stable source transaction/document identifier |
| `user_id` | text | User/service that created the event |
| `occurred_at` | timestamp | Business transaction timestamp |
| `created_at` | timestamp | Immutable database/audit creation timestamp |
| `amount` | numeric | Transaction amount in the approved comparison currency |
| `discount` | numeric | Effective discount percentage or approved normalized measure |
| `refund_count` | integer | Refund events associated with this transaction/user period |
| `void_count` | integer | Void events associated with this transaction/user period |
| `invoice_modifications` | integer | Number of persisted invoice revisions |
| `metadata` | json/jsonb | Evidence fields safe to retain with an alert |

The view must enforce tenant fields and must not expose secrets or unrestricted personal
data in `metadata`. Use immutable creation time for backdate detection. Do not substitute
accounting `date_trans` for `created_at`.

Validate after the DBA creates the view:

```powershell
.\.venv\Scripts\python.exe scripts\validate_fraud_transaction_view.py
```

Scheduler activation is allowed only after this command succeeds for the target database.

An reviewed migration candidate for the confirmed Sales and Purchase header fields is
available at `scripts/sql/create_fraud_transaction_source.sql`. It deliberately excludes
unconfirmed login-session data. `date_post` is used as the creation/post audit timestamp
and must be approved by the ERP owner before applying the migration.
