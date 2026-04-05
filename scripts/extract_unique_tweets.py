#!/usr/bin/env python3.11
"""Merge tweet JSON page files and deduplicate by tweet id."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def tweets_from_payload(data: object) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("tweets", "data", "results"):
            v = data.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def parse_created_at(s: str | None) -> datetime:
    if not s:
        return datetime.min
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return datetime.min


def main() -> None:
    p = argparse.ArgumentParser(description="Extract unique tweets from scraped JSON pages.")
    p.add_argument(
        "dataset_dir",
        type=Path,
        help="Folder containing tweets_*.json page files",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file (default: <dataset_dir>/unique_tweets.json)",
    )
    args = p.parse_args()
    dataset_dir = args.dataset_dir.resolve()
    out_path = args.output or (dataset_dir / "unique_tweets.json")

    files = sorted(dataset_dir.glob("*.json"))
    files = [f for f in files if f.name != out_path.name]

    seen: dict[str, dict] = {}
    order: list[str] = []
    total_rows = 0

    for fp in files:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        batch = tweets_from_payload(data)
        total_rows += len(batch)
        for t in batch:
            tid = t.get("id")
            if tid is None:
                continue
            sid = str(tid)
            if sid not in seen:
                seen[sid] = t
                order.append(sid)

    unique = [seen[i] for i in order]
    unique.sort(key=lambda t: parse_created_at(t.get("createdAt")), reverse=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"Files: {len(files)}")
    print(f"Total tweet rows read: {total_rows:,}")
    print(f"Unique tweets: {len(unique):,}")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
