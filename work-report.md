# ERP AI Assistant — Báo Cáo Năng Lực Dự Án

> **Dự án:** Globe3 ERP AI Assistant V2  
> **Mục tiêu:** Trợ lý AI đa-tenant cho ERP Globe3 — hỏi đáp thông minh, phát hiện gian lận, dự báo & cảnh báo

---

## 🎯 Dự Án Này Làm Được Gì?

### 1. 🤖 Chatbot ERP thông minh (RAG + Live Data)
- **Hỏi đáp bằng tiếng Việt / English** về dữ liệu ERP realtime
- **Tra cứu kiến thức** từ tài liệu (docx/pdf) đã ingest vào ChromaDB
- **Truy vấn trực tiếp PostgreSQL** — doanh số, tồn kho, mua hàng, kế toán, nhân sự...
- **Phân biệt ý định** (intent detection) + **làm rõ câu hỏi mơ hồ** (ambiguity check)
- **Stream kết quả** qua SSE — realtime, không chờ đợi

### 2. 📊 Phân tích Chuỗi Cung Ứng (SCM) — 15/15 câu hỏi ✅
| Tính năng | Mô tả |
|---|---|
| Dự báo nhu cầu SKU | Theo tuần/tháng, khoảng tin cậy, backtest accuracy |
| Đề xuất tái đặt hàng | Reorder point, safety stock, MOQ, ngày nhận dự kiến |
| Phát hiện bất thường tồn kho | Điều chỉnh lớn bất thường, hao hụt, âm kho |
| Cảnh báo hết hạn lô | Ngày hết hạn, giá trị rủi ro, mức tiêu thụ dự kiến |
| Xếp hạng rủi ro hết hàng | Days of cover, stockout score, ưu tiên đặt hàng |

### 3. 🔍 Phát hiện Gian Lận & Bất Thường Tài Chính
| Tính năng | Trạng thái |
|---|---|
| Phát hiện hóa đơn/thanh toán trùng | ✅ Đã chạy |
| Phát hiện giao dịch AP bất thường (cao, lạ, vendor mới) | ⚠️ Một phần |
| Phát hiện tài khoản ngân hàng vendor bị dùng chung | ✅ Đã chạy |
| Kiểm tra cân đối journal (debit/credit) | ✅ Đã chạy |
| So khớp 3 chiều Invoice/PO/GRN | ✅ Đã chạy |
| Phát hiện thanh toán chưa đối chiếu | ✅ Đã chạy |
| Phát hiện giao dịch ngoài giờ làm việc | 🔜 Đang làm |
| Kiểm tra approval bypass / vượt hạn mức | 🔜 Đang làm |
| **Quy trình xử lý alert** (new → investigating → confirmed/false positive) | ✅ Đã chạy |

### 4. ⚙️ Fraud Detection Engine (Chạy nền theo lịch)
- **10+ rule** phát hiện: amount cao, frequency spike, refunds, voids, backdating, giờ bất thường...
- **Chống trùng lặp** bằng SHA-256 hash
- **Configurable thresholds** qua biến môi trường
- **Full lifecycle**: acknowledge / resolve / hide + audit trail
- **59 unit tests** passed

### 5. 🧠 Tích hợp AI
- **Gemini API** — xử lý ngôn ngữ tự nhiên, sinh câu trả lời
- **Hybrid search** — kết hợp vector search (ChromaDB) + keyword search
- **Session history** — giữ ngữ cảnh hội thoại (SKU, vendor, location, top-N...)
- **Bilingual** — hỏi bằng tiếng Việt hoặc English, đều trả lời được

### 6. 🛡️ An toàn & Kiểm soát
- **Tenant-scoped** — mọi truy vấn đều có `masterfn`/`companyfn`
- **Read-only** — không bao giờ ghi vào ERP
- **Query timeout** (15s), row limit, pagination
- **Audit log** — JSONL rotation 10MB
- **Mask dữ liệu nhạy cảm** — số tài khoản ngân hàng chỉ hiện 4 số cuối

---

## 📈 Hiện Trạng

| Hạng mục | SL |
|---|---|
| Đã hoàn thành | 15 truy vấn SCM + 2 nền tảng + Fraud Engine |
| Đang làm P0 | 9 |
| Sẽ làm P1 | 14 |
| P2 (sau này) | 1 |

---

## 🚧 Đang Chờ Gì?

1. **ERP-owner xác nhận** — định nghĩa business, field mapping, nguồn dữ liệu
2. **Cross-tenant tests** — kiểm tra fail-closed, review query plan trên database lớn
3. **Hoàn thiện P0 Finance** — approval bypass, working-hours, split transactions...

---

## 🏗️ Kiến Trúc Hệ Thống

```
User ──► FastAPI ──► Gemini LLM
              │
              ├── ChromaDB (knowledge base)
              ├── SQLite (erp_knowledge.db)
              └── Skills Server (Node.js) ──► PostgreSQL (ERP live data)
                                                    │
                                              Fraud Engine (scheduled)
```

| Service | URL |
|---|---|
| FastAPI | `localhost:8000` |
| Skills | `localhost:3001` |
| PostgreSQL | `localhost:5432` |
