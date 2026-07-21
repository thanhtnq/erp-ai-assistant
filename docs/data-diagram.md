# ERP AI Assistant Chatbox Workflow Diagram

## 1. Tổng Quan Kiến Trúc (High-Level Architecture)

```mermaid
flowchart LR
    subgraph S1["1. Chuẩn Bị Dữ Liệu"]
        docs["Tài liệu ERP<br/>quy trình, hướng dẫn, FAQ"]
        erpdb["ERP Database<br/>dữ liệu vận hành thực tế"]
        prepare["Lập chỉ mục / trích xuất<br/>chuẩn bị dữ liệu cho AI"]
        prepared["Kho dữ liệu AI<br/>kiến thức + dữ liệu phân tích"]

        docs --> prepare
        erpdb --> prepare
        prepare --> prepared
    end

    subgraph S2["2. Người Dùng Hỏi"]
        user["Người dùng ERP"]
        chatbox["AI Chatbox<br/>màn hình hỏi đáp"]

        user --> chatbox
    end

    subgraph S3["3. AI Hiểu Câu Hỏi"]
        backend["AI Backend<br/>nhận câu hỏi và ngữ cảnh"]
        history["Lịch sử hội thoại<br/>câu hỏi trước đó"]
        classify{"Phân loại câu hỏi"}

        backend --> history
        backend --> classify
    end

    subgraph S4["4. Lấy Dữ Liệu Phù Hợp"]
        knowledge["Tìm trong kho kiến thức<br/>nếu hỏi cách làm / quy trình"]
        live_data["Truy vấn dữ liệu ERP<br/>nếu hỏi số liệu thực tế"]
        clarify["Hỏi lại người dùng<br/>nếu câu hỏi chưa đủ rõ"]

        classify -->|Hỏi quy trình| knowledge
        classify -->|Hỏi số liệu| live_data
        classify -->|Thiếu thông tin| clarify
    end

    subgraph S5["5. AI Tạo Câu Trả Lời"]
        llm["LLM / AI Model<br/>đọc dữ liệu và diễn giải"]
        final_answer["Câu trả lời cuối cùng<br/>ngắn gọn, dễ hiểu, có bảng nếu cần"]

        llm --> final_answer
    end

    subgraph S6["6. Hiển Thị Trên Chatbox"]
        stream["Stream kết quả từng phần<br/>trạng thái, nội dung, nguồn tham khảo"]
        render["Chatbox render kết quả<br/>text, bảng, từng bước, gợi ý biểu đồ"]

        stream --> render
    end

    chatbox --> backend
    prepared --> knowledge
    prepared -. hỗ trợ kiểm tra / dự phòng .-> live_data
    erpdb --> live_data
    knowledge --> llm
    live_data --> llm
    clarify --> final_answer
    final_answer --> stream
    render --> user
```

### Workflow Tóm Tắt

| Bước | Khung | Ý nghĩa |
|---|---|---|
| 1 | Chuẩn bị dữ liệu | Hệ thống lấy tài liệu ERP và dữ liệu ERP thật để chuẩn bị cho AI sử dụng. |
| 2 | Người dùng hỏi | Người dùng nhập câu hỏi trực tiếp trong AI Chatbox. |
| 3 | AI hiểu câu hỏi | Backend đọc câu hỏi, xem lịch sử hội thoại và xác định ý định. |
| 4 | Lấy dữ liệu phù hợp | Nếu hỏi quy trình thì tìm trong kho kiến thức; nếu hỏi số liệu thì truy vấn ERP; nếu chưa rõ thì hỏi lại. |
| 5 | AI tạo câu trả lời | LLM đọc dữ liệu liên quan và viết lại thành câu trả lời dễ hiểu. |
| 6 | Hiển thị trên Chatbox | Chatbox nhận kết quả dạng stream và hiển thị cho người dùng. |

### Nguyên Tắc Chính

- AI chỉ đọc dữ liệu ERP, không tự ý chỉnh sửa dữ liệu gốc.
- Mỗi câu hỏi về dữ liệu ERP đều được giới hạn theo đúng công ty/tenant của người dùng.
- Dữ liệu trích xuất dùng để hỗ trợ kiểm tra, tăng tốc hoặc dự phòng; dữ liệu live vẫn lấy từ ERP Database khi cần số liệu mới nhất.

