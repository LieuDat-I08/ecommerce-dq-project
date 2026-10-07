# Observability

Phụ trách: Nguyễn Hoàng Hải

- `dq_module/` — module Python tự viết, đo 6 chiều chất lượng dữ liệu,
  ghi kết quả vào dataset `observability` (bảng dq_results) trên BigQuery.
- `great_expectations/` — expectation suites cho các bảng marts quan trọng.
- `tests/` — unit test cho dq_module, dùng ground truth từ Đức.
