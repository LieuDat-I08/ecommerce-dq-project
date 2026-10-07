# Automated Data Pipeline & Data Observability — E-commerce

Xây dựng đường ống dữ liệu tự động và nền tảng Giám sát chất
lượng dữ liệu ứng dụng trong phân tích hành vi mua sắm Thương mại
điện tử.

## Features
- Trích xuất và nạp dữ liệu thô từ hệ thống nguồn.
- Xử lý, làm sạch và xây dựng các mô hình dữ liệu.
- Kiểm tra và giám sát chất lượng dữ liệu tự động.
- Điều phối tập trung toàn bộ vòng đời dữ liệu.

## Technologies
- **Data Warehouse:** Google BigQuery
- **Orchestration:** Kestra
- **Transformation:** dbt
- **Data Quality:** Great Expectations / Python Script
- **Infrastructure:** Docker & Docker Compose

## Project Structure

```text
/
├── ingestion/        # Trích xuất và nạp dữ liệu thô
├── dbt/              # Các model xử lý và biến đổi dữ liệu
├── observability/    # Module kiểm tra chất lượng dữ liệu
├── orchestration/    # Định nghĩa flow điều phối tự động
├── docs/             # Sơ đồ kiến trúc và tài liệu dự án
└── docker-compose.yaml
