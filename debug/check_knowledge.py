"""
ERP AI — Knowledge DB Viewer
View what has been ingested into the knowledge database.

Usage:
    python check_knowledge.py                      # overview summary
    python check_knowledge.py --domain Sales       # all entries in Sales
    python check_knowledge.py --entry 5            # full content of entry ID 5
    python check_knowledge.py --search "quotation" # search by keyword
    python check_knowledge.py --tickets            # show ticket-sourced entries only
    python check_knowledge.py --flagged            # show flagged entries
"""

import argparse
import json
import sqlite3

DB_PATH = "../data/erp_knowledge.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Overview ─────────────────────────────────────────────────────────────────

def show_overview(conn):
    print("\n" + "=" * 60)
    print("  ERP KNOWLEDGE BASE — OVERVIEW")
    print("=" * 60)

    domains = conn.execute("""
        SELECT d.name,
               COUNT(DISTINCT f.id)  as features,
               COUNT(DISTINCT e.id)  as entries,
               SUM(CASE WHEN ev.source_type='document' AND ev.is_current=1 THEN 1 ELSE 0 END) as from_docs,
               SUM(CASE WHEN ev.source_type='ticket'   AND ev.is_current=1 THEN 1 ELSE 0 END) as from_tickets,
               SUM(CASE WHEN ev.is_flagged=1 AND ev.is_current=1 THEN 1 ELSE 0 END) as flagged
        FROM domains d
        LEFT JOIN features f     ON f.domain_id  = d.id
        LEFT JOIN entries e      ON e.feature_id = f.id
        LEFT JOIN entry_versions ev ON ev.entry_id = e.id
        GROUP BY d.id, d.name
        ORDER BY d.name
    """).fetchall()

    if not domains:
        print("\n  No data yet. Run: python ingest/ingest_knowledge.py")
        return

    print(f"\n  {'Domain':<22} {'Features':>9} {'Entries':>8} {'Docs':>6} {'Tickets':>8} {'Flagged':>8}")
    print(f"  {'─'*22} {'─'*9} {'─'*8} {'─'*6} {'─'*8} {'─'*8}")
    for d in domains:
        flag = f" ⚠{d['flagged']}" if d['flagged'] else ""
        print(f"  {d['name']:<22} {d['features']:>9} {d['entries']:>8} "
              f"{d['from_docs']:>6} {d['from_tickets']:>8} {d['flagged']:>8}{flag}")

    totals = conn.execute("""
        SELECT COUNT(DISTINCT d.id) as domains, COUNT(DISTINCT f.id) as features,
               COUNT(DISTINCT e.id) as entries
        FROM domains d
        LEFT JOIN features f ON f.domain_id = d.id
        LEFT JOIN entries e  ON e.feature_id = f.id
    """).fetchone()

    print(f"  {'─'*60}")
    print(f"  {'TOTAL':<22} {totals['features']:>9} {totals['entries']:>8}")

    # Entry types
    types = conn.execute("""
        SELECT type, COUNT(*) as n FROM entries GROUP BY type ORDER BY n DESC
    """).fetchall()
    print(f"\n  Entry Types:")
    for t in types:
        bar = "█" * min(t["n"], 25)
        print(f"    {t['type']:<15} {t['n']:>4}  {bar}")

    # Source types
    print(f"\n  Source Types (current versions):")
    sources = conn.execute("""
        SELECT source_type, COUNT(*) as n FROM entry_versions
        WHERE is_current=1 GROUP BY source_type
    """).fetchall()
    for s in sources:
        print(f"    {s['source_type']:<15} {s['n']:>4}")

    # Companies
    global_n = conn.execute(
        "SELECT COUNT(*) FROM entry_versions WHERE company_id IS NULL AND is_current=1"
    ).fetchone()[0]
    companies = conn.execute("""
        SELECT c.code, COUNT(ev.id) as n FROM companies c
        LEFT JOIN entry_versions ev ON ev.company_id = c.id AND ev.is_current=1
        GROUP BY c.id, c.code
    """).fetchall()
    print(f"\n  Company Versions:")
    print(f"    {'[Global]':<18} {global_n:>4}")
    for c in companies:
        print(f"    {c['code']:<18} {c['n']:>4}")

    # Documents
    docs = conn.execute("""
        SELECT COUNT(*) total,
               SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) done
        FROM document_registry
    """).fetchone()
    print(f"\n  Documents ingested: {docs['done']} ✓ / {docs['total']} total")
    print("=" * 60 + "\n")


