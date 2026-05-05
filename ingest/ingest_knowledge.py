"""
ERP AI — Knowledge Ingest Pipeline
Auto-scans documents/ folder and ingests all .docx and .pdf files.

Folder structure:
    documents/
      ├── _global/
      │     └── sales/          ← domain = Sales, company = global
      │           └── *.docx
      │           └── *.pdf
      └── clients/
            └── ABC/
                  └── sales/    ← domain = Sales, company = ABC
                        └── *.docx
                        └── *.pdf

Usage:
    python ingest_knowledge.py                  # ingest all new/changed files
    python ingest_knowledge.py --dry-run        # preview without saving
    python ingest_knowledge.py --force          # re-ingest all files
    python ingest_knowledge.py --file path.pdf  # ingest single file
    python ingest_knowledge.py --workers 1      # sequential (debug mode)
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import google.generativeai as genai

# ─── Config ───────────────────────────────────────────────────────────────────

from ingest_config import (
    KNOWLEDGE_DB as DB_PATH,
    DOCS_DIR,
    GEMINI_API_KEY,
    LLM_MODEL_INGEST as LLM_MODEL,
    IMAGES_BASE,
    LLM_WORKERS,
    MAX_LLM_RETRIES,
    LLM_RETRY_DELAY,
)

genai.configure(api_key=GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel(LLM_MODEL)

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

# ── Embedding + ChromaDB (optional — graceful fallback if not installed) ──────
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from embedding_helper import batch_upsert_entries, CHROMA_AVAILABLE
    if CHROMA_AVAILABLE:
        print("[OK] ChromaDB ready — entries will be indexed")
    else:
        print("[--] ChromaDB not available — skipping vector indexing")
except ImportError:
    CHROMA_AVAILABLE = False
    def batch_upsert_entries(*a, **kw): return 0
    print("[--] embedding_helper not found — skipping vector indexing")

RE_HEADING = re.compile(r'^(\d+(?:\.\d+)*)[\s\t]+(.+)$')


def folder_to_domain(folder_name: str) -> str:
    """Convert folder name to domain name.
    Human_Resources → Human Resources
    sales           → Sales
    CRM             → CRM
    """
    return folder_name.replace("_", " ").strip()


# ─── Folder Scanner ───────────────────────────────────────────────────────────

def scan_documents(docs_dir: str) -> list:
    files = []
    base  = Path(docs_dir)

    if not base.exists():
        print(f"[ERROR] Documents folder not found: {docs_dir}")
        print(f"        Create the folder structure:")
        print(f"        documents/_global/Sales/")
        print(f"        documents/_global/Human_Resources/")
        print(f"        documents/clients/ABC/Sales/")
        return []

    # Scan both .docx and .pdf
    for pattern in ["*.docx", "*.pdf"]:
        for doc_file in base.rglob(pattern):
            parts = doc_file.relative_to(base).parts

            # _global/Sales/file.docx
            if parts[0] == "_global" and len(parts) >= 3:
                domain = folder_to_domain(parts[1])
                files.append({"file_path": str(doc_file), "domain": domain, "company_code": None})

            # clients/ABC/Sales/file.docx
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
    """Returns (entry_id, is_new). Does NOT commit — caller owns the transaction."""
    row = conn.execute(
        "SELECT id FROM entries WHERE feature_id = ? AND name = ?", (feature_id, name)
    ).fetchone()
    if row:
        if menu_path:
            conn.execute(
                "UPDATE entries SET menu_path = COALESCE(?, menu_path) WHERE id = ?",
                (menu_path, row["id"])
            )
        return row["id"], False
    cur = conn.execute(
        "INSERT INTO entries (feature_id, name, type, menu_path, sort_order) VALUES (?, ?, ?, ?, ?)",
        (feature_id, name, entry_type, menu_path, sort_order)
    )
    return cur.lastrowid, True


def get_current_version(conn, entry_id, company_id):
    return conn.execute("""
        SELECT * FROM entry_versions
        WHERE entry_id = ? AND company_id IS ? AND is_current = 1
        ORDER BY version DESC LIMIT 1
    """, (entry_id, company_id)).fetchone()


def add_version(conn, entry_id, company_id, steps, notes, raw_content, source_ref):
    """Insert a new version row. Does NOT commit — caller owns the transaction."""
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
    """Append to audit log. Does NOT commit — caller owns the transaction."""
    conn.execute(
        "INSERT INTO ingest_log (document_id, entry_id, action, detail) VALUES (?, ?, ?, ?)",
        (doc_id, entry_id, action, detail)
    )


def content_hash(text):
    return hashlib.md5((text or "").strip().encode()).hexdigest()


# ─── Image Helpers ────────────────────────────────────────────────────────────

NS_DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_REL     = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_DRAW    = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def get_image_folder(file_path: str, company_code: str) -> Path:
    """
    Build image output folder mirroring documents/ structure.
    documents/_global/Sales/manual.docx → document_images/_global/Sales/manual/
    documents/clients/ABC/Sales/manual.docx → document_images/clients/ABC/Sales/manual/
    """
    p     = Path(file_path)
    parts = p.parts

    # Find anchor (_global or clients)
    if "_global" in parts:
        idx    = list(parts).index("_global")
        rel    = Path(*parts[idx:p.parts.index(p.name)])  # _global/Sales
    elif "clients" in parts:
        idx    = list(parts).index("clients")
        rel    = Path(*parts[idx:p.parts.index(p.name)])  # clients/ABC/Sales
    else:
        rel    = Path(company_code or "_global")

    folder = Path(IMAGES_BASE) / rel / p.stem
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def extract_images_with_positions(file_path: str) -> dict:
    """
    Extract images from docx and map each to its body element index.
    Returns: { body_index: [ (image_name, image_bytes), ... ] }
    """
    from docx import Document
    from docx.oxml.ns import qn

    doc        = Document(file_path)
    body       = doc.element.body
    image_map  = {}

    # Build rId → (name, bytes) map from document part relationships
    rid_to_image = {}
    for rel in doc.part.rels.values():
        if "image" in rel.reltype.lower():
            try:
                img_bytes = rel.target_part.blob
                img_name  = Path(rel.target_ref).name
                rid_to_image[rel.rId] = (img_name, img_bytes)
            except:
                pass

    for idx, element in enumerate(body):
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag != "p":
            continue

        blips = element.findall(f".//{{{NS_DRAWING}}}blip")
        if not blips:
            blips = element.findall(f".//{{{NS_DRAW}}}blip") if not blips else blips

        rids = []
        for blip in blips:
            rid = blip.get(f"{{{NS_REL}}}embed") or blip.get("r:embed")
            if rid:
                rids.append(rid)

        if not rids:
            for el in element.iter():
                for attr_val in el.attrib.values():
                    if attr_val.startswith("rId") and attr_val in rid_to_image:
                        rids.append(attr_val)

        images_in_para = []
        for rid in rids:
            if rid in rid_to_image:
                images_in_para.append(rid_to_image[rid])

        if images_in_para:
            image_map[idx] = images_in_para

    return image_map


def save_images(image_map: dict, body_to_section_idx: dict,
                img_folder: Path, version: int) -> dict:
    """
    Save images to disk with version prefix.
    Returns: { section_idx: [saved_filename, ...] }
    Scans existing files once to build a hash lookup — avoids per-image glob.
    """
    section_images = {}
    sorted_keys    = sorted(body_to_section_idx.keys())

    # Build hash cache in one pass over the folder
    existing_by_hash: dict = {}   # "{hash8}{ext}" → filename
    if img_folder.exists():
        for f in img_folder.iterdir():
            stem_parts = f.stem.rsplit("_", 1)
            if len(stem_parts) == 2:
                key = stem_parts[1] + f.suffix
                existing_by_hash[key] = f.name

    def find_nearest_section(body_idx):
        best = None
        for k in sorted_keys:
            if k <= body_idx:
                best = body_to_section_idx[k]
            else:
                break
        return best

    for body_idx, images in image_map.items():
        sec_idx = find_nearest_section(body_idx)
        if sec_idx is None:
            continue

        saved = []
        for img_name, img_bytes in images:
            img_hash  = hashlib.md5(img_bytes).hexdigest()[:8]
            stem      = Path(img_name).stem
            ext       = Path(img_name).suffix or ".png"
            key       = f"{img_hash}{ext}"

            if key in existing_by_hash:
                saved.append(existing_by_hash[key])
                continue

            versioned = f"v{version}_{stem}_{img_hash}{ext}"
            (img_folder / versioned).write_bytes(img_bytes)
            existing_by_hash[key] = versioned
            saved.append(versioned)

        if saved:
            section_images.setdefault(sec_idx, []).extend(saved)

    return section_images


# ─── Document Parser ──────────────────────────────────────────────────────────

def parse_docx(file_path):
    from docx import Document
    doc      = Document(file_path)
    sections = []
    current  = None
    body     = doc.element.body

    # ── Step 1: Extract feature headings from 2-column single-row tables ──
    feature_map = {}
    for table in doc.tables:
        if len(table.rows) == 1 and len(table.columns) == 2:
            c0 = table.rows[0].cells[0].text.strip().strip(".")
            c1 = table.rows[0].cells[1].text.strip()
            if c0.isdigit() and c1:
                feature_map[c0] = c1.title()

    body_to_section_idx = {}

    for body_idx, element in enumerate(body):
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag != "p":
            continue

        text = ""
        for node in element.iter():
            ntag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
            if ntag == "t" and node.text:
                text += node.text
        text = text.replace("\t", " ").strip()

        if not text:
            continue

        style_name = ""
        WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        pPr = element.find(f".//{{{WNS}}}pStyle")
        if pPr is not None:
            val = pPr.get(f"{{{WNS}}}val", "")
            style_name = val.lower().replace(" ", "")

        is_bold = len(element.findall(f".//{{{WNS}}}b")) > 0

        import re as _re
        text = _re.sub(r'^(\d+(?:\.\d+)*)([A-Za-z])', r'\1 \2', text)

        match      = RE_HEADING.match(text)
        is_heading = False

        if match:
            number       = match.group(1)
            heading_text = match.group(2).strip()
            level        = len(number.split("."))

            is_heading = (
                "heading" in style_name
                or (level == 2 and ("heading" in style_name or is_bold))
            )

            if is_heading:
                top_num = number.split(".")[0]

                if current is None or current.get("number") != top_num:
                    if current:
                        sections.append(current)
                    feature_name = feature_map.get(top_num, f"Section {top_num}")
                    sections.append({
                        "level":      1,
                        "number":     top_num,
                        "heading":    feature_name,
                        "content":    "",
                        "sort_order": float(top_num) if top_num.isdigit() else 0.0,
                        "is_feature": True,
                        "images":     [],
                    })

                if current and not current.get("is_feature"):
                    sections.append(current)

                try:
                    sort_val = float(number)
                except:
                    sort_val = 0.0

                current = {
                    "level":      level,
                    "number":     number,
                    "heading":    heading_text,
                    "content":    "",
                    "sort_order": sort_val,
                    "is_feature": False,
                    "images":     [],
                    "body_idx":   body_idx,
                }

        if not is_heading and current and not current.get("is_feature"):
            current["content"] += text + "\n"
            body_to_section_idx[body_idx] = len(sections)
            current["_last_body_idx"] = body_idx

    if current and not current.get("is_feature"):
        sections.append(current)

    final_map = {}
    for sec_idx, sec in enumerate(sections):
        if sec.get("is_feature"):
            continue
        s = sec.get("body_idx", 0)
        e = sec.get("_last_body_idx", s)
        for bi in range(s, e + 1):
            final_map[bi] = sec_idx

    if sections:
        sections[0]["_body_to_section_idx"] = final_map

    return sections


# ─── PDF Parser ───────────────────────────────────────────────────────────────

def parse_pdf(file_path: str) -> list:
    try:
        import pdfplumber
    except ImportError:
        print("[ERROR] pdfplumber not installed. Run: pip install pdfplumber")
        return []

    sections      = []
    current       = None
    body_idx      = 0
    final_map     = {}
    feature_map   = {}

    all_sizes = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                for word in (page.extract_words(extra_attrs=["size"]) or []):
                    s = word.get("size", 0)
                    if s:
                        all_sizes.append(round(s, 1))
    except Exception as e:
        print(f"  [pdf] Cannot scan font sizes: {e}")
        return []

    if not all_sizes:
        print(f"  [pdf] No text found in PDF")
        return []

    from statistics import median
    body_median  = median(all_sizes)
    unique_sizes = sorted(set(all_sizes), reverse=True)
    heading_sizes = [s for s in unique_sizes if s > body_median * 1.15][:2]

    if not heading_sizes:
        print(f"  [pdf] Cannot detect heading sizes — using largest font as heading")
        heading_sizes = unique_sizes[:2]

    h1_size = heading_sizes[0] if heading_sizes else 0
    h2_size = heading_sizes[1] if len(heading_sizes) > 1 else 0
    print(f"  [pdf] Body median: {body_median:.1f}pt | H1≥{h1_size}pt | H2≥{h2_size}pt")

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words      = page.extract_words(extra_attrs=["size", "fontname"]) or []
                lines      = _group_words_into_lines(words)

                for line_idx, (line_text, line_size, line_y) in enumerate(lines):
                    body_idx = page_num * 10000 + line_idx
                    text     = line_text.strip()
                    if not text:
                        continue

                    text = re.sub(r'^(\d+(?:\.\d+)*)([A-Za-z])', r'\1 \2', text)

                    match = RE_HEADING.match(text)

                    is_h1 = line_size >= h1_size * 0.95 and match
                    is_h2 = (not is_h1) and h2_size > 0 and line_size >= h2_size * 0.95 and match

                    if is_h1 and match:
                        number       = match.group(1)
                        heading_text = match.group(2).strip()
                        top_num      = number.split(".")[0]

                        if current and not current.get("is_feature"):
                            sections.append(current)
                            current = None

                        feature_name = feature_map.get(top_num, heading_text)
                        if not any(s.get("number") == top_num and s.get("level") == 1
                                   for s in sections):
                            sections.append({
                                "level":      1,
                                "number":     top_num,
                                "heading":    feature_name,
                                "content":    "",
                                "sort_order": float(top_num) if top_num.isdigit() else 0.0,
                                "is_feature": True,
                                "images":     [],
                            })
                        feature_map[top_num] = heading_text

                    elif is_h2 and match:
                        number       = match.group(1)
                        heading_text = match.group(2).strip()
                        level        = len(number.split("."))
                        top_num      = number.split(".")[0]

                        if not any(s.get("number") == top_num and s.get("level") == 1
                                   for s in sections):
                            feature_name = feature_map.get(top_num, f"Section {top_num}")
                            sections.append({
                                "level":      1,
                                "number":     top_num,
                                "heading":    feature_name,
                                "content":    "",
                                "sort_order": float(top_num) if top_num.isdigit() else 0.0,
                                "is_feature": True,
                                "images":     [],
                            })

                        if current and not current.get("is_feature"):
                            sections.append(current)

                        try:
                            sort_val = float(number)
                        except:
                            sort_val = 0.0

                        current = {
                            "level":      level,
                            "number":     number,
                            "heading":    heading_text,
                            "content":    "",
                            "sort_order": sort_val,
                            "is_feature": False,
                            "images":     [],
                            "body_idx":   body_idx,
                        }

                    else:
                        if current and not current.get("is_feature"):
                            current["content"] += text + "\n"
                            final_map[body_idx] = len(sections)
                            current["_last_body_idx"] = body_idx

    except Exception as e:
        print(f"  [pdf] Parse error: {e}")
        return []

    if current and not current.get("is_feature"):
        sections.append(current)

    final_map2 = {}
    for sec_idx, sec in enumerate(sections):
        if sec.get("is_feature"):
            continue
        s = sec.get("body_idx", 0)
        e = sec.get("_last_body_idx", s)
        for bi in range(s, e + 1):
            final_map2[bi] = sec_idx

    if sections:
        sections[0]["_body_to_section_idx"] = final_map2

    return sections


def _group_words_into_lines(words: list) -> list:
    if not words:
        return []

    words = sorted(words, key=lambda w: (round(w.get("top", 0), 1), w.get("x0", 0)))

    lines     = []
    cur_y     = None
    cur_words = []
    Y_THRESH  = 3.0

    for word in words:
        y = round(word.get("top", 0), 1)
        if cur_y is None or abs(y - cur_y) <= Y_THRESH:
            cur_words.append(word)
            cur_y = y
        else:
            if cur_words:
                text  = " ".join(w["text"] for w in cur_words)
                sizes = [w.get("size", 0) for w in cur_words if w.get("size", 0)]
                size  = max(sizes) if sizes else 0
                lines.append((text, size, cur_y))
            cur_words = [word]
            cur_y     = y

    if cur_words:
        text  = " ".join(w["text"] for w in cur_words)
        sizes = [w.get("size", 0) for w in cur_words if w.get("size", 0)]
        size  = max(sizes) if sizes else 0
        lines.append((text, size, cur_y))

    return lines


def extract_images_from_pdf(file_path: str) -> dict:
    try:
        import pdfplumber
    except ImportError:
        return {}

    image_map = {}

    try:
        import fitz
        HAS_FITZ = True
    except ImportError:
        HAS_FITZ = False

    if HAS_FITZ:
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page   = doc[page_num]
                images = page.get_images(full=True)
                for img_idx, img_info in enumerate(images):
                    xref      = img_info[0]
                    base_image = doc.extract_image(xref)
                    img_bytes  = base_image["image"]
                    img_ext    = base_image["ext"]
                    img_name   = f"page{page_num+1}_img{img_idx+1}.{img_ext}"
                    body_idx   = page_num * 10000 + img_idx
                    image_map.setdefault(body_idx, []).append((img_name, img_bytes))
            doc.close()
            return image_map
        except Exception as e:
            print(f"  [pdf] PyMuPDF image extract error: {e}")

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                for img_idx, img in enumerate(page.images or []):
                    try:
                        x0 = img["x0"]; y0 = img["top"]
                        x1 = img["x1"]; y1 = img["bottom"]
                        cropped    = page.crop((x0, y0, x1, y1))
                        img_bytes  = cropped.to_image(resolution=150).original.tobytes("png")
                        img_name   = f"page{page_num+1}_img{img_idx+1}.png"
                        body_idx   = page_num * 10000 + img_idx
                        image_map.setdefault(body_idx, []).append((img_name, img_bytes))
                    except Exception:
                        pass
    except Exception as e:
        print(f"  [pdf] pdfplumber image extract error: {e}")

    return image_map


def detect_menu_path(content):
    match = re.search(r'([A-Z][^>\n]+(?:\s*>\s*[A-Z][^>\n]+){2,})', content)
    return match.group(1).strip() if match else None


def classify_type(heading, content):
    h = heading.lower()
    if any(k in h for k in ["error", "fix", "issue", "cannot", "failed", "unable", "bug"]):
        return "error_fix"
    if any(k in h for k in ["what is", "what are", "difference", "why", "faq", "overview", "about"]):
        return "faq"
    if any(k in h for k in ["list", "definition", "glossary", "status", "field", "setup", "control", "report"]):
        return "reference"
    return "procedure"


# ─── LLM ──────────────────────────────────────────────────────────────────────

def call_llm(prompt, desc="LLM"):
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
                tqdm.write(f"\n  [!] LLM error (attempt {attempt+1}/{MAX_LLM_RETRIES}): {e} — retrying in {wait}s")
                _time.sleep(wait)

    log.warning(f"LLM failed after {MAX_LLM_RETRIES} attempts: {last_exc}")
    return ""


def parse_with_llm(heading, content, entry_type, images=None):
    """Parse entry content into structured steps via LLM."""
    type_hints = {
        "procedure":  "Convert into numbered steps. Each step covers one logical action — include enough detail so the user knows exactly what to do and what fields to fill in.",
        "error_fix":  "Extract: cause of the error, step-by-step fix with field details, how to verify it's resolved.",
        "faq":        "Extract the key question and provide a clear, complete answer.",
        "reference":  "Extract field names, their purpose, accepted values, and important notes.",
    }

    image_hint = ""
    if images:
        image_hint = f"""
