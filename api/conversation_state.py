"""
Small conversation-state extractor for context-first ERP query routing.

The state intentionally stores only business-visible context. Internal ERP
identifiers such as uniquenum_pri are ignored here and should not be displayed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re


_DOC_NUMBER_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9-]*\d{4,}[A-Z0-9-]*\b", re.IGNORECASE)
_INTERNAL_KEYS_RE = re.compile(
    r"\b(?:uniquenum_pri|uniquenum_uniq|masterfn|companyfn|party_unique|"
    r"tag_void_yn|tag_deleted_yn)\b",
    re.IGNORECASE,
)


@dataclass
class ConversationState:
    last_module: str = ""
    last_document_type: str = ""
    last_document_no: str = ""
    last_report_id: str = ""
    last_tab: str = ""
    last_result_shape: str = ""
    last_result_columns: list[str] = field(default_factory=list)


def _strip_internal(text: str) -> str:
    return _INTERNAL_KEYS_RE.sub("", text or "")


def _latest_prefixed_lines(history_text: str, prefix: str, limit: int = 8) -> list[str]:
    rows: list[tuple[str, list[str]]] = []
    current_role = ""
    current_lines: list[str] = []
    role_re = re.compile(r"^(User|Assistant):\s*(.*)$")

    for raw_line in (history_text or "").splitlines():
        match = role_re.match(raw_line)
        if match:
            if current_role:
                rows.append((current_role, current_lines))
            current_role = match.group(1)
            current_lines = [match.group(2)]
        elif current_role:
            current_lines.append(raw_line)
    if current_role:
        rows.append((current_role, current_lines))

    selected: list[str] = []
    for role, lines in reversed(rows):
        if role == prefix:
            selected.append(_strip_internal("\n".join(lines).strip()))
            if len(selected) >= limit:
                break
    return selected


def _extract_document_no(text: str) -> str:
    matches = _DOC_NUMBER_RE.findall(text or "")
    return matches[-1].upper() if matches else ""


def _extract_tab(text: str) -> str:
    q = (text or "").lower()
    if re.search(r"\bdriver\s*info|driver\s*infor?|vehicle|shipping\s*by|transport(?:ation)?\s*cost\b", q):
        return "Driver Info"
    if re.search(r"\bdetail\s*items?|line\s*items?|products?|services?\b", q):
        return "Detail Items"
    if re.search(r"\bsales\s+order\s+(?:header|listing)|\bheader\b", q):
        return "Sales Order Header"
    return ""


def _extract_columns(text: str) -> list[str]:
    for line in (text or "").splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.strip("| ").split("|") if c.strip()]
        if len(cols) >= 2 and not all(re.fullmatch(r"[-:\s]+", c) for c in cols):
            return [_strip_internal(c) for c in cols if _strip_internal(c)]
    return []


def _parse_markdown_table(text: str, max_rows: int = 30) -> tuple[list[str], list[list[str]]]:
    lines = [line.strip() for line in (text or "").splitlines() if "|" in line]
    if len(lines) < 2:
        return [], []

    header: list[str] = []
    body_rows: list[list[str]] = []
    for idx, line in enumerate(lines):
        cols = [c.strip() for c in line.strip("| ").split("|")]
        if len(cols) < 2:
            continue
        if not header:
            header = [_strip_internal(c) for c in cols if _strip_internal(c)]
            continue
        if all(re.fullmatch(r"[-:\s]+", c or "") for c in cols):
            continue
        clean = [_strip_internal(c) for c in cols[:len(header)]]
        if any(clean):
            body_rows.append(clean)
        if len(body_rows) >= max_rows:
            break
    return header, body_rows


def _numeric_value(value: str) -> float | None:
    raw = re.sub(r"[^\d.\-]", "", value or "")
    if not raw or raw in {"-", ".", "-."}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def build_result_metadata(answer_text: str, source_query: str = "") -> dict:
    """Build small, safe metadata for the latest assistant data result."""
    columns, rows = _parse_markdown_table(answer_text)
    metadata = {
        "shape": "table" if columns and rows else "",
        "row_count": len(rows),
        "columns": columns,
        "chartable": False,
        "default_chart": "",
        "source_query": source_query or "",
    }
    if not columns or len(rows) < 2:
        return metadata

    numeric_columns = []
    for idx, column in enumerate(columns):
        numeric_hits = sum(1 for row in rows if idx < len(row) and _numeric_value(row[idx]) is not None)
        if numeric_hits >= 2:
            numeric_columns.append(column)

    label_columns = [c for c in columns if c not in numeric_columns]
    metadata["chartable"] = bool(label_columns and numeric_columns)
    metadata["default_chart"] = "bar" if metadata["chartable"] else ""
    return metadata


def build_conversation_state(history_text: str) -> ConversationState:
    """Build a compact business state from recent chat history."""
    state = ConversationState()
    user_lines = _latest_prefixed_lines(history_text, "User")
    assistant_lines = _latest_prefixed_lines(history_text, "Assistant")
    latest_text = "\n".join(user_lines[:1] + assistant_lines[:2])
    all_recent = "\n".join(user_lines + assistant_lines)

    state.last_document_no = _extract_document_no("\n".join(user_lines)) or _extract_document_no(all_recent)
    if state.last_document_no.startswith("SO") or re.search(r"\bsales?\s+ord(?:er|e)?\b", all_recent, re.IGNORECASE):
        state.last_module = "sales"
        state.last_document_type = "sales_order"

    state.last_tab = _extract_tab(latest_text) or _extract_tab(all_recent)
    if state.last_tab == "Driver Info":
        state.last_report_id = "SAL-SO-DRIVER-INFO"
    elif state.last_tab == "Detail Items":
        state.last_report_id = "SAL-SO-DETAIL"
    elif state.last_tab == "Sales Order Header":
        state.last_report_id = "SAL-SO-LIST"

    columns = _extract_columns("\n".join(assistant_lines))
    if columns:
        state.last_result_shape = "table"
        state.last_result_columns = columns

    return state