# ─── Domain view ──────────────────────────────────────────────────────────────

def show_domain(conn, name):
    domain = conn.execute(
        "SELECT * FROM domains WHERE name LIKE ?", (f"%{name}%",)
    ).fetchone()
    if not domain:
        print(f"\n  Domain not found: {name}")
        available = [r["name"] for r in conn.execute("SELECT name FROM domains ORDER BY name")]
        print(f"  Available: {', '.join(available)}")
        return

    print(f"\n{'='*60}")
    print(f"  DOMAIN: {domain['name']}")
    print(f"{'='*60}")

    features = conn.execute("""
        SELECT f.id, f.name, COUNT(e.id) as n
        FROM features f LEFT JOIN entries e ON e.feature_id=f.id
        WHERE f.domain_id=? GROUP BY f.id, f.name ORDER BY f.sort_order
    """, (domain["id"],)).fetchall()

    for feat in features:
        print(f"\n  📁 {feat['name']} ({feat['n']} entries)")
        entries = conn.execute("""
            SELECT e.id, e.name, e.type, e.summary, e.menu_path,
                   ev.version, ev.source_type, ev.thumbs_up, ev.thumbs_down,
                   ev.is_flagged, ev.flag_reason,
                   COALESCE(json_array_length(ev.steps), 0) as steps,
                   (SELECT COUNT(*) FROM entry_versions ev2
                    WHERE ev2.entry_id=e.id AND ev2.company_id IS NULL) as versions
            FROM entries e
            LEFT JOIN entry_versions ev ON ev.entry_id=e.id AND ev.is_current=1 AND ev.company_id IS NULL
            WHERE e.feature_id=? ORDER BY e.sort_order
        """, (feat["id"],)).fetchall()

        for e in entries:
            icon = {"procedure":"📋","error_fix":"🔧","faq":"❓","reference":"📖"}.get(e["type"],"•")
            src  = "📄" if e["source_type"]=="document" else "🎫"
            flag = " ⚠ FLAGGED" if e["is_flagged"] else ""
            print(f"    {icon}{src} [{e['id']:3}] {e['name']}{flag}")
            print(f"         v{e['version']} · {e['steps']} steps · 👍{e['thumbs_up']} 👎{e['thumbs_down']}")
            if e["summary"]:
                print(f"         {e['summary'][:80]}")
            if e["menu_path"]:
                print(f"         📍 {e['menu_path']}")
            if e["is_flagged"] and e["flag_reason"]:
                print(f"         ⚠  {e['flag_reason'][:80]}")


# ─── Entry detail ─────────────────────────────────────────────────────────────

def show_entry(conn, entry_id):
    entry = conn.execute("""
        SELECT e.*, f.name as feature, d.name as domain
        FROM entries e JOIN features f ON e.feature_id=f.id JOIN domains d ON f.domain_id=d.id
        WHERE e.id=?
    """, (entry_id,)).fetchone()
    if not entry:
        print(f"\n  Entry {entry_id} not found.")
        return

    version = conn.execute("""
        SELECT * FROM entry_versions WHERE entry_id=? AND company_id IS NULL AND is_current=1
    """, (entry_id,)).fetchone()

    print(f"\n{'='*60}")
    print(f"  {entry['domain']} › {entry['feature']} › {entry['name']}")
    print(f"  Type: {entry['type']}  ID: {entry_id}")
    if entry["menu_path"]: print(f"  Menu: {entry['menu_path']}")
    if entry["summary"]:   print(f"  Summary: {entry['summary']}")
    print(f"{'='*60}")

    if not version:
        print("  No version found.")
        return

    print(f"\n  Source: {version['source_type']} · {version['source_ref']} · v{version['version']}")
    print(f"  Score: {version['score']:.2f} · 👍{version['thumbs_up']} 👎{version['thumbs_down']}")
    if version["is_flagged"]:
        print(f"  ⚠ FLAGGED: {version['flag_reason']}")

    steps = json.loads(version["steps"] or "[]")
    if steps:
        print(f"\n  STEPS ({len(steps)}):")
        for s in steps:
            img = f" 🖼 {s['image']}" if s.get("image") else ""
            print(f"\n  {s.get('step_number','?')}. {s.get('action','')}{img}")
            print(f"     {s.get('description','')}")
            if s.get("fields"):
                print(f"     Fields: {', '.join(s['fields'])}")

    notes = json.loads(version["notes"] or "[]")
    if notes:
        print(f"\n  NOTES:")
        for n in notes: print(f"  • {n}")

    # Version history
    history = conn.execute("""
        SELECT version, source_type, source_ref, created_at, is_current
        FROM entry_versions WHERE entry_id=? AND company_id IS NULL ORDER BY version DESC
    """, (entry_id,)).fetchall()
    if len(history) > 1:
        print(f"\n  VERSION HISTORY:")
        for h in history:
            cur = " ← current" if h["is_current"] else ""
            print(f"  v{h['version']} · {h['source_type']} · {h['source_ref']} · {h['created_at'][:10]}{cur}")


