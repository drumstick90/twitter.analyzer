"""In-memory ring buffer for Intelligence UI (concept map + Q&A)."""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from typing import Any

_lock = threading.Lock()
_seq = 0
_buf: deque[dict[str, Any]] = deque(maxlen=400)


def log(dataset: str, message: str) -> None:
    """Append one line. `dataset` is the folder name or \"_\" for global."""
    global _seq
    with _lock:
        _seq += 1
        _buf.append({
            "seq": _seq,
            "ts": datetime.now().strftime("%H:%M:%S"),
            "dataset": dataset,
            "msg": message,
        })


def fetch_since(since_seq: int, dataset: str | None = None) -> tuple[list[dict[str, Any]], int]:
    """
    Return entries with seq > since_seq, optionally filtered to one dataset.
    """
    with _lock:
        out = []
        for e in _buf:
            if e["seq"] <= since_seq:
                continue
            if dataset and e["dataset"] != dataset:
                continue
            out.append(e)
        return out, _seq
