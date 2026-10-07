# Automated Data Pipeline & Data Observability — E-commerce

Xây dựng đường ống dữ liệu tự động và nền tảng Giám sát chất
lượng dữ liệu ứng dụng trong phân tích hành vi mua sắm Thương mại
điện tử.

## Thành viên

| Tên | Vai trò |
|---|---|
| Liêu Văn Đạt | Orchestration & Tích hợp hệ thống |
| Phan Hữu Đức | Ingestion & Data Source |
| Nguyễn Thanh Bình | Transformation (dbt) |
| Nguyễn Hoàng Hải | Data Observability |

## Cấu trúc thư mục

```
.
├── ingestion/        # Đức — generator, extract
├── dbt/              # Bình — staging, marts
├── observability/    # Hải — module DQ, Great Expectations
├── orchestration/    # Đạt — Kestra flows
├── docs/             # Sơ đồ kiến trúc, báo cáo
├── secrets/          # KHÔNG commit — key BigQuery (đã .gitignore)
└── docker-compose.yaml
```

## Chạy hạ tầng

```bash
docker compose up -d
```