# ─── Search ───────────────────────────────────────────────────────────────────

def show_search(conn, keyword):
    results = conn.execute("""
        SELECT e.id, e.name, e.type, e.summary, f.name as feature, d.name as domain
        FROM entries e JOIN features f ON e.feature_id=f.id JOIN domains d ON f.domain_id=d.id
        WHERE e.name LIKE ? OR e.summary LIKE ? OR e.menu_path LIKE ?
        ORDER BY d.name, f.name, e.sort_order LIMIT 20
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")).fetchall()

    print(f"\n  Search: '{keyword}' — {len(results)} result(s)\n")
    for r in results:
        icon = {"procedure":"📋","error_fix":"🔧","faq":"❓","reference":"📖"}.get(r["type"],"•")
        print(f"  {icon} [{r['id']}] {r['domain']} › {r['feature']} › {r['name']}")
        if r["summary"]: print(f"       {r['summary'][:80]}")
        print()


# ─── Tickets ──────────────────────────────────────────────────────────────────

def show_tickets(conn):
    rows = conn.execute("""
        SELECT e.id, e.name, e.type, f.name as feature, d.name as domain,
               ev.source_ref, ev.thumbs_up, ev.thumbs_down, ev.is_flagged, ev.created_at
        FROM entry_versions ev
        JOIN entries e  ON ev.entry_id  = e.id
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE ev.source_type='ticket' AND ev.is_current=1
        ORDER BY ev.created_at DESC LIMIT 50
    """).fetchall()

    print(f"\n  TICKET-SOURCED ENTRIES ({len(rows)} shown)\n")
    for r in rows:
        flag = " ⚠" if r["is_flagged"] else ""
        print(f"  🎫 [{r['id']}] {r['domain']} › {r['feature']}")
        print(f"     {r['name']}{flag}")
        print(f"     Ticket: {r['source_ref']} · 👍{r['thumbs_up']} 👎{r['thumbs_down']}")
        print()


# ─── Flagged ──────────────────────────────────────────────────────────────────

def show_flagged(conn):
    rows = conn.execute("""
        SELECT e.id, e.name, e.type, f.name as feature, d.name as domain,
               ev.flag_reason, ev.thumbs_up, ev.thumbs_down, ev.source_type
        FROM entry_versions ev
        JOIN entries e  ON ev.entry_id  = e.id
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE ev.is_flagged=1 AND ev.is_current=1
        ORDER BY ev.thumbs_down DESC
    """).fetchall()

    print(f"\n  ⚠ FLAGGED ENTRIES ({len(rows)})\n")
    if not rows:
        print("  None — all entries look good!")
        return
    for r in rows:
        icon = {"procedure":"📋","error_fix":"🔧","faq":"❓","reference":"📖"}.get(r["type"],"•")
        print(f"  {icon} [{r['id']}] {r['domain']} › {r['feature']} › {r['name']}")
        print(f"     Source: {r['source_type']} · 👍{r['thumbs_up']} 👎{r['thumbs_down']}")
        print(f"     Reason: {r['flag_reason']}")
        print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="View ERP Knowledge DB contents")
    parser.add_argument("--domain",  help="Show entries in a domain")
    parser.add_argument("--entry",   type=int, help="Show full entry by ID")
    parser.add_argument("--search",  help="Search by keyword")
    parser.add_argument("--tickets", action="store_true", help="Show ticket-sourced entries")
    parser.add_argument("--flagged", action="store_true", help="Show flagged entries")
    args = parser.parse_args()

    try:
        conn = get_conn()
    except Exception as e:
        print(f"[ERROR] Cannot open DB: {e}")
        return

    if args.domain:   show_domain(conn, args.domain)
    elif args.entry:  show_entry(conn, args.entry)
    elif args.search: show_search(conn, args.search)
    elif args.tickets: show_tickets(conn)
    elif args.flagged: show_flagged(conn)
    else:             show_overview(conn)

    conn.close()


if __name__ == "__main__":
    main()
