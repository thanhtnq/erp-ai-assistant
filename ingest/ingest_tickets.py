"""
ERP AI — Ticket Ingest Pipeline
Fetches resolved tickets from PostgreSQL and ingests into knowledge DB.

Usage:
    python ingest_tickets.py                    # ingest all new tickets
    python ingest_tickets.py --dry-run          # preview without saving
    python ingest_tickets.py --force            # re-process all tickets
    python ingest_tickets.py --company ABC      # ingest specific company only
    python ingest_tickets.py --limit 50         # limit number of tickets
    python ingest_tickets.py --workers 1        # sequential (debug mode)
"""

import argparse
import json
import logging
import re
import sqlite3
import sys
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import google.generativeai as genai

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("[ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from ingest_config import (
    PG_CONFIG as DB_CONFIG,
    TICKET_QUERY,
    FILTER_COMPANY_FN,
    KNOWLEDGE_DB,
    GEMINI_API_KEY,
    LLM_MODEL_TICKET as LLM_MODEL,
    AVAILABLE_DOMAINS,
    AVAILABLE_TYPES,
    MIN_DESCRIPTION_LENGTH,
    MIN_SOLUTION_LENGTH,
    SKIP_EXISTING,
    LLM_WORKERS,
    MAX_LLM_RETRIES,
    LLM_RETRY_DELAY,
)

genai.configure(api_key=GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel(LLM_MODEL)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable=None, **kwargs):
        if iterable:
            return iterable
        class FakeTqdm:
            def update(self, n=1): pass
            def write(self, s): print(s)
            def close(self): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return FakeTqdm()

# ─── Logging ──────────────────────────────────────────────────────────────────

_log_dir = Path(__file__).parent.parent / "schedule"
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "ingest_tickets.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ingest_tickets")

# ── Embedding + ChromaDB (optional) ──────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from embedding_helper import batch_upsert_entries, CHROMA_AVAILABLE
    if CHROMA_AVAILABLE:
        print("[OK] ChromaDB ready — tickets will be indexed")
    else:
        print("[--] ChromaDB not available — skipping vector indexing")
except ImportError:
    CHROMA_AVAILABLE = False
    def batch_upsert_entries(*a, **kw): return 0
    print("[--] embedding_helper not found — skipping vector indexing")

# ─── PostgreSQL ───────────────────────────────────────────────────────────────

