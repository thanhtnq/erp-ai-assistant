# Sales Training - Hướng dẫn Train & Sử dụng

## 🚀 Cách Train Model

### Bước 1: Extract dữ liệu từ PostgreSQL
```bash
cd d:\Web\erp-ai-assistant
python sales-training/src/extractors/sales_extractor.py
```

Hoặc dùng script tiện lợi:
```bash
sales-training\train.bat
```
Script này sẽ:
1. Extract dữ liệu từ PostgreSQL (scm_sal_main, scm_sal_data)
2. Train 2 model ML:
   - **Churn Prediction**: Dự đoán khách hàng rời bỏ
   - **Sales Forecast**: Dự báo doanh thu
3. Lưu model vào `sales-training/data/models/`

---

## 🤖 Cách Sử dụng (qua Chat)

Sau khi train xong, user có thể hỏi AI Assistant các câu hỏi như:

### Tiếng Việt:
- "top 10 sản phẩm bán chạy nhất"
- "doanh thu tháng 1/2024"
- "phân tích xu hướng doanh thu 3 tháng gần nhất"
- "khách hàng nào mua nhiều nhất"
- "sản phẩm triển vọng nhất"
- "tỷ lệ khách hàng quay lại mua"
- "dự đoán khách hàng rời bỏ" (nếu đã train churn model)
- "dự báo doanh thu 30 ngày tới" (nếu đã train forecast model)

### Tiếng Anh:
- "top 10 best selling products"
- "monthly sales trend"
- "customer segments"
- "product trend analysis"

---

## 🧠 Các Model ML

| Model | Description | Algorithm |
|-------|-------------|-----------|
| Churn Predictor | Predict customers at risk | RandomForest |
| Sales Forecast | Predict revenue | XGBoost / Linear Regression |
| Product Trend | Top potential products | Growth rate analysis |

## 📁 Cấu trúc thư mục

```
sales-training/
├── analyze_sales_bridge.py    # Python bridge cho Skills Server
├── config/
│   ├── database.json          # Kết nối PostgreSQL
│   └── mapping.json           # Mapping data
├── data/
│   ├── processed/             # Dữ liệu đã xử lý (parquet)
│   └── models/                # Model đã train (.pkl)
├── src/
│   ├── extractors/            # Lấy dữ liệu từ DB
│   ├── transformers/          # Xử lý dữ liệu
│   ├── trainers/              # Train ML models
│   ├── analysis/              # Phân tích xu hướng
│   └── query/                 # Query interface
└── README.md