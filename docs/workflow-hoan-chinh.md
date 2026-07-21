# Workflow Phát Triển Feature Hoàn Chỉnh

> **Quy trình bắt buộc** — áp dụng cho tất cả AI agents và developers trên project này.

---

## Sơ đồ tổng quan

```
📚 Đọc Docs ──► 🔍 CodeGraph ──► 📋 Phân tích ──► ✏️ Code ──► 🧪 Test ──► 🔄 Sync
    Bước 1          Bước 2          Bước 3         Bước 4        Bước 5       Bước 6
```

---

## Bước 1: Đọc tài liệu (Docs First)

**Mục tiêu:** Hiểu rules, architecture, design specs trước khi làm.

| Thứ tự | File | Mục đích |
|--------|------|----------|
| 1 | `docs/codegraph-workflow.md` | Quy tắc workflow bắt buộc |
| 2 | `docs/cfml-sync-rules.md` | Quy tắc sync CFML, API key, ERP cookies |
| 3 | `docs/erp-shell-asset-fixes.md` | Fix assets ERP shell |
| 4 | `docs/superpowers/specs/*.md` | Design specs cho feature |
| 5 | `ROLE.md` | System prompt, guardrails, behavior rules |
| 6 | `README.md` | Kiến trúc project, setup, daily operation |
| 7 | `docs/ai_assistant_feature_tasks.md` | Kế hoạch feature implementation |
| 8 | `docs/ai-requirement-data-mapping.md` | Schema audit, data mapping |

**Các docs khác (đọc khi cần):**
- `docs/erp-ai-capability-matrix.md` — Ma trận coverage
- `docs/memo_admin_columns.md` — Schema memo admin
- `docs/contentadmin_audit_training_tasks.md` — Audit logic training
- `docs/system-architecture-graph.md` — **MỚI** — Kiến trúc tổng thể, API router map, data flow diagrams, DB schemas

---

## Bước 2: Dùng CodeGraph để hiểu Architecture

**Mục tiêu:** Visualize dependencies, class hierarchies, data flow.

### 2.1 Kiểm tra trạng thái CodeGraph

```bash
codegraph status
```

Kết quả mong đợi: `[OK] Index is up to date`

### 2.2 Nếu có pending changes, sync index

```bash
codegraph sync
```

### 2.3 Generate diagram cho khu vực liên quan

Trong VS Code: `Ctrl+Shift+P` → `CodeGraph: Generate Diagram`

Hoặc dùng CLI:
```bash
codegraph diagram api/routers/chat.py
```

### 2.4 Tra cứu dependencies

```bash
# Xem file nào import file này
codegraph deps --incoming api/routers/chat.py

# Xem file này import những gì
codegraph deps --outgoing api/routers/chat.py
```

---

## Bước 3: Phân tích & Map Dependencies

**Mục tiêu:** Xác định tất cả files/modules/services liên quan đến task.

### 3.1 Trace pipeline

Ví dụ cho chat feature:
```
Frontend (CFML) ──► API Router ──► Chat Handler ──► LLM Call ──► Skills Server
                                                      │
                                                      └──► Knowledge Base (SQLite + ChromaDB)
```

### 3.2 Xác định các files cần thay đổi

| Layer | Công nghệ | Thư mục |
|-------|-----------|---------|
| Frontend | CFML | `cfml-examples/` |
| API | Python/FastAPI | `api/routers/`, `api/main.py` |
| Services | Python | `api/services/` |
| Models | Python | `api/models.py` |
| Fraud Engine | Python | `api/fraud/` (domain.py, engine.py, rules.py) |
| Skills | Node.js | `skills/globe3-*/` |
| Database | SQLite / PostgreSQL | `data/`, `.env` config |
| Ingestion | Python | `ingest/` |
| SCM Training | Python | `scm_training/` |

### 3.3 Kiểm tra impact

- API endpoints → router files → service layer → database/models
- Frontend templates → API calls → data flow
- Sync rules giữa `cfml-examples/` và ColdFusion server

---

## Bước 4: Code (Smallest Possible Patch)

**Mục tiêu:** Chỉ sửa đúng những gì cần thiết, không scope creep.

### 4.1 Nguyên tắc

1. **Giải thích root cause trước khi sửa**
   - Vấn đề là gì?
   - Tại sao nó xảy ra (root cause)?
   - Giải pháp nhỏ nhất là gì?

