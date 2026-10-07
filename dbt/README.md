# dbt — Transformation

Phụ trách: Nguyễn Thanh Bình

- `models/staging/` — làm sạch dữ liệu thô (1 bảng raw <-> 1 model staging).
- `models/marts/` — star schema.
- `tests/` — dbt tests tuỳ chỉnh ngoài schema.yml.
- `macros/` — SQL macro dùng chung giữa nhiều model.

Lưu ý: project dbt thật sự (dbt_project.yml, profiles.yml...) sẽ được
khởi tạo bằng lệnh `dbt init` chạy ngay trong thư mục này.
