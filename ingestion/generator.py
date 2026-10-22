#!/usr/bin/env python3
"""Data generator: sinh đơn hàng giả lập theo cấu trúc Olist (orders, order_items, order_payments, customers).

Chạy độc lập (không cần Kestra):
    python ingestion/generator.py --date 2026-09-15
    python ingestion/generator.py --date 2026-09-15 --orders 200 --seed 7

Đặc điểm:
  - Mô phỏng hành vi mua sắm: số đơn/ngày theo thứ trong tuần, phân bố theo giờ (đỉnh 10h-22h).
  - Deterministic: cùng (--seed, --date) cho ra cùng dữ liệu -> chạy lại không tạo dữ liệu khác
    (nền tảng cho idempotency ở T10).
  - Dùng khoá tham chiếu (product_id, seller_id, customer_unique_id) từ dữ liệu Olist đã extract
    nếu có; nếu chưa có thì tự sinh bộ tham chiếu giả để vẫn chạy được.
  - Bản đầu: CHƯA có lỗi cố ý (sẽ thêm ở T11, nên phần sinh dữ liệu "sạch" được tách riêng trong build_day()).
Exit code: 0 = thành công, 1 = lỗi.
"""
import argparse
import logging
import math
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from faker import Faker

from common import append_run_log, setup_logging

log = logging.getLogger("generator")

# Phân bố đơn hàng theo giờ (0h..23h): thấp về đêm, cao từ 10h-22h
HOUR_WEIGHTS = [2, 1, 1, 0.5, 0.5, 0.5, 1, 2, 4, 6, 8, 9,
                8, 8, 8, 8, 8, 7, 6, 6, 7, 8, 7, 4]
# Hệ số theo thứ trong tuần (Mon=0 .. Sun=6)
WEEKDAY_FACTOR = [1.15, 1.10, 1.05, 1.00, 0.95, 0.75, 0.80]

STATUS_CHOICES = (["created", "approved", "invoiced", "processing"], [0.05, 0.60, 0.10, 0.25])
PAYMENT_TYPES = (["credit_card", "boleto", "voucher", "debit_card"], [0.74, 0.19, 0.05, 0.02])
ITEMS_PER_ORDER = ([1, 2, 3], [0.88, 0.09, 0.03])
NEW_CUSTOMER_RATE = 0.85  # tỉ lệ khách hàng mới (Olist: đa số khách chỉ mua 1 lần)

TS_FMT = "%Y-%m-%d %H:%M:%S"


def new_id(rng: random.Random) -> str:
    """ID 32 ký tự hex giống Olist, nhưng sinh từ rng nên deterministic."""
    return f"{rng.getrandbits(128):032x}"


def product_price(product_id: str) -> float:
    """Giá cố định theo từng sản phẩm (cùng sản phẩm -> cùng giá ở mọi ngày)."""
    r = random.Random(product_id)
    return round(min(max(r.lognormvariate(4.3, 0.8), 5.0), 2500.0), 2)


def load_reference(ref_dir: Path) -> dict:
    """Lấy danh sách khoá tham chiếu từ dữ liệu Olist đã extract; không có thì sinh bộ giả cố định."""
    files = {k: ref_dir / f"{k}.csv" for k in ("customers", "products", "sellers")}
    if all(p.exists() for p in files.values()):
        customers = pd.read_csv(files["customers"], dtype=str,
                                usecols=["customer_unique_id", "customer_zip_code_prefix",
                                         "customer_city", "customer_state"]).drop_duplicates("customer_unique_id")
        return {
            "source": "olist",
            "customers": customers.to_dict("records"),
            "products": pd.read_csv(files["products"], dtype=str, usecols=["product_id"])["product_id"].tolist(),
            "sellers": pd.read_csv(files["sellers"], dtype=str, usecols=["seller_id"])["seller_id"].tolist(),
        }

    log.warning("Chưa có dữ liệu Olist đã extract trong %s -> dùng bộ tham chiếu giả", ref_dir)
    r = random.Random(0)  # cố định, không phụ thuộc ngày chạy
    fake = Faker("pt_BR")
    fake.seed_instance(0)
    customers = [{
        "customer_unique_id": new_id(r),
        "customer_zip_code_prefix": str(r.randint(1000, 99990)),
        "customer_city": fake.city().lower(),
        "customer_state": fake.estado_sigla(),
    } for _ in range(300)]
    return {
        "source": "synthetic",
        "customers": customers,
        "products": [new_id(r) for _ in range(500)],
        "sellers": [new_id(r) for _ in range(50)],
    }


def expected_orders(day: date, base_orders: int, rng: random.Random) -> int:
    lam = base_orders * WEEKDAY_FACTOR[day.weekday()]
    return max(0, round(rng.gauss(lam, math.sqrt(lam))))  # xấp xỉ Poisson