2. **Một thay đổi tại một thời điểm**
   - Không refactor code không liên quan
   - Chỉ sửa những gì được yêu cầu

3. **Theo đúng pattern có sẵn**
   - Học từ các endpoints/services tương tự
   - Giữ nguyên response format, error handling pattern

### 4.2 Ví dụ: Thêm endpoint mới

```python
# Pattern: router → service → response
@router.post("/analytics/fraud-scan")
async def fraud_scan(
    request: FraudScanRequest,
    api_key: str = Depends(verify_api_key)
):
    # 1. Validate scope
    # 2. Call service
    # 3. Return response
    pass
```

### 4.3 Kiểm tra coding standards

- Python: type hints, docstrings, error handling
- Node.js: async/await, error boundaries
- CFML: ERP cookie context, API key server-side

---

## Bước 5: Test

**Mục tiêu:** Đảm bảo feature hoạt động đúng và không regression.

### 5.1 Các loại test cần có

| Loại test | Mô tả | Ví dụ |
|-----------|-------|-------|
| Unit test | Test function/service riêng lẻ | `tests/test_ai_analytics.py` |
| Integration test | Test API endpoint | `POST /analytics/fraud-scan` |
| Scope isolation | Test cross-company không cho phép | Gọi API với masterfn khác |
| Validation test | Test request validation | Thiếu scope → 400 |
| Regression test | Test tính năng cũ không hỏng | Chat SSE stream vẫn chạy |

### 5.2 Test commands

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_ai_analytics.py -v

# Test API manually
curl -X POST http://localhost:8000/analytics/fraud-scan \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"masterfn": "...", "companyfn": "..."}'
```

### 5.3 Kiểm tra frontend (nếu có UI changes)

- Mở file CFML trong browser (qua ColdFusion server)
- Test desktop và mobile widths
- Kiểm tra loading/error/empty states

---

## Bước 6: Sync & Deploy

**Mục tiêu:** Đưa thay đổi lên môi trường production.

### 6.1 Sync CFML files (nếu có thay đổi frontend)

```bash
# Sync một lần
.\scripts\sync_cfml_examples.ps1

# Hoặc chạy watcher trong khi dev
.\scripts\sync_cfml_examples.ps1 -Watch
```

### 6.2 Kiểm tra health sau deploy

```bash
# 1. FastAPI health
curl http://localhost:8000/health

# 2. Skills server health
curl http://localhost:3001/health

# 3. Kiểm tra API key trong CFML page
# Mở browser và kiểm tra network tab
```

### 6.3 Commit & Push

```bash
git add .
git commit -m "feat: mô tả ngắn gọn về feature"
git push
```

---

## Checklist rút gọn (Quick Reference)

```
[ ] Đọc docs/ liên quan (bao gồm docs/system-architecture-graph.md)
[ ] codegraph status → codegraph sync (nếu cần)
[ ] codegraph deps để map dependencies
[ ] Xác định root cause / approach
[ ] Code với smallest possible patch
[ ] Chạy tests
[ ] Sync CFML (nếu có UI changes)
[ ] Kiểm tra health
[ ] Commit
```

---

## Ví dụ thực tế: Thêm Fraud Scan Endpoint

### Bước 1: Đọc docs
- `docs/ai_assistant_feature_tasks.md` → P0.3 Scoped analytics endpoints
- `docs/ai-requirement-data-mapping.md` → 100.06 Finance anomaly

### Bước 2: CodeGraph
```bash
codegraph status
codegraph deps --outgoing api/routers/analytics_fraud.py
```

### Bước 3: Phân tích
- Router: `api/routers/analytics_fraud.py`
- Models: `api/models.py` (FraudScanRequest, FraudScanResponse)
- Service: `api/services/erp_db.py` (ERP database queries)
- Main: `api/main.py` (router registration)

### Bước 4: Code
- Thêm endpoint `POST /analytics/fraud-scan`
- Validate scope (masterfn, companyfn)
- Gọi skills server hoặc direct DB query
- Trả về structured JSON response

### Bước 5: Test
```bash
pytest tests/test_ai_analytics.py -v -k "fraud"
curl -X POST http://localhost:8000/analytics/fraud-scan ...
```

### Bước 6: Sync
```bash
git add .
git commit -m "feat: add fraud scan analytics endpoint"
```