The following screenshot images are available for this section (in order of appearance):
{chr(10).join(f'  - {img}' for img in images)}

IMPORTANT image assignment rules:
- Assign images to steps in ORDER — image 1 goes to the first step that shows a screen, image 2 to the next, etc.
- Every image in the list should be assigned to a step if possible.
- Set "image" to null only if a step has no corresponding screenshot.
- Do NOT skip images — if there are {len(images)} images, try to assign all {len(images)} to appropriate steps.
"""

    prompt = f"""You are an ERP documentation parser.

Section: "{heading}"
Type: {entry_type}
Task: {type_hints.get(entry_type, type_hints['procedure'])}
{image_hint}
Raw content:
{content}

Return ONLY valid JSON:
{{
  "summary": "one sentence describing this section",
  "steps": [
    {{
      "step_number": 1,
      "action": "verb phrase describing the action (max 8 words)",
      "description": "detailed explanation of what the user does, including field names and values where relevant",
      "fields": ["field names involved in this step"],
      "image": null
    }}
  ],
  "notes": ["important warnings, tips, or exceptions"]
}}

Rules:
- Max 10 steps — group minor sub-actions into one step if they belong together
- Each step's description should be complete enough for the user to follow without the original document
- Each action must start with a verb
- Answer in English
"""
    raw = call_llm(prompt, desc=f"{entry_type}: {heading[:30]}").strip()
    raw = re.sub(r'^```json\s*|^```\s*|\s*```$', '', raw, flags=re.MULTILINE)
    try:
        data = json.loads(raw)
        return data.get("steps", []), data.get("notes", []), data.get("summary", "")
    except:
        m = re.search(r'\{[\s\S]*"steps"[\s\S]*\}', raw)
        if m:
            try:
                data = json.loads(m.group())
                return data.get("steps", []), data.get("notes", []), data.get("summary", "")
            except:
                pass
    log.warning(f"LLM parse failed for: {heading}")
    return [], [], ""


# ─── Core Ingest ──────────────────────────────────────────────────────────────

def ingest_file(file_path, domain_name, company_code, dry_run, force,
                force_entries=False, workers=None):
    workers = workers or LLM_WORKERS
    label   = f"{company_code or 'global'}/{domain_name}/{Path(file_path).name}"
    print(f"\n  📄 {label}")

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
        print(f"     ✓ No change — skipped (use --force to re-ingest)")
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

    print(f"     Parsing document structure...", end="", flush=True)

    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        sections = parse_pdf(file_path)
    else:
        sections = parse_docx(file_path)

    print(f" {len(sections)} sections found")

    # ── Extract images ─────────────────────────────────────────────
    print(f"     Extracting images...", end="", flush=True)
    img_folder = get_image_folder(file_path, company_code)

    if ext == ".pdf":
        image_map = extract_images_from_pdf(file_path)
    else:
        image_map = extract_images_with_positions(file_path)

    total_imgs = sum(len(v) for v in image_map.values())
    print(f" {total_imgs} image(s) found")

    body_to_section_idx = {}
    if sections:
        body_to_section_idx = sections[0].pop("_body_to_section_idx", {})

    next_ver = 1
    if not dry_run and doc_id:
        row = conn.execute("""
            SELECT COALESCE(MAX(ev.version), 0) FROM entry_versions ev
            JOIN entries e ON ev.entry_id = e.id
            JOIN features f ON e.feature_id = f.id
            WHERE f.domain_id = ?
        """, (domain_id,)).fetchone()
        next_ver = (row[0] or 0) + 1

    if not dry_run:
        section_images = save_images(image_map, body_to_section_idx, img_folder, next_ver)
        tqdm.write(f"     💾 Images saved to: {img_folder}")
    else:
        section_images = {}

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

    # ── Phase A: Walk sections, DB setup, collect entries needing LLM ──────
    pending = []   # entries that need parse_with_llm

    try:
        for sec_idx, section in enumerate(sections):
            level   = section["level"]
            number  = section["number"]
            heading = section["heading"]
            content = section["content"].strip()

            if level == 1:
                tqdm.write(f"     📁 {heading}")
                if not dry_run:
                    current_feature_id = get_or_create_feature(
                        conn, domain_id, heading, int(number.split(".")[0])
                    )
                continue

            if level >= 2 and (dry_run or current_feature_id is not None):
                if not content:
                    entry_pbar.update(1)
                    continue

                menu_path    = detect_menu_path(content)
                entry_type   = classify_type(heading, content)
                raw_hash     = content_hash(content)
                indent       = "  " * (level - 1)
                entry_images = section_images.get(sec_idx, [])
                if not entry_images and section.get("body_idx"):
                    mapped_idx = body_to_section_idx.get(section["body_idx"])
                    if mapped_idx is not None:
                        entry_images = section_images.get(mapped_idx, [])

                if dry_run:
                    pending.append({
                        "sec_idx": sec_idx, "heading": heading, "content": content,
                        "entry_type": entry_type, "entry_images": entry_images,
                        "number": number, "indent": indent, "dry_run": True,
                        "entry_id": None, "is_new": None, "feature_id": None,
                        "menu_path": menu_path, "sort_order": 0,
                    })
                    continue

                try:
                    sort_order = int(float(number) * 10) if number.count(".") == 1 else 0
                except:
                    sort_order = 0

                entry_id, is_new = get_or_create_entry(
                    conn, current_feature_id, heading, entry_type, menu_path, sort_order
                )

                cur_ver = get_current_version(conn, entry_id, company_id)
                if not force_entries and cur_ver and content_hash(cur_ver["raw_content"] or "") == raw_hash:
                    tqdm.write(f"     {indent}[{number}] {heading} [{entry_type}] → no change")
                    stats["skipped"] += 1
                    log_action(conn, doc_id, entry_id, "skipped", "Content unchanged")
                    conn.commit()
                    entry_pbar.update(1)
                    continue

                img_label = f" 🖼 {len(entry_images)}" if entry_images else ""
                tqdm.write(f"     {indent}[{number}] {heading} [{entry_type}]{img_label}")

                pending.append({
                    "sec_idx": sec_idx, "heading": heading, "content": content,
                    "entry_type": entry_type, "entry_images": entry_images,
                    "number": number, "indent": indent, "dry_run": False,
                    "entry_id": entry_id, "is_new": is_new,
                    "feature_id": current_feature_id,
                    "menu_path": menu_path, "sort_order": sort_order,
                })

        # ── Phase B: Parallel LLM calls ──────────────────────────────────────
        llm_results: dict = {}
        if pending:
            tqdm.write(f"\n     ⚡ Running LLM for {len(pending)} entries ({workers} workers)...")
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(
                        parse_with_llm,
                        w["heading"], w["content"], w["entry_type"], w["entry_images"]
                    ): w["sec_idx"]
                    for w in pending
                }
                for fut in as_completed(futures):
                    sec_idx = futures[fut]
                    try:
                        llm_results[sec_idx] = fut.result()
                    except Exception as e:
                        log.warning(f"LLM worker error for sec_idx={sec_idx}: {e}")
                        llm_results[sec_idx] = ([], [], "")

        # ── Phase C: Serial DB writes + collect ChromaDB payloads ────────────
        chroma_payloads = []

        for work in pending:
            steps, notes, summary = llm_results.get(work["sec_idx"], ([], [], ""))
            heading    = work["heading"]
            number     = work["number"]
            indent     = work["indent"]
            entry_type = work["entry_type"]

            if work["dry_run"]:
                img_info = f" 🖼 {len(work['entry_images'])} img(s)" if work["entry_images"] else ""
                tqdm.write(f"     {indent}[{number}] {heading} [{entry_type}] → {len(steps)} steps{img_info}")
                entry_pbar.update(1)
                continue

            if not steps:
                log.warning(f"Zero steps returned by LLM for '{heading}' — skipping version write")
                stats["skipped"] += 1
                entry_pbar.update(1)
                continue

            entry_id   = work["entry_id"]
            is_new     = work["is_new"]
            feature_id = work["feature_id"]
            menu_path  = work["menu_path"]

            try:
                if summary:
                    conn.execute("UPDATE entries SET summary = ? WHERE id = ?", (summary, entry_id))

                new_ver, version_id = add_version(
                    conn, entry_id, company_id, steps, notes,
                    work["content"], Path(file_path).name
                )

                action = "created" if is_new else "version_added"
                log_action(conn, doc_id, entry_id, action, f"v{new_ver} — {len(steps)} steps")
                conn.commit()

                result_label = "✨ created" if is_new else f"🔄 updated → v{new_ver}"
                step_count   = len([s for s in steps if s])
                img_count    = len([s for s in steps if s.get("image")])
                tqdm.write(f"            {result_label} ({step_count} steps, {img_count} with images)")
                stats["created" if is_new else "updated"] += 1

                if CHROMA_AVAILABLE:
                    domain_row  = conn.execute(
                        "SELECT d.name FROM domains d JOIN features f ON f.domain_id=d.id WHERE f.id=?",
                        (feature_id,)
                    ).fetchone()
                    feature_row = conn.execute(
                        "SELECT name FROM features WHERE id=?", (feature_id,)
                    ).fetchone()
                    chroma_payloads.append({
                        "version_id":  version_id,
                        "entry_id":    entry_id,
                        "domain":      domain_row["name"] if domain_row else "",
                        "feature":     feature_row["name"] if feature_row else "",
                        "name":        heading,
                        "type":        entry_type,
                        "menu_path":   menu_path or "",
                        "summary":     summary or "",
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

        # Batch ChromaDB upsert for all entries in this file
        if chroma_payloads:
            n = batch_upsert_entries(
                chroma_payloads,
                company_code=company_code if company_id else None
            )
            tqdm.write(f"     🔍 {n} entries indexed in ChromaDB")

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
    parser.add_argument("--file",          help="Single file to ingest (auto-detect domain from path)")
    parser.add_argument("--domain",        help="Override domain name (e.g. Sales)")
    parser.add_argument("--company",       help="Override company code (e.g. ABC)")
    parser.add_argument("--dry-run",       action="store_true", help="Preview without saving to DB")
    parser.add_argument("--force",         action="store_true", help="Re-ingest even if file unchanged")
    parser.add_argument("--force-entries", action="store_true", help="Re-parse all entries even if content unchanged")
    parser.add_argument("--workers",       type=int, default=None,
                        help=f"Parallel LLM workers (default: LLM_WORKERS={LLM_WORKERS}; use 1 for sequential/debug)")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Knowledge DB not found: {DB_PATH}")
        print(f"        Run: python knowledge_schema.py first")
        sys.exit(1)

    workers = args.workers or LLM_WORKERS
    print(f"\nERP Knowledge Ingest — {'DRY RUN' if args.dry_run else 'LIVE'} | workers={workers}")
    print(f"{'─' * 50}")

    # Single file mode
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
            print("[ERROR] Cannot detect domain from path. Use --domain 'Human Resources'")
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
            file_path     = f["file_path"],
            domain_name   = f["domain"],
            company_code  = f["company_code"],
            dry_run       = args.dry_run,
            force         = args.force,
            force_entries = args.force_entries,
            workers       = workers,
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
