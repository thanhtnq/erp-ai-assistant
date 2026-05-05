"""
ERP AI — Image Ingest Viewer
Check which images were extracted and how they map to knowledge entries.

Usage:
    python check_images.py                         # overview of all image folders
    python check_images.py --domain Sales          # images for Sales domain
    python check_images.py --entry 5               # images assigned to entry ID 5
    python check_images.py --missing               # entries with steps but no images
    python check_images.py --orphans               # image files not referenced in any entry
"""

import argparse
import json
import os
import sqlite3
from pathlib import Path

DB_PATH    = "../data/erp_knowledge.db"
IMAGES_DIR = "../document_images"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Overview ─────────────────────────────────────────────────────────────────

def show_overview():
    base = Path(IMAGES_DIR)
    if not base.exists():
        print(f"\n  [!] Image folder not found: {IMAGES_DIR}")
        return

    print(f"\n{'='*60}")
    print(f"  DOCUMENT IMAGES — OVERVIEW")
    print(f"  Base: {base.resolve()}")
    print(f"{'='*60}\n")

    total_files = 0
    for folder in sorted(base.rglob("*")):
        if not folder.is_dir():
            continue
        images = list(folder.glob("*.png")) + list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
        if not images:
            continue
        rel = folder.relative_to(base)
        print(f"  📁 {rel}")
        print(f"     {len(images)} image(s)")
        # Show versions
        versions = set()
        for img in images:
            if img.name.startswith("v"):
                v = img.name.split("_")[0]
                versions.add(v)
        if versions:
            print(f"     Versions: {', '.join(sorted(versions))}")
        total_files += len(images)

    print(f"\n  Total images: {total_files}")

    # DB stats
    conn = get_conn()
    total_with_img = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT DISTINCT ev.id FROM entry_versions ev
            WHERE ev.is_current=1
            AND json_array_length(ev.steps) > 0
            AND ev.steps LIKE '%"image"%'
            AND ev.steps NOT LIKE '%"image": null%'
            AND ev.steps NOT LIKE '%"image":null%'
        )
    """).fetchone()[0]
    conn.close()
    print(f"  Entries with images in DB: {total_with_img}")
    print()


# ─── Domain images ────────────────────────────────────────────────────────────

def show_domain_images(domain_name):
    base = Path(IMAGES_DIR)
    conn = get_conn()

    domain = conn.execute(
        "SELECT * FROM domains WHERE name LIKE ?", (f"%{domain_name}%",)
    ).fetchone()

    if not domain:
        print(f"\n  Domain not found: {domain_name}")
        conn.close()
        return

    print(f"\n{'='*60}")
    print(f"  IMAGES FOR DOMAIN: {domain['name']}")
    print(f"{'='*60}\n")

    # Find image folders for this domain
    for scope in ["_global", "clients"]:
        scope_path = base / scope
        if not scope_path.exists():
            continue
        for folder in sorted(scope_path.rglob("*")):
            if not folder.is_dir():
                continue
            # Check if folder name matches domain
            parts = folder.relative_to(base).parts
            domain_part = parts[1] if len(parts) >= 2 else ""
            if domain_part.lower().replace(" ","_") != domain["name"].lower().replace(" ","_"):
                if domain["name"].lower() not in domain_part.lower():
                    continue
            images = list(folder.glob("*.png")) + list(folder.glob("*.jpg"))
            if not images:
                continue
            print(f"  📁 {folder.relative_to(base)}")
            for img in sorted(images):
                size = img.stat().st_size // 1024
                print(f"     🖼  {img.name}  ({size} KB)")
            print()

    conn.close()


# ─── Entry images ─────────────────────────────────────────────────────────────

def show_entry_images(entry_id):
    conn = get_conn()

    entry = conn.execute("""
        SELECT e.*, f.name as feature, d.name as domain
        FROM entries e JOIN features f ON e.feature_id=f.id JOIN domains d ON f.domain_id=d.id
        WHERE e.id=?
    """, (entry_id,)).fetchone()

    if not entry:
        print(f"\n  Entry {entry_id} not found.")
        conn.close()
        return

    version = conn.execute("""
        SELECT * FROM entry_versions WHERE entry_id=? AND company_id IS NULL AND is_current=1
    """, (entry_id,)).fetchone()

    print(f"\n  {entry['domain']} › {entry['feature']} › {entry['name']}")

    if not version:
        print("  No version found.")
        conn.close()
        return

    steps   = json.loads(version["steps"] or "[]")
    src_ref = version["source_ref"] or ""
    doc_stem = src_ref.replace(".docx","").replace(".DOCX","")

    print(f"  Source: {src_ref}\n")

    has_any = False
    for s in steps:
        img = s.get("image")
        if img:
            has_any = True
            # Build expected path
            img_path = Path(IMAGES_DIR) / "_global" / entry["domain"] / doc_stem / img
            exists   = "✅" if img_path.exists() else "❌ NOT FOUND"
            print(f"  Step {s.get('step_number','?')}: {s.get('action','')}")
            print(f"    🖼  {img}  {exists}")
            print(f"    Path: {img_path}")
        else:
            print(f"  Step {s.get('step_number','?')}: {s.get('action','')}  (no image)")

    if not has_any:
        print("  No images assigned to any steps.")

    conn.close()


# ─── Missing images ───────────────────────────────────────────────────────────

def show_missing(conn):
    """Entries that have steps but no images assigned."""
    rows = conn.execute("""
        SELECT e.id, e.name, f.name as feature, d.name as domain,
               json_array_length(ev.steps) as step_count, ev.source_ref
        FROM entry_versions ev
        JOIN entries e  ON ev.entry_id  = e.id
        JOIN features f ON e.feature_id = f.id
        JOIN domains d  ON f.domain_id  = d.id
        WHERE ev.is_current=1 AND ev.source_type='document'
        AND json_array_length(ev.steps) > 0
        AND (ev.steps NOT LIKE '%"image": "v%' AND ev.steps NOT LIKE '%"image":"v%')
        ORDER BY d.name, f.name
        LIMIT 50
    """).fetchall()

    print(f"\n  ENTRIES WITH NO IMAGES ({len(rows)} shown)\n")
    for r in rows:
        print(f"  [{r['id']}] {r['domain']} › {r['feature']} › {r['name']}")
        print(f"       {r['step_count']} steps · {r['source_ref']}")
    print()


# ─── Orphaned images ──────────────────────────────────────────────────────────

def show_orphans(conn):
    """Image files on disk not referenced in any entry."""
    base = Path(IMAGES_DIR)
    if not base.exists():
        print(f"\n  Image folder not found: {IMAGES_DIR}")
        return

    # Collect all image refs from DB
    rows = conn.execute(
        "SELECT steps FROM entry_versions WHERE is_current=1 AND steps IS NOT NULL"
    ).fetchall()
    referenced = set()
    for row in rows:
        for s in json.loads(row["steps"] or "[]"):
            if s.get("image"):
                referenced.add(s["image"])

    # Find files not referenced
    print(f"\n  ORPHANED IMAGES (not referenced in any entry)\n")
    orphan_count = 0
    for img in sorted(base.rglob("*.png")):
        if img.name not in referenced:
            size = img.stat().st_size // 1024
            print(f"  ❌ {img.relative_to(base)}  ({size} KB)")
            orphan_count += 1

    if orphan_count == 0:
        print("  None — all images are referenced. ✅")
    else:
        print(f"\n  Total orphaned: {orphan_count}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Check image ingestion status")
    parser.add_argument("--domain",  help="Show images for a domain")
    parser.add_argument("--entry",   type=int, help="Show images for a specific entry ID")
    parser.add_argument("--missing", action="store_true", help="Entries with no images")
    parser.add_argument("--orphans", action="store_true", help="Image files not in any entry")
    args = parser.parse_args()

    if args.domain:
        show_domain_images(args.domain)
    elif args.entry:
        show_entry_images(args.entry)
    elif args.missing:
        conn = get_conn()
        show_missing(conn)
        conn.close()
    elif args.orphans:
        conn = get_conn()
        show_orphans(conn)
        conn.close()
    else:
        show_overview()


if __name__ == "__main__":
    main()
