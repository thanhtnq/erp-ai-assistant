# ERP AI Assistant Task Backlog

Mục tiêu: biến assistant thành công cụ có thể kiểm tra được theo yêu cầu trong ảnh, không chỉ trả lời chung chung.

## Priority 0

1. [completed] Dựng bảng năng lực theo requirement
   - Mô tả: gom các yêu cầu trong ảnh vào một bảng `Supported / Partial / Not yet` để trả lời nhất quán khi người dùng hỏi hệ thống có đáp ứng không.
   - Kết quả mong đợi: assistant trả lời được cả câu hỏi tổng quan lẫn từng requirement riêng lẻ.
   - Test: hỏi “what can you do?”, “does it support InvoiceNow?”, “AI demand forecasting có chưa?”.

2. [pending] Chuẩn hóa luồng history theo session
   - Mô tả: chỉ load session hiện tại, load thêm theo lô nhỏ, tránh kéo toàn bộ lịch sử.
   - Kết quả mong đợi: mở lại chat không còn trống, nhưng cũng không tải quá nặng.
   - Test: mở recent chat, refresh trang, kiểm tra chỉ thấy vài message gần nhất và có nút tải thêm.

3. [pending] Hoàn thiện recent chat actions
   - Mô tả: xóa recent thật sự xóa sau reload, bỏ confirm alert nếu không cần, và nối menu ba chấm với các action có chức năng.
   - Kết quả mong đợi: xóa là mất thật, không quay lại sau refresh.
   - Test: xóa 1 chat recent, reload, xác nhận biến mất.

## Priority 1

4. [pending] Khôi phục render ảnh theo từng step
   - Mô tả: bảo toàn ảnh gắn với bước hướng dẫn, cả khi nội dung được stream từ API.
   - Kết quả mong đợi: reply step-by-step hiển thị ảnh giống source cũ.
   - Test: hỏi quy trình có ảnh, xem ảnh xuất hiện ở đúng step.

5. [pending] Tối ưu tốc độ phản hồi và tải lịch sử
   - Mô tả: giảm thời gian loading, giới hạn recent chats, cache nhẹ phía client nếu cần.
   - Kết quả mong đợi: mở UI nhanh hơn khi nhiều người dùng đồng thời.
   - Test: mở nhiều session, đo thời gian load ban đầu và load history.

6. [pending] Phân loại rõ các khoảng trống chức năng AI
   - Mô tả: tách riêng invoice OCR, journal suggestions, anomaly/fraud detection, InvoiceNow readiness, budgeting/forecasting.
   - Kết quả mong đợi: không “hứa quá tay”, có câu trả lời trung thực cho mỗi gap.
   - Test: hỏi từng tính năng AI và đối chiếu với bảng coverage.

## Priority 2

7. [pending] Tạo test script cho từng requirement trong ảnh
   - Mô tả: xây bộ câu hỏi kiểm thử bằng Anh/Việt để chạy regression.
   - Kết quả mong đợi: mỗi requirement có ít nhất 1 câu test chuẩn.
   - Test: dùng bộ câu hỏi này sau mỗi lần đổi model hoặc đổi prompt.
