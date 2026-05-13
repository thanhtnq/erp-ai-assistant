"""
ERP AI — Knowledge Ingest Pipeline
No-LLM: parse document sections → extract steps positionally → embed → ChromaDB

Folder structure:
    documents/
      ├── _global/
      │     └── Sales/          ← domain = Sales, company = global
      │           └── *.docx / *.pdf
      └── clients/
            └── ABC/
                  └── Sales/    ← domain = Sales, company = ABC
                        └── *.docx / *.pdf

Usage:
    python ingest_knowledge.py                  # ingest all new/changed files
    python ingest_knowledge.py --dry-run        # preview without saving
    python ingest_knowledge.py --force          # re-ingest all files
    python ingest_knowledge.py --file path.pdf  # ingest single file
    python ingest_knowledge.py --workers 4      # parallel embed workers
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Ensure stdout handles Unicode (Windows console defaults to cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── Config ───────────────────────────────────────────────────────────────────

from ingest_config import (
    KNOWLEDGE_DB as DB_PATH,
    DOCS_DIR,
    IMAGES_BASE,
    LLM_WORKERS,
)

# ─── Logging ──────────────────────────────────────────────────────────────────

_log_dir = Path(__file__).parent.parent / "schedule"
_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "ingest_knowledge.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ingest_knowledge")

# ── Embedding + ChromaDB ──────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from embedding_helper import upsert_entry, CHROMA_AVAILABLE
    if CHROMA_AVAILABLE:
        print("[OK] ChromaDB ready — entries will be indexed")
    else:
        print("[--] ChromaDB not available — skipping vector indexing")
except ImportError:
    CHROMA_AVAILABLE = False
    def upsert_entry(*a, **kw): return False
    print("[--] embedding_helper not found — skipping vector indexing")

RE_HEADING = re.compile(r'^(\d+(?:\.\d+)*)[\s\t]+(.+)$')

NS_DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_REL     = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_DRAW    = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def folder_to_domain(folder_name: str) -> str:
    return folder_name.replace("_", " ").strip()


# ─── Folder Scanner ───────────────────────────────────────────────────────────

def scan_documents(docs_dir: str) -> list:
    files = []
    base  = Path(docs_dir)

    if not base.exists():
        print(f"[ERROR] Documents folder not found: {docs_dir}")
        print(f"        Create: documents/_global/Sales/")
        return []

    for pattern in ["*.docx", "*.pdf"]:
        for doc_file in base.rglob(pattern):
            parts = doc_file.relative_to(base).parts
            if parts[0] == "_global" and len(parts) >= 3:
                domain = folder_to_domain(parts[1])
                files.append({"file_path": str(doc_file), "domain": domain, "company_code": None})
            elif parts[0] == "clients" and len(parts) >= 4:
                domain = folder_to_domain(parts[2])
                files.append({"file_path": str(doc_file), "domain": domain, "company_code": parts[1].upper()})
            else:
                print(f"  [WARN] Unexpected path: {doc_file} — skipping")

    return files


# ─── DB Helpers ───────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_company_id(conn, code):
    if not code:
        return None
    row = conn.execute("SELECT id FROM companies WHERE code = ?", (code,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO companies (code, name) VALUES (?, ?)", (code, code))
    conn.commit()
    print(f"  [+] Auto-created company: {code}")
    return cur.lastrowid


def get_or_create_domain(conn, name):
    row = conn.execute("SELECT id FROM domains WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO domains (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def get_or_create_feature(conn, domain_id, name, sort_order):
    row = conn.execute(
        "SELECT id FROM features WHERE domain_id = ? AND name = ?", (domain_id, name)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO features (domain_id, name, sort_order) VALUES (?, ?, ?)",
        (domain_id, name, sort_order)
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_entry(conn, feature_id, name, entry_type, menu_path, sort_order):
    row = conn.execute(
        "SELECT id, is_active FROM entries WHERE feature_id = ? AND name = ?", (feature_id, name)
    ).fetchone()
    if row:
        was_inactive = row["is_active"] == 0
        conn.execute(
            "UPDATE entries SET type = ?, is_active = 1, menu_path = COALESCE(?, menu_path) WHERE id = ?",
            (entry_type, menu_path, row["id"])
        )
        return row["id"], False, was_inactive
    cur = conn.execute(
        "INSERT INTO entries (feature_id, name, type, menu_path, sort_order) VALUES (?, ?, ?, ?, ?)",
        (feature_id, name, entry_type, menu_path, sort_order)
    )
    return cur.lastrowid, True, False


def get_current_version(conn, entry_id, company_id):
    return conn.execute("""
        SELECT * FROM entry_versions
        WHERE entry_id = ? AND company_id IS ? AND is_current = 1
        ORDER BY version DESC LIMIT 1
    """, (entry_id, company_id)).fetchone()


def add_version(conn, entry_id, company_id, steps, notes, raw_content, source_ref):
    cur_ver = conn.execute("""
        SELECT COALESCE(MAX(version), 0) FROM entry_versions
        WHERE entry_id = ? AND company_id IS ?
    """, (entry_id, company_id)).fetchone()[0]

    new_ver = cur_ver + 1
    conn.execute("""
        UPDATE entry_versions SET is_current = 0
        WHERE entry_id = ? AND company_id IS ?
    """, (entry_id, company_id))
    cur = conn.execute("""
        INSERT INTO entry_versions
            (entry_id, company_id, version, steps, notes, raw_content,
             source_type, source_ref, is_current)
        VALUES (?, ?, ?, ?, ?, ?, 'document', ?, 1)
    """, (entry_id, company_id, new_ver,
          json.dumps(steps, ensure_ascii=False),
          json.dumps(notes, ensure_ascii=False),
          raw_content, source_ref))
    return new_ver, cur.lastrowid


def log_action(conn, doc_id, entry_id, action, detail):
    conn.execute(
        "INSERT INTO ingest_log (document_id, entry_id, action, detail) VALUES (?, ?, ?, ?)",
        (doc_id, entry_id, action, detail)
    )


def content_hash(text):
    return hashlib.md5((text or "").strip().encode()).hexdigest()


# ─── Image + Markdown Helpers ─────────────────────────────────────────────────

def get_image_folder(file_path: str, company_code: str) -> Path:
    p     = Path(file_path)
    parts = p.parts
    if "_global" in parts:
        idx = list(parts).index("_global")
        rel = Path(*parts[idx:list(parts).index(p.name)])
    elif "clients" in parts:
        idx = list(parts).index("clients")
        rel = Path(*parts[idx:list(parts).index(p.name)])
    else:
        rel = Path(company_code or "_global")
    folder = Path(IMAGES_BASE) / rel / p.stem
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ─── Document → Markdown (markitdown) ────────────────────────────────────────

def _extract_docx_images(file_path: str, img_folder: Path) -> list:
    """
    Extract all images from a DOCX in document order using python-docx.
    Returns a list of saved filenames (in the order they appear in the doc).
    markitdown truncates base64 to placeholders, so we get real bytes here.
    """
    try:
        from docx import Document
    except ImportError:
        return []

    doc          = Document(file_path)
    saved        = []
    existing_by_hash: dict = {}

    if img_folder.exists():
        for f in img_folder.iterdir():
            h = f.stem.rsplit("_", 1)
            if len(h) == 2:
                existing_by_hash[h[1] + f.suffix] = f.name

    # Collect rId → (name, bytes) from document relationships
    rid_to_image = {}
    for rel in doc.part.rels.values():
        if "image" in rel.reltype.lower():
            try:
                rid_to_image[rel.rId] = (
                    Path(rel.target_ref).name,
                    rel.target_part.blob,
                )
            except Exception:
                pass

    NS_A  = "http://schemas.openxmlformats.org/drawingml/2006/main"
    NS_R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    counter = [0]

    def save_image(img_name, img_bytes):
        img_hash = hashlib.md5(img_bytes).hexdigest()[:8]
        ext      = Path(img_name).suffix or ".png"
        key      = f"{img_hash}{ext}"
        if key in existing_by_hash:
            return existing_by_hash[key]
        counter[0] += 1
        fname = f"img_{counter[0]:03d}_{img_hash}{ext}"
        (img_folder / fname).write_bytes(img_bytes)
        existing_by_hash[key] = fname
        return fname

    for element in doc.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag != "p":
            continue
        rids = []
        for blip in element.findall(f".//{{{NS_A}}}blip"):
            rid = blip.get(f"{{{NS_R}}}embed")
            if rid:
                rids.append(rid)
        if not rids:
            for el in element.iter():
                for val in el.attrib.values():
                    if val.startswith("rId") and val in rid_to_image:
                        rids.append(val)
        for rid in rids:
            if rid in rid_to_image:
                img_name, img_bytes = rid_to_image[rid]
                fname = save_image(img_name, img_bytes)
                saved.append(fname)

    return saved


def _count_img_placeholders(text: str) -> int:
    """Count markitdown image placeholders (real or truncated base64)."""
    return len(re.findall(r'!\[[^\]]*\]\(data:image/', text))


def _parse_markdown_sections(markdown_text: str) -> list:
    """
    Split markitdown output into sections matching the 4-tier schema.

    markitdown converts DOCX headings to ## / ### etc. and feature headers
    to table rows like:  | **1.** | SALES QUOTATION |

    Returns a flat list of dicts:
      { level, number, heading, content, sort_order, is_feature, images }
    where images = list of filenames found in ![...](filename) within content.
    """
    sections    = []
    current     = None
    cur_feature = None

    # Regex for feature table rows:  | **1.** | FEATURE NAME |
    RE_FEAT_ROW = re.compile(r'^\|\s*\*\*(\d+)\.\*\*\s*\|\s*([^|]+)\|')
    # Regex for heading: ## 1.1 Some Title  or  ### 1.1.2 Sub
    RE_MD_HEAD  = re.compile(r'^(#{1,6})\s+(\d+(?:\.\d+)*)\s+(.+)')
    # TOC link lines to skip
    RE_TOC_LINK = re.compile(r'^\[.+\]\(#_Toc')
    # Image references to collect
    RE_IMG_REF  = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

    for line in markdown_text.split("\n"):
        raw = line.rstrip()

        # Skip TOC links
        if RE_TOC_LINK.match(raw.strip()):
            continue

        # Feature header (table row)
        m_feat = RE_FEAT_ROW.match(raw)
        if m_feat:
            if current:
                sections.append(current)
                current = None
            num  = m_feat.group(1)
            name = m_feat.group(2).strip().title()
            cur_feature = {
                "level": 1, "number": num, "heading": name,
                "content": "", "sort_order": float(num),
                "is_feature": True, "images": [],
            }
            sections.append(cur_feature)
            continue

        # Markdown heading
        m_head = RE_MD_HEAD.match(raw)
        if m_head:
            hashes  = m_head.group(1)
            number  = m_head.group(2)
            heading = m_head.group(3).strip()
            level   = len(hashes)
            top_num = number.split(".")[0]

            # Ensure feature section exists
            if cur_feature is None or cur_feature.get("number") != top_num:
                if cur_feature is None:
                    cur_feature = {
                        "level": 1, "number": top_num, "heading": f"Section {top_num}",
                        "content": "", "sort_order": float(top_num) if top_num.isdigit() else 0.0,
                        "is_feature": True, "images": [],
                    }
                    sections.append(cur_feature)

            if current:
                sections.append(current)

            try:
                sort_val = float(number)
            except Exception:
                sort_val = 0.0

            current = {
                "level": level, "number": number, "heading": heading,
                "content": "", "sort_order": sort_val,
                "is_feature": False, "images": [],
            }
            continue

        # Body content
        if current and not current.get("is_feature"):
            current["content"] += raw + "\n"

    if current and not current.get("is_feature"):
        sections.append(current)

    # Collect image filenames from each section's content
    for sec in sections:
        if not sec.get("is_feature"):
            sec["images"] = RE_IMG_REF.findall(sec["content"])

    return sections


def file_to_sections(file_path: str, img_folder: Path) -> list:
    """
    Convert DOCX or PDF to sections using markitdown.
    Falls back to pdfplumber heading-based parse for PDFs if markitdown fails.
    """
    try:
        from markitdown import MarkItDown
        md     = MarkItDown()
        result = md.convert(file_path)
        raw_md = result.text_content
    except Exception as e:
        print(f"  [markitdown] Conversion failed: {e}")
        return []

    # Extract actual image bytes from DOCX (markitdown only emits placeholders)
    ext = Path(file_path).suffix.lower()
    if ext == ".docx":
        all_images = _extract_docx_images(file_path, img_folder)
    else:
        all_images = []
    print(f" {len(all_images)} image(s) extracted")

    sections = _parse_markdown_sections(raw_md)

    # Assign images to sections by placeholder count (positional order)
    img_pool = list(all_images)
    for sec in sections:
        if sec.get("is_feature"):
            continue
        n = _count_img_placeholders(sec["content"])
        sec["images"] = img_pool[:n]
        img_pool = img_pool[n:]
        # Clean placeholder refs from content (replace with filename refs)
        _sec_imgs = sec["images"][:]
        _idx = [0]
        def _sub_img(_m):
            fname = _sec_imgs[_idx[0]] if _idx[0] < len(_sec_imgs) else None
            _idx[0] += 1
            return f"![]({fname})" if fname else ""
        sec["content"] = re.sub(r'!\[[^\]]*\]\(data:image/[^)]*\)', _sub_img, sec["content"])

    entry_count = sum(1 for s in sections if not s.get("is_feature"))
    print(f"     {entry_count} entries across {sum(1 for s in sections if s.get('is_feature'))} features")

    return sections


# ─── Step Extractor (positional heuristic — no LLM) ──────────────────────────

def extract_steps_from_content(content: str, images: list) -> tuple:
    """
    Extract steps from markdown content using positional image assignment.

    Supports two step patterns found in ERP manuals:
      1. Numbered:  "1. Do something"
      2. Bold field: "**Field Name**" followed by description paragraph

    Images appear inline in markdown after the step they illustrate, so they
    are assigned positionally as steps are encountered.
    """
    lines   = content.strip().split("\n")
    steps   = []
    notes   = []

    cur_num     = None
    cur_head    = None   # bold field name acting as step heading
    cur_lines   = []
    pending_img = None   # image seen before any step header (image-before-step pattern)

    def flush():
        nonlocal cur_num, cur_head, cur_lines, pending_img
        if cur_num is None and cur_head is None:
            return
        desc = " ".join(l for l in cur_lines if not re.match(r'!\[', l)).strip()
        # Find inline image in this step's lines
        img_in_lines = next(
            (re.search(r'!\[[^\]]*\]\(([^)]+)\)', l) for l in cur_lines
             if re.search(r'!\[[^\]]*\]\(([^)]+)\)', l)),
            None
        )
        img = img_in_lines.group(1) if img_in_lines else None
        action   = cur_head or (desc[:70] if len(desc) > 70 else desc)
        step_num = cur_num if cur_num is not None else len(steps) + 1
        steps.append({
            "step_number": step_num,
            "action":      action,
            "description": desc,
            "image":       img,
        })
        cur_num   = None
        cur_head  = None
        cur_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Standalone image line before any step → buffer for next step (image-before-step pattern)
        m_img_only = re.match(r'^!\[[^\]]*\]\(([^)]+)\)\s*$', stripped)
        if m_img_only and cur_num is None and cur_head is None:
            pending_img = pending_img or m_img_only.group(1)
            continue

        # Numbered step: "1. text" or "1) text"
        m_num = re.match(r"^(\d+)[.)]\s+(.+)", stripped)
        if m_num:
            flush()
            cur_num   = int(m_num.group(1))
            cur_lines = [m_num.group(2)]
            # Attach pending image (was before this step)
            if pending_img:
                cur_lines.append(f"![]({pending_img})")
                pending_img = None
            continue

        # Note / warning lines
        if re.match(r"^(Note|Warning|Important|Tip)[:\s]", stripped, re.IGNORECASE):
            notes.append(stripped)
            continue

        # Bold field name acting as step header: **Field Name** (standalone line)
        m_bold = re.match(r"^\*\*([^*]+)\*\*\s*$", stripped)
        if m_bold and len(m_bold.group(1)) < 60:
            flush()
            cur_head  = m_bold.group(1).strip()
            cur_lines = []
            # Attach pending image (was before this bold field)
            if pending_img:
                cur_lines.append(f"![]({pending_img})")
                pending_img = None
            continue

        # Body line (description or inline image)
        if cur_num is not None or cur_head is not None:
            cur_lines.append(stripped)

    flush()

    # Fallback: no steps detected → entire content as one step
    if not steps and content.strip():
        # Skip image lines when picking the action summary
        first_line = next(
            (l.strip()[:70] for l in content.strip().split('\n')
             if l.strip() and not l.strip().startswith('!')),
            "See content below"
        )
        img = images[0] if images else None
        steps = [{
            "step_number": 1,
            "action":      first_line,
            "description": content.strip(),
            "image":       img,
        }]

    return steps, notes


# ─── Content Classification ───────────────────────────────────────────────────

def detect_menu_path(content):
    m = re.search(r'([A-Z][^>\n]+(?:\s*>\s*[A-Z][^>\n]+){2,})', content)
    return m.group(1).strip() if m else None


def classify_type(heading, content):
    h = heading.lower().strip()

    # Priority 1: heading starts with an action verb → procedure
    procedure_verbs = [
        "creating", "create", "how to", "adding", "add ", "setting up",
        "set up", "configure", "configuring", "edit", "editing",
        "processing", "process", "entering", "enter", "submit",
        "approve", "approving", "generate", "generating", "run ",
        "running", "print", "printing", "post", "posting",
        "record", "recording", "apply", "applying", "convert",
    ]
    if any(h.startswith(v) or (" " + v) in h for v in procedure_verbs):
        return "procedure"

    # Priority 2: heading contains error keywords → error_fix
    if any(k in h for k in ["error", "fix", "issue", "cannot", "failed", "unable", "bug", "problem", "troubleshoot"]):
        return "error_fix"

    # Priority 3: heading signals faq
    if any(k in h for k in ["what is", "what are", "difference", "why", "faq", "overview", "about"]):
        return "faq"

    # Priority 4: heading signals reference
    if any(k in h for k in ["list", "definition", "glossary", "status", "field", "setup", "control", "report"]):
        return "reference"

    # Fallback: check content for error keywords
    if any(k in content[:200].lower() for k in ["error", "bug", "cannot", "failed", "unable"]):
        return "error_fix"

    return "procedure"


# ─── Core Ingest ──────────────────────────────────────────────────────────────

def _embed_and_upsert(payload, company_code):
    """Called in worker thread — embed + ChromaDB upsert for one entry."""
    if not CHROMA_AVAILABLE:
        return False
    return upsert_entry(payload, company_code=company_code)


def ingest_file(file_path, domain_name, company_code, dry_run, force, workers=None):
    workers = workers or LLM_WORKERS
    label   = f"{company_code or 'global'}/{domain_name}/{Path(file_path).name}"
    print(f"\n  {label}")

    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    conn       = get_conn()
    company_id = get_company_id(conn, company_code)
    domain_id  = get_or_create_domain(conn, domain_name)

    existing = conn.execute("""
        SELECT id, file_hash FROM document_registry
        WHERE file_path = ? AND company_id IS ?
    """, (file_path, company_id)).fetchone()

    if not force and existing and existing["file_hash"] == file_hash:
        print(f"     No change — skipped (use --force to re-ingest)")
        conn.close()
        return {"skipped_file": 1, "created": 0, "updated": 0, "skipped": 0}

    doc_id = None
    if not dry_run:
        if existing:
            conn.execute(
                "UPDATE document_registry SET file_hash=?, status='processing', ingested_at=? WHERE id=?",
                (file_hash, datetime.now().isoformat(), existing["id"])
            )
            doc_id = existing["id"]
        else:
            cur = conn.execute("""
                INSERT INTO document_registry (file_path, company_id, domain_id, file_hash, status)
                VALUES (?, ?, ?, ?, 'processing')
            """, (file_path, company_id, domain_id, file_hash))
            doc_id = cur.lastrowid
        conn.commit()

    img_folder = get_image_folder(file_path, company_code)
    print(f"     Converting document...", end="", flush=True)
    sections = file_to_sections(file_path, img_folder)

    stats              = {"created": 0, "updated": 0, "skipped": 0, "skipped_file": 0}
    current_feature_id = None

    entry_sections = [s for s in sections if s["level"] >= 2 and s["content"].strip()]
    entry_pbar = tqdm(
        total      = len(entry_sections),
        desc       = "     Entries",
        unit       = " entry",
        ncols      = 60,
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}{unit} [{elapsed}<{remaining}]"
    )

    # Collect (db_payload, chroma_payload) for parallel embed
    chroma_payloads = []

    try:
        for sec_idx, section in enumerate(sections):
            level   = section["level"]
            number  = section["number"]
            heading = section["heading"]
            content = section["content"].strip()

            if level == 1:
                tqdm.write(f"     {heading}")
                if not dry_run:
                    current_feature_id = get_or_create_feature(
                        conn, domain_id, heading, int(number.split(".")[0])
                    )
                continue

            if not content:
                entry_pbar.update(1)
                continue

            if dry_run or current_feature_id is not None:
                menu_path    = detect_menu_path(content)
                entry_type   = classify_type(heading, content)
                raw_hash     = content_hash(content)
                indent       = "  " * (level - 1)

                entry_images = section.get("images", [])

                steps, notes = extract_steps_from_content(content, entry_images)

                if dry_run:
                    img_info = f" ({len(entry_images)} images)" if entry_images else ""
                    tqdm.write(
                        f"     {indent}[{number}] {heading} [{entry_type}]"
                        f" → {len(steps)} step(s){img_info}"
                    )
                    entry_pbar.update(1)
                    continue

                try:
                    sort_order = int(float(number) * 10) if number.count(".") == 1 else 0
                except Exception:
                    sort_order = 0

                entry_id, is_new, was_inactive = get_or_create_entry(
                    conn, current_feature_id, heading, entry_type, menu_path, sort_order
                )

                cur_ver = get_current_version(conn, entry_id, company_id)
                hash_unchanged = cur_ver and content_hash(cur_ver["raw_content"] or "") == raw_hash
                if hash_unchanged and not was_inactive:
                    tqdm.write(f"     {indent}[{number}] {heading} → no change")
                    stats["skipped"] += 1
                    log_action(conn, doc_id, entry_id, "skipped", "Content unchanged")
                    conn.commit()
                    entry_pbar.update(1)
                    continue

                img_label = f" [{len(entry_images)} img]" if entry_images else ""
                tqdm.write(f"     {indent}[{number}] {heading} [{entry_type}]{img_label}")

                try:
                    new_ver, version_id = add_version(
                        conn, entry_id, company_id, steps, notes, content,
                        Path(file_path).name
                    )
                    log_action(conn, doc_id, entry_id,
                               "created" if is_new else "version_added",
                               f"v{new_ver} — {len(steps)} steps")
                    conn.commit()

                    result_label = "created" if is_new else f"updated → v{new_ver}"
                    tqdm.write(f"            {result_label} ({len(steps)} steps)")
                    stats["created" if is_new else "updated"] += 1

                    if CHROMA_AVAILABLE:
                        domain_row  = conn.execute(
                            "SELECT d.name FROM domains d JOIN features f ON f.domain_id=d.id WHERE f.id=?",
                            (current_feature_id,)
                        ).fetchone()
                        feature_row = conn.execute(
                            "SELECT name FROM features WHERE id=?", (current_feature_id,)
                        ).fetchone()
                        chroma_payloads.append({
                            "version_id":  version_id,
                            "entry_id":    entry_id,
                            "domain":      domain_row["name"] if domain_row else "",
                            "feature":     feature_row["name"] if feature_row else "",
                            "name":        heading,
                            "type":        entry_type,
                            "menu_path":   menu_path or "",
                            "summary":     "",
                            "steps":       steps,
                            "notes":       notes,
                            "source_type": "document",
                            "is_flagged":  False,
                        })

                except sqlite3.Error as e:
                    conn.rollback()
                    log.error(f"DB error for '{heading}': {e} — skipped")
                    stats["skipped"] += 1

            entry_pbar.update(1)

        # ── Parallel embed + ChromaDB upsert ─────────────────────────────────
        if chroma_payloads:
            tqdm.write(f"\n     Embedding {len(chroma_payloads)} entries ({workers} workers)...")
            success = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(_embed_and_upsert, p, company_code): p["name"]
                    for p in chroma_payloads
                }
                for fut in as_completed(futures):
                    name = futures[fut]
                    try:
                        if fut.result():
                            success += 1
                    except Exception as e:
                        log.warning(f"Embed error for '{name}': {e}")
            tqdm.write(f"     {success}/{len(chroma_payloads)} entries indexed in ChromaDB")

    except Exception as e:
        log.error(f"Ingest aborted for {label}: {e}")
        if not dry_run and doc_id:
            conn.execute(
                "UPDATE document_registry SET status='failed', error_message=? WHERE id=?",
                (str(e)[:500], doc_id)
            )
            conn.commit()
        conn.close()
        entry_pbar.close()
        return stats

    entry_pbar.close()

    if not dry_run and doc_id:
        conn.execute("""
            UPDATE document_registry SET status='done', entries_parsed=?, ingested_at=? WHERE id=?
        """, (stats["created"] + stats["updated"], datetime.now().isoformat(), doc_id))
        conn.commit()

    conn.close()
    return stats


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest ERP documents into Knowledge DB")
    parser.add_argument("--file",    help="Single file to ingest (auto-detect domain from path)")
    parser.add_argument("--domain",  help="Override domain name (e.g. Sales)")
    parser.add_argument("--company", help="Override company code (e.g. ABC)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving to DB")
    parser.add_argument("--force",   action="store_true", help="Re-ingest even if file unchanged")
    parser.add_argument("--workers", type=int, default=None,
                        help=f"Parallel embed workers (default: {LLM_WORKERS})")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Knowledge DB not found: {DB_PATH}")
        print(f"        Run: python knowledge_schema.py first")
        sys.exit(1)

    workers = args.workers or LLM_WORKERS
    print(f"\nERP Knowledge Ingest - {'DRY RUN' if args.dry_run else 'LIVE'} | workers={workers}")
    print("-" * 50)

    if args.file:
        p     = Path(args.file)
        parts = p.parts
        domain  = args.domain
        company = args.company
        if not domain:
            if "_global" in parts:
                idx = list(parts).index("_global")
                if idx + 1 < len(parts):
                    domain = folder_to_domain(parts[idx + 1])
            elif "clients" in parts:
                idx = list(parts).index("clients")
                if idx + 2 < len(parts):
                    domain = folder_to_domain(parts[idx + 2])
        if not domain:
            print("[ERROR] Cannot detect domain from path. Use --domain 'Sales'")
            sys.exit(1)
        if not company and "clients" in parts:
            idx = list(parts).index("clients")
            if idx + 1 < len(parts):
                company = parts[idx + 1].upper()
        files = [{"file_path": args.file, "domain": domain, "company_code": company}]
    else:
        files = scan_documents(DOCS_DIR)
        if not files:
            sys.exit(1)
        print(f"Found {len(files)} file(s)\n")

    total = {"created": 0, "updated": 0, "skipped": 0, "skipped_file": 0}

    file_pbar = tqdm(
        files,
        desc       = "Files",
        unit       = " file",
        ncols      = 60,
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}{unit} [{elapsed}<{remaining}]"
    )

    for f in file_pbar:
        file_pbar.set_postfix_str(Path(f["file_path"]).name[:30])
        stats = ingest_file(
            file_path    = f["file_path"],
            domain_name  = f["domain"],
            company_code = f["company_code"],
            dry_run      = args.dry_run,
            force        = args.force,
            workers      = workers,
        )
        for k in total:
            total[k] += stats.get(k, 0)

    file_pbar.close()

    print(f"\n{'=' * 50}")
    print(f"  Files processed : {len(files) - total['skipped_file']}")
    print(f"  Files skipped   : {total['skipped_file']} (unchanged)")
    print(f"  Entries created : {total['created']}")
    print(f"  Entries updated : {total['updated']}")
    print(f"  Entries skipped : {total['skipped']} (unchanged)")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