def fetch_tickets(company: str = None, limit: int = None) -> list:
    """Fetch resolved tickets from PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        print(f"[ERROR] Cannot connect to PostgreSQL: {e}")
        sys.exit(1)

    query  = TICKET_QUERY
    params = []

    filter_fn = company or FILTER_COMPANY_FN
    if filter_fn:
        query += f" AND main.companyfn = %s"
        params.append(filter_fn)

    if limit:
        query += f" LIMIT %s"
        params.append(limit)

    try:
        cur.execute(query, params or None)
        rows = cur.fetchall()
        print(f"[OK] Fetched {len(rows)} tickets from PostgreSQL")
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

# ─── Knowledge DB ─────────────────────────────────────────────────────────────

def get_knowledge_conn():
    conn = sqlite3.connect(KNOWLEDGE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_or_create_company(conn, code: str) -> int | None:
    if not code:
        return None
    row = conn.execute("SELECT id FROM companies WHERE code = ?", (code,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO companies (code, name) VALUES (?, ?)", (code, code)
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_domain(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM domains WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO domains (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def get_or_create_feature(conn, domain_id: int, name: str) -> int:
    row = conn.execute(
        "SELECT id FROM features WHERE domain_id = ? AND name = ?",
        (domain_id, name)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO features (domain_id, name, sort_order) VALUES (?, ?, 9999)",
        (domain_id, name)
    )
    conn.commit()
    return cur.lastrowid


def ticket_already_ingested(conn, ticket_id: str, company_id: int | None) -> bool:
    """Check if ticket already exists in knowledge DB."""
    row = conn.execute("""
        SELECT ev.id FROM entry_versions ev
        JOIN entries e ON ev.entry_id = e.id
        WHERE ev.source_type = 'ticket'
        AND ev.source_ref = ?
        AND ev.company_id IS ?
        AND ev.is_current = 1
        LIMIT 1
    """, (str(ticket_id), company_id)).fetchone()
    return row is not None


def save_ticket_entry(conn, ticket: dict, classification: dict,
                      company_id: int | None) -> dict | None:
    """Save classified ticket as a knowledge entry.
    Returns dict(entry_id, version_id, domain, feature) on success, None on failure.
    Caller must commit — this function does NOT commit.
    """
    domain_name  = classification["domain"]
    entry_type   = classification["entry_type"]
    feature_name = classification["feature"]
    summary      = classification["summary"]
    steps        = classification["steps"]
    notes        = classification["notes"]

    domain_id  = get_or_create_domain(conn, domain_name)
    feature_id = get_or_create_feature(conn, domain_id, feature_name)

    entry_name = ticket["subject"] or f"Ticket {ticket['ticket_id']}"
    row = conn.execute(
        "SELECT id FROM entries WHERE feature_id = ? AND name = ?",
        (feature_id, entry_name)
    ).fetchone()

    if row:
        entry_id = row["id"]
    else:
        cur = conn.execute("""
            INSERT INTO entries (feature_id, name, type, summary, sort_order)
            VALUES (?, ?, ?, ?, 9999)
        """, (feature_id, entry_name, entry_type, summary))
        entry_id = cur.lastrowid

    conn.execute("""
        UPDATE entry_versions SET is_current = 0
        WHERE entry_id = ? AND company_id IS ?
    """, (entry_id, company_id))

    cur_ver = conn.execute("""
        SELECT COALESCE(MAX(version), 0) FROM entry_versions
        WHERE entry_id = ? AND company_id IS ?
    """, (entry_id, company_id)).fetchone()[0]

    raw_content = f"Issue: {ticket['description'] or ''}\n\nSolution: {ticket['solution'] or ''}"

    cur = conn.execute("""
        INSERT INTO entry_versions
            (entry_id, company_id, version, steps, notes, raw_content,
             source_type, source_ref, is_current)
        VALUES (?, ?, ?, ?, ?, ?, 'ticket', ?, 1)
    """, (
        entry_id, company_id, cur_ver + 1,
        json.dumps(steps, ensure_ascii=False),
        json.dumps(notes, ensure_ascii=False),
        raw_content,
        str(ticket["ticket_id"])
    ))
    version_id = cur.lastrowid   # no extra SELECT needed

    return {
        "entry_id":   entry_id,
        "version_id": version_id,
        "domain":     domain_name,
        "feature":    feature_name,
    }

# ─── LLM ──────────────────────────────────────────────────────────────────────

def call_llm(prompt: str) -> str:
    """Call Gemini with exponential-backoff retry."""
    last_exc = None
    for attempt in range(MAX_LLM_RETRIES):
        try:
            resp = _gemini_model.generate_content(
                prompt,
                generation_config={"temperature": 0.1},
            )
            return resp.text
        except Exception as e:
            last_exc = e
            if attempt < MAX_LLM_RETRIES - 1:
                wait = LLM_RETRY_DELAY * (2 ** attempt)
                print(f"  [!] LLM error (attempt {attempt+1}/{MAX_LLM_RETRIES}): {e} — retrying in {wait}s")
                _time.sleep(wait)

    log.warning(f"LLM failed after {MAX_LLM_RETRIES} attempts: {last_exc}")
    return ""


def classify_ticket(ticket: dict) -> dict | None:
    """Use LLM to classify ticket into domain/feature/type and extract steps."""
    subject     = (ticket.get("subject") or "").strip()
    description = (ticket.get("description") or "").strip()
    solution    = (ticket.get("solution") or "").strip()

    if not subject and not description:
        return None

    domains_list = "\n".join(f"  - {d}" for d in AVAILABLE_DOMAINS)
    types_list   = "\n".join(f"  - {t}" for t in AVAILABLE_TYPES)

    prompt = f"""You are an ERP support ticket classifier for Globe3 ERP.