def build_day(day: date, n_orders: int, seed: int, ref: dict) -> dict[str, pd.DataFrame]:
    """Sinh dữ liệu "sạch" cho 1 ngày. (T11: lỗi cố ý sẽ được áp dụng SAU hàm này, qua flag.)"""
    rng = random.Random(f"{seed}-{day.isoformat()}")
    fake = Faker("pt_BR")
    fake.seed_instance(rng.getrandbits(32))

    hours = rng.choices(range(24), weights=HOUR_WEIGHTS, k=n_orders)
    midnight = datetime.combine(day, datetime.min.time())
    orders, items, payments, customers = [], [], [], []

    for hour in hours:
        purchase = midnight + timedelta(hours=hour, minutes=rng.randint(0, 59), seconds=rng.randint(0, 59))
        order_id, customer_id = new_id(rng), new_id(rng)

        # --- customer ---
        if rng.random() < NEW_CUSTOMER_RATE:
            cust = {
                "customer_unique_id": new_id(rng),
                "customer_zip_code_prefix": str(rng.randint(1000, 99990)),
                "customer_city": fake.city().lower(),
                "customer_state": fake.estado_sigla(),
            }
        else:
            cust = rng.choice(ref["customers"])
        customers.append({"customer_id": customer_id, **cust})

        # --- order ---
        status = rng.choices(*STATUS_CHOICES)[0]
        approved = None if status == "created" else purchase + timedelta(minutes=rng.randint(1, 120))
        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_status": status,
            "order_purchase_timestamp": purchase.strftime(TS_FMT),
            "order_approved_at": approved.strftime(TS_FMT) if approved else None,
            "order_delivered_carrier_date": None,
            "order_delivered_customer_date": None,
            "order_estimated_delivery_date": (purchase + timedelta(days=rng.randint(10, 30))).strftime(TS_FMT),
        })

        # --- order items ---
        total = 0.0
        for item_no in range(1, rng.choices(*ITEMS_PER_ORDER)[0] + 1):
            product_id = rng.choice(ref["products"])
            price = product_price(product_id)
            freight = round(rng.uniform(7, 40), 2)
            total += price + freight
            items.append({
                "order_id": order_id,
                "order_item_id": item_no,
                "product_id": product_id,
                "seller_id": rng.choice(ref["sellers"]),
                "shipping_limit_date": (purchase + timedelta(days=3)).strftime(TS_FMT),
                "price": price,
                "freight_value": freight,
            })

        # --- payment ---
        ptype = rng.choices(*PAYMENT_TYPES)[0]
        installments = rng.choices(range(1, 11), weights=[50, 12, 10, 8, 6, 4, 3, 3, 2, 2])[0] \
            if ptype == "credit_card" else 1
        payments.append({
            "order_id": order_id,
            "payment_sequential": 1,
            "payment_type": ptype,
            "payment_installments": installments,
            "payment_value": round(total, 2),
        })

    orders.sort(key=lambda o: o["order_purchase_timestamp"])
    return {
        "orders": pd.DataFrame(orders),
        "order_items": pd.DataFrame(items),
        "order_payments": pd.DataFrame(payments),
        "customers": pd.DataFrame(customers),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sinh đơn hàng giả lập theo cấu trúc Olist")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(),
                        help="Ngày cần sinh đơn (YYYY-MM-DD), mặc định: hôm nay")
    parser.add_argument("--orders", type=int, default=None, help="Số đơn cố định (bỏ qua mô phỏng theo ngày)")
    parser.add_argument("--base-orders", type=int, default=150, help="Số đơn trung bình/ngày")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ref-dir", type=Path, default=Path("data/extracted"),
                        help="Thư mục dữ liệu Olist đã extract (lấy khoá tham chiếu)")
    parser.add_argument("--output-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--log-file", type=Path, default=Path("logs/generator_runs.jsonl"))
    args = parser.parse_args(argv)

    setup_logging()
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    try:
        if args.orders is not None and args.orders < 0:
            raise ValueError("--orders phải >= 0")
        ref = load_reference(args.ref_dir)
        n_orders = args.orders if args.orders is not None else expected_orders(
            args.date, args.base_orders, random.Random(f"{args.seed}-count-{args.date.isoformat()}"))
        tables = build_day(args.date, n_orders, args.seed, ref)

        out = args.output_dir / f"dt={args.date.isoformat()}"  # chạy lại cùng ngày -> ghi đè, không nhân đôi
        out.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            df.to_csv(out / f"{name}.csv", index=False)
    except Exception as exc:  # noqa: BLE001 - exit code 1 để Kestra nhận biết thất bại
        log.error("Generator thất bại: %s", exc)
        return 1

    duration = round(time.perf_counter() - t0, 2)
    counts = {k: len(v) for k, v in tables.items()}
    append_run_log(args.log_file, {
        "script": "generator",
        "started_at": started.isoformat(),
        "duration_seconds": duration,
        "target_date": args.date.isoformat(),
        "seed": args.seed,
        "reference_source": ref["source"],
        "row_counts": counts,
        "output_dir": str(out),
    })
    log.info("Xong ngày %s: %s (%.2fs) -> %s", args.date, counts, duration, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
