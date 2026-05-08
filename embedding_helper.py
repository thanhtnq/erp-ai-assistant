"""
ERP AI — Embedding & ChromaDB & Reranker Helper
Used by: ingest/ingest_knowledge.py, ingest/ingest_tickets.py, api.py

Place this file at project root: erp-ai-v2/embedding_helper.py
"""

import sys
import requests as _requests
from pathlib import Path

from google import genai

# ── Config import ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "ingest"))
from ingest_config import (
    GEMINI_API_KEY, EMBEDDING_MODEL,
    CHROMA_DIR, CHROMA_COLLECTION_GLOBAL, CHROMA_COLLECTION_PREFIX,
    RERANKER_MODEL, RERANK_MIN_SCORE, VECTOR_TOP_K, RERANK_TOP_N,
    EMBED_BATCH_SIZE, CHROMA_BATCH_SIZE,
)

_gemini_client = genai.Client(api_key=GEMINI_API_KEY)

_EMBED_BASE = "https://generativelanguage.googleapis.com/v1beta"

# ── ChromaDB ──────────────────────────────────────────────────────────────────
try:
    import chromadb
    _chroma_client = None

    def get_chroma_client():
        global _chroma_client
        if _chroma_client is None:
            _chroma_client = chromadb.PersistentClient(
                path=str(Path(CHROMA_DIR).resolve())
            )
        return _chroma_client

    def get_collection(company_code=None):
        client = get_chroma_client()
        name   = (f"{CHROMA_COLLECTION_PREFIX}{company_code.lower()}"
                  if company_code else CHROMA_COLLECTION_GLOBAL)
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    CHROMA_AVAILABLE = True

except ImportError:
    CHROMA_AVAILABLE = False
    print("[--] ChromaDB not installed. Run: pip install chromadb")

# ── Embedding via Gemini REST (embedContent) ──────────────────────────────────
# Note: google-genai SDK uses batchEmbedContents which is unsupported for
# text-embedding-004, so we call the embedContent REST endpoint directly.

def embed_text(text, is_query=False):
    if not text or not text.strip():
        return None
    task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    url = f"{_EMBED_BASE}/models/{EMBEDDING_MODEL}:embedContent"
    try:
        resp = _requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={
                "model": f"models/{EMBEDDING_MODEL}",
                "content": {"parts": [{"text": text.strip()}]},
                "taskType": task_type,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]
    except Exception as e:
        print(f"  [embed] Error: {e}")
    return None


def test_embedding():
    vec = embed_text("test embedding")
    print(f"[embed] {'OK' if vec else 'FAIL'} — dims: {len(vec) if vec else 0}")


def build_entry_text(entry):
    parts = []
    for key, label in [("domain","Domain"),("feature","Feature"),("name","Title"),
                        ("type","Type"),("menu_path","Menu"),("summary","Summary")]:
        if entry.get(key):
            parts.append(f"{label}: {entry[key]}")
    steps = entry.get("steps", [])
    if steps:
        step_texts = [
            f"{s.get('step_number','')}. {s.get('action','')} — {s.get('description','')[:120]}"
            for s in steps[:6]
        ]
        parts.append("Steps: " + " | ".join(step_texts))
    notes = entry.get("notes", [])
    if notes:
        parts.append("Notes: " + " | ".join(str(n)[:80] for n in notes[:3]))
    return ". ".join(parts)


# ── ChromaDB CRUD ─────────────────────────────────────────────────────────────

def embed_texts_batch(texts: list, is_query: bool = False) -> list:
    """Embed multiple texts via individual Gemini embedContent calls.
    Returns a list parallel to `texts`: each element is a vector or None on failure.
    Note: batchEmbedContents is not supported for text-embedding-004, so we loop.
    """
    out = [None] * len(texts)
    for i, t in enumerate(texts):
        if not t or not t.strip():
            continue
        out[i] = embed_text(t, is_query=is_query)
    return out


def batch_upsert_entries(entries: list, company_code=None) -> int:
    """Embed and upsert a list of entry dicts in batched Ollama + ChromaDB calls.
    Returns the number of successfully upserted entries.
    """
    if not CHROMA_AVAILABLE or not entries:
        return 0

    texts = [build_entry_text(e) for e in entries]

    # Embed in batches of EMBED_BATCH_SIZE
    all_vectors: list = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch_vecs = embed_texts_batch(texts[i:i + EMBED_BATCH_SIZE])
        all_vectors.extend(batch_vecs)

    ids, embeddings, documents, metadatas = [], [], [], []
    for entry, text, vector in zip(entries, texts, all_vectors):
        if not vector:
            continue
        ids.append(f"v{entry['version_id']}")
        embeddings.append(vector)
        documents.append(text)
        metadatas.append({
            "version_id":  int(entry["version_id"]),
            "entry_id":    int(entry.get("entry_id", 0)),
            "domain":      entry.get("domain", ""),
            "feature":     entry.get("feature", ""),
            "name":        entry.get("name", ""),
            "type":        entry.get("type", ""),
            "source_type": entry.get("source_type", "document"),
            "is_flagged":  int(entry.get("is_flagged", False)),
            "company":     company_code or "_global",
        })

    if not ids:
        return 0

    collection = get_collection(company_code)
    for i in range(0, len(ids), CHROMA_BATCH_SIZE):
        collection.upsert(
            ids=ids[i:i + CHROMA_BATCH_SIZE],
            embeddings=embeddings[i:i + CHROMA_BATCH_SIZE],
            documents=documents[i:i + CHROMA_BATCH_SIZE],
            metadatas=metadatas[i:i + CHROMA_BATCH_SIZE],
        )
    return len(ids)