Classify this support ticket and extract structured resolution steps.

Ticket Subject: {subject}
Ticket Description: {description}
Resolution/Solution: {solution}

Available domains (choose the most relevant one):
{domains_list}

Available entry types:
{types_list}
  - error_fix: user encountered a bug or error
  - faq: user asked how something works
  - reference: request for field/config information
  - procedure: request for how to do a task

Return ONLY valid JSON:
{{
  "domain": "one of the available domains above",
  "feature": "specific feature within the domain (e.g. Sales Invoice, Purchase Order, Leave Application)",
  "entry_type": "one of the available entry types above",
  "summary": "one sentence describing the issue and its resolution",
  "steps": [
    {{
      "step_number": 1,
      "action": "verb phrase describing the action",
      "description": "detailed explanation including field names and values",
      "fields": ["relevant field names"],
      "image": null
    }}
  ],
  "notes": ["important warnings or conditions"]
}}

Rules:
- steps should be based on the solution/resolution
- If no solution provided, steps can be empty []
- notes should include any important conditions or caveats
- Answer in English
"""

    raw = call_llm(prompt).strip()
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw, flags=re.MULTILINE)

    try:
        data = json.loads(raw)
        if not data.get("domain") or data["domain"] not in AVAILABLE_DOMAINS:
            data["domain"] = "General"
        if not data.get("entry_type") or data["entry_type"] not in AVAILABLE_TYPES:
            data["entry_type"] = "error_fix"
        if not data.get("feature"):
            data["feature"] = "Support Tickets"
        return data
    except:
        m = re.search(r'\{[\s\S]*"domain"[\s\S]*\}', raw)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
    log.warning(f"Classification failed for: {subject[:50]}")
    return None

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest ERP tickets into Knowledge DB")
    parser.add_argument("--dry-run",  action="store_true", help="Preview without saving")
    parser.add_argument("--force",    action="store_true", help="Re-process existing tickets")
    parser.add_argument("--company",  help="Filter by company fn (e.g. ABC001)")
    parser.add_argument("--limit",    type=int, help="Max tickets to process")
    parser.add_argument("--workers",  type=int, default=None,
                        help=f"Parallel LLM workers (default: LLM_WORKERS={LLM_WORKERS}; use 1 for sequential/debug)")
    args = parser.parse_args()

    if not Path(KNOWLEDGE_DB).exists():
        print(f"[ERROR] Knowledge DB not found: {KNOWLEDGE_DB}")
        print(f"        Run: python knowledge_schema.py first")
        sys.exit(1)

    workers = args.workers or LLM_WORKERS
    print(f"\nERP Ticket Ingest — {'DRY RUN' if args.dry_run else 'LIVE'} | workers={workers}")
    print(f"{'─' * 55}")

    # ── Fetch tickets ─────────────────────────────────────────────
    tickets = fetch_tickets(company=args.company, limit=args.limit)

    if not tickets:
        print("No tickets found.")
        return

    # ── Filter ────────────────────────────────────────────────────
    conn = get_knowledge_conn()
    to_process = []

    for t in tickets:
        desc = (t.get("description") or "").strip()
        sol  = (t.get("solution") or "").strip()
        if len(desc) < MIN_DESCRIPTION_LENGTH and len(sol) < MIN_SOLUTION_LENGTH:
            continue

        if not args.force and SKIP_EXISTING:
            company_id = get_or_create_company(conn, t.get("company_code")) if not args.dry_run else None
            if ticket_already_ingested(conn, t["ticket_id"], company_id):
                continue

        to_process.append(t)

    print(f"Tickets to process: {len(to_process)} / {len(tickets)} total")
    print(f"(skipped {len(tickets) - len(to_process)} — too short or already ingested)\n")

    if not to_process:
        print("Nothing to do.")
        conn.close()
        return

    # ── Phase A: Parallel LLM classification ─────────────────────
    stats = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}

    print(f"⚡ Classifying {len(to_process)} tickets with {workers} workers...")
    classifications: dict = {}  # ticket_id → classification dict or None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(classify_ticket, t): t["ticket_id"]
            for t in to_process
        }
        pbar_classify = tqdm(
            as_completed(futures), total=len(futures),
            desc="Classifying", unit=" ticket", ncols=60,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}{unit} [{elapsed}<{remaining}]"
        )
        for fut in pbar_classify:
            tid = futures[fut]
            try:
                classifications[tid] = fut.result()
            except Exception as e:
                log.warning(f"Classify worker error for ticket {tid}: {e}")
                classifications[tid] = None
        pbar_classify.close()

    # ── Phase B: Serial DB writes + collect ChromaDB payloads ─────
    print(f"\nSaving to DB...")
    chroma_payloads = []

    pbar = tqdm(to_process, desc="Saving", unit=" ticket", ncols=60,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}{unit} [{elapsed}<{remaining}]")

    for ticket in pbar:
        subject      = (ticket.get("subject") or "")[:60]
        company_code = ticket.get("company_code") or ""
        tid          = ticket["ticket_id"]

        classification = classifications.get(tid)

        if not classification:
            tqdm.write(f"  [{tid}] {subject} — classification failed")
            stats["failed"] += 1
            continue

        domain  = classification.get("domain", "General")
        feat    = classification.get("feature", "Support Tickets")
        etype   = classification.get("entry_type", "error_fix")
        n_steps = len(classification.get("steps", []))
        tqdm.write(f"  [{tid}] {subject} → {domain} > {feat} [{etype}] ({n_steps} steps)")

        if args.dry_run:
            stats["created"] += 1
            continue

        company_id = get_or_create_company(conn, company_code)
        existed    = ticket_already_ingested(conn, tid, company_id)

        try:
            result = save_ticket_entry(conn, ticket, classification, company_id)
            if not result:
                stats["failed"] += 1
                continue
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            log.error(f"DB error for ticket {tid}: {e}")
            stats["failed"] += 1
            continue

        if CHROMA_AVAILABLE:
            entry_name = ticket["subject"] or f"Ticket {tid}"
            chroma_payloads.append({
                "version_id":  result["version_id"],
                "entry_id":    result["entry_id"],
                "domain":      result["domain"],
                "feature":     result["feature"],
                "name":        entry_name,
                "type":        classification.get("entry_type", "error_fix"),
                "menu_path":   "",
                "summary":     classification.get("summary", ""),
                "steps":       classification.get("steps", []),
                "notes":       classification.get("notes", []),
                "source_type": "ticket",
                "is_flagged":  False,
                "_company_code": company_code or None,
            })

        if existed:
            stats["updated"] += 1
        else:
            stats["created"] += 1

    pbar.close()

    # ── Batch ChromaDB upsert ─────────────────────────────────────
    if chroma_payloads:
        # Group by company_code for collection routing
        by_company: dict = {}
        for p in chroma_payloads:
            cc = p.pop("_company_code")
            by_company.setdefault(cc, []).append(p)

        total_indexed = 0
        for cc, entries in by_company.items():
            n = batch_upsert_entries(entries, company_code=cc)
            total_indexed += n
        print(f"🔍 {total_indexed} tickets indexed in ChromaDB")

    conn.close()

    print(f"\n{'=' * 55}")
    print(f"  Tickets created : {stats['created']}")
    print(f"  Tickets updated : {stats['updated']}")
    print(f"  Tickets skipped : {stats['skipped']}")
    print(f"  Tickets failed  : {stats['failed']}")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
