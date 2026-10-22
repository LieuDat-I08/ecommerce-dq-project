#!/usr/bin/env python3
"""Extract bộ dữ liệu Olist (Kaggle) từ CSV -> DataFrame chuẩn hoá -> CSV sạch.

Chạy độc lập (không cần Kestra):
    python ingestion/extract_olist.py --input-dir data/olist --output-dir data/extracted

Chuẩn hoá ở mức "raw" (giữ nguyên cấu trúc gốc, biến đổi tối thiểu):
  - tên cột: strip + lowercase (giữ nguyên tên gốc, kể cả lỗi chính tả của Olist như product_name_lenght)
  - cột chuỗi: strip khoảng trắng thừa, chuỗi rỗng -> NaN
  - cột thời gian: ép về datetime (đếm và cảnh báo số giá trị không parse được)
Exit code: 0 = thành công, 1 = lỗi (thiếu file, đọc file lỗi...).
"""
import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from common import append_run_log, setup_logging

log = logging.getLogger("extract_olist")

# tên bảng (dùng trong dự án) -> tên file CSV gốc trên Kaggle
OLIST_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}


def extract_table(name: str, path: Path) -> pd.DataFrame:
    """Đọc 1 file CSV Olist và chuẩn hoá nhẹ."""
    df = pd.read_csv(path, dtype=str, encoding="utf-8")  # đọc toàn bộ dạng str để không mất dữ liệu gốc
    df.columns = [c.strip().lower() for c in df.columns]

    for col in df.columns:
        df[col] = df[col].str.strip().replace("", pd.NA)

    for col in DATE_COLUMNS.get(name, []):
        if col not in df.columns:
            log.warning("[%s] thiếu cột thời gian dự kiến: %s", name, col)
            continue
        before_null = df[col].isna().sum()
        df[col] = pd.to_datetime(df[col], errors="coerce")
        bad = int(df[col].isna().sum() - before_null)
        if bad > 0:
            log.warning("[%s] %d giá trị ở cột %s không parse được thành datetime", name, bad, col)

    # các cột số: ép kiểu số, giá trị không hợp lệ -> NaN (và cảnh báo)
    for col in df.columns:
        if col.endswith(("_qty", "_g", "_cm", "_lenght", "_value", "_installments", "_sequential")) \
                or col in {"price", "freight_value", "review_score", "order_item_id"}:
            before_null = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            bad = int(df[col].isna().sum() - before_null)
            if bad > 0:
                log.warning("[%s] %d giá trị ở cột %s không phải số", name, bad, col)
    return df


def extract_all(input_dir: Path, tables: list[str]) -> dict[str, pd.DataFrame]:
    missing = [OLIST_FILES[t] for t in tables if not (input_dir / OLIST_FILES[t]).exists()]
    if missing:
        raise FileNotFoundError(f"Thiếu file trong {input_dir}: {', '.join(missing)}")

    result = {}
    for name in tables:
        t0 = time.perf_counter()
        df = extract_table(name, input_dir / OLIST_FILES[name])
        log.info("[%s] %d dòng, %d cột (%.2fs)", name, len(df), df.shape[1], time.perf_counter() - t0)
        result[name] = df
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract dữ liệu Olist từ CSV")
    parser.add_argument("--input-dir", type=Path, default=Path("data/olist"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/extracted"))
    parser.add_argument("--tables", nargs="+", choices=list(OLIST_FILES), default=list(OLIST_FILES),
                        help="Chỉ extract một số bảng (mặc định: tất cả)")
    parser.add_argument("--log-file", type=Path, default=Path("logs/extract_runs.jsonl"))
    args = parser.parse_args(argv)

    setup_logging()
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    try:
        data = extract_all(args.input_dir, args.tables)
    except Exception as exc:  # noqa: BLE001 - muốn exit code 1 cho mọi lỗi để Kestra nhận biết thất bại
        log.error("Extract thất bại: %s", exc)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    row_counts = {}
    for name, df in data.items():
        df.to_csv(args.output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
        row_counts[name] = len(df)

    duration = round(time.perf_counter() - t0, 2)
    append_run_log(args.log_file, {
        "script": "extract_olist",
        "started_at": started.isoformat(),
        "duration_seconds": duration,
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
    })
    log.info("Xong: %d bảng, %d dòng, %.2fs -> %s", len(row_counts), sum(row_counts.values()), duration, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