def upsert_entry(entry, company_code=None):
    if not CHROMA_AVAILABLE:
        return False
    text   = build_entry_text(entry)
    vector = embed_text(text, is_query=False)
    if not vector:
        return False
    collection = get_collection(company_code)
    doc_id     = f"v{entry['version_id']}"
    metadata   = {
        "version_id":  int(entry["version_id"]),
        "entry_id":    int(entry.get("entry_id", 0)),
        "domain":      entry.get("domain", ""),
        "feature":     entry.get("feature", ""),
        "name":        entry.get("name", ""),
        "type":        entry.get("type", ""),
        "source_type": entry.get("source_type", "document"),
        "is_flagged":  int(entry.get("is_flagged", False)),
        "company":     company_code or "_global",
    }
    collection.upsert(ids=[doc_id], embeddings=[vector], documents=[text], metadatas=[metadata])
    return True


def delete_entry_from_chroma(version_id, company_code=None):
    if not CHROMA_AVAILABLE:
        return
    try:
        get_collection(company_code).delete(ids=[f"v{version_id}"])
    except Exception as e:
        print(f"  [chroma] Delete error: {e}")


def vector_search(query, company_code=None, top_k=None,
                  feature_name=None, domain_name=None, type_names=None):
    if not CHROMA_AVAILABLE:
        return []
    query_vec = embed_text(query, is_query=True)
    if not query_vec:
        return []
    top_k = top_k or VECTOR_TOP_K
    conditions = []
    if feature_name:
        conditions.append({"feature": {"$eq": feature_name}})
    if domain_name:
        conditions.append({"domain":  {"$eq": domain_name}})
    if type_names:
        if len(type_names) == 1:
            conditions.append({"type": {"$eq": type_names[0]}})
        else:
            conditions.append({"type": {"$in": type_names}})
    where = ({"$and": conditions} if len(conditions) > 1
             else conditions[0] if conditions else None)
    try:
        collection = get_collection(company_code)
        count      = collection.count()
        if count == 0:
            return []
        kwargs = {
            "query_embeddings": [query_vec],
            "n_results":        min(top_k, count),
            "include":          ["metadatas", "documents", "distances"],
        }
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        output  = []
        for i, meta in enumerate(results["metadatas"][0]):
            output.append({
                **meta,
                "chroma_score": 1 - results["distances"][0][i],
                "document":     results["documents"][0][i],
            })
        return output
    except Exception as e:
        print(f"  [chroma] Search error: {e}")
        return []


# ── CrossEncoder Reranker ─────────────────────────────────────────────────────

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            print(f"  [reranker] Loading {RERANKER_MODEL}...")
            _reranker = CrossEncoder(RERANKER_MODEL)
            print(f"  [reranker] Ready")
        except ImportError:
            print("[--] sentence-transformers not installed. Run: pip install sentence-transformers")
        except Exception as e:
            print(f"  [reranker] Load error: {e}")
    return _reranker


def rerank(query, candidates, top_n=None):
    top_n = top_n or RERANK_TOP_N
    if not candidates:
        return []
    reranker = get_reranker()
    if not reranker:
        return sorted(candidates, key=lambda x: x.get("chroma_score", 0), reverse=True)[:top_n]
    try:
        pairs  = [(query, c["document"]) for c in candidates]
        scores = reranker.predict(pairs)
        for c, score in zip(candidates, scores):
            c["rerank_score"] = float(score)
        filtered = [c for c in candidates if c.get("rerank_score", -99) >= RERANK_MIN_SCORE]
        ranked   = sorted(filtered, key=lambda x: x["rerank_score"], reverse=True)
        print(f"  [reranker] {len(candidates)} → {len(ranked)} (min={RERANK_MIN_SCORE})")
        for r in ranked[:top_n]:
            print(f"    {r.get('rerank_score',0):.3f} | "
                  f"{r.get('domain','')} > {r.get('feature','')} > {r.get('name','')}")
        return ranked[:top_n]
    except Exception as e:
        print(f"  [reranker] Error: {e}")
        return candidates[:top_n]
