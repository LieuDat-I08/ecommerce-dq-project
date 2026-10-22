"""Tiện ích dùng chung cho các script ingestion (logging + metadata mỗi lần chạy)."""
import json
import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def append_run_log(path: Path, record: dict) -> None:
    """Ghi 1 dòng JSON vào file .jsonl (metadata mỗi lần chạy: số bản ghi, thời gian chạy...)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
