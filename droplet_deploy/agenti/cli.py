#!/usr/bin/env python3
"""
CLI for Market Signal Extraction System.

Usage:
  python -m agenti.cli run --dataset ../datasets/24h_accrued [--commentators 3] [--output out/plan.json]
  python -m agenti.cli extract --dataset ../datasets/24h_accrued --handle clkleinmonaco [--output out/extract.json]
  python -m agenti.cli orchestrate --extractions out/extract_*.json [--output out/plan.json]
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agenti.loader import load_posts_by_commentator, get_scrape_date
from agenti.extraction import extract_signals
from agenti.orchestrator import orchestrate


def _log(msg: str, verbose: bool):
    if verbose:
        print(f"  [verbose] {msg}")


def cmd_run(args):
    """Full pipeline: load → extract (×N) → orchestrate → output."""
    dataset = Path(args.dataset).resolve()
    if not dataset.exists():
        print(f"Error: dataset dir not found: {dataset}", file=sys.stderr)
        sys.exit(1)

    verbose = getattr(args, "verbose", False)
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")

    commentators_limit = args.commentators or 5
    posts = load_posts_by_commentator(str(dataset), max_commentators=commentators_limit)

    if not posts:
        print("Error: no posts loaded. Check dataset path and file pattern.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(posts)} commentators: {list(posts.keys())}")
    for handle, raw in posts.items():
        _log(f"@{handle}: {len(raw)} chars, ~{raw.count('---') + 1} posts", verbose)

    # Extraction phase
    extractions = []
    for handle, raw in posts.items():
        print(f"  Extracting @{handle}...")
        try:
            t0 = time.perf_counter()
            report = extract_signals(handle, raw)
            elapsed = time.perf_counter() - t0
            _log(f"@{handle} extraction done in {elapsed:.1f}s", verbose)
            extractions.append(report)
            if args.save_extractions:
                out_dir = Path(args.output).parent if args.output else Path("agenti/output")
                out_dir.mkdir(parents=True, exist_ok=True)
                ext_path = out_dir / f"extract_{handle}.json"
                with open(ext_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2)
                print(f"    Saved {ext_path}")
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)
            if not args.continue_on_error:
                raise

    # Orchestrate
    print("Orchestrating...")
    t0 = time.perf_counter()
    plan = orchestrate(extractions)
    _log(f"Orchestration done in {time.perf_counter() - t0:.1f}s", verbose)

    out_path = Path(args.output or "agenti/output/positioning_plan.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"\nDone. Positioning plan: {out_path}")
    if "daily_briefing" in plan:
        print("\n--- Daily Briefing ---")
        print(plan["daily_briefing"])


def cmd_extract(args):
    """Extract only — single commentator."""
    dataset = Path(args.dataset).resolve()
    if not dataset.exists():
        print(f"Error: dataset dir not found: {dataset}", file=sys.stderr)
        sys.exit(1)

    posts = load_posts_by_commentator(str(dataset), max_commentators=None)
    handle = args.handle.lstrip("@")

    if handle not in posts:
        print(f"Error: commentator @{handle} not found. Available: {list(posts.keys())}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting @{handle}...")
    report = extract_signals(handle, posts[handle])

    out_path = Path(args.output or f"agenti/output/extract_{handle}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Saved: {out_path}")


def cmd_orchestrate(args):
    """Orchestrate only — from existing extraction JSON files."""
    extraction_paths = []
    for p in args.extractions:
        path = Path(p)
        if path.is_dir():
            extraction_paths.extend(path.glob("extract_*.json"))
        else:
            extraction_paths.append(path)

    if not extraction_paths:
        print("Error: no extraction files found.", file=sys.stderr)
        sys.exit(1)

    reports = []
    for p in sorted(extraction_paths):
        with open(p, "r", encoding="utf-8") as f:
            reports.append(json.load(f))
    print(f"Loaded {len(reports)} extraction reports")

    plan = orchestrate(reports)

    out_path = Path(args.output or "agenti/output/positioning_plan.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"Saved: {out_path}")
    if "daily_briefing" in plan:
        print("\n--- Daily Briefing ---")
        print(plan["daily_briefing"])


def main():
    parser = argparse.ArgumentParser(description="Market Signal Extraction System — CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Full pipeline: load → extract → orchestrate")
    p_run.add_argument("--dataset", "-d", required=True, help="Path to 24h_accrued dataset")
    p_run.add_argument("--commentators", "-n", type=int, default=5, help="Max commentators (default 5)")
    p_run.add_argument("--output", "-o", help="Output path for positioning plan")
    p_run.add_argument("--save-extractions", action="store_true", help="Save per-commentator extraction JSONs")
    p_run.add_argument("--continue-on-error", action="store_true", help="Skip failed extractions")
    p_run.add_argument("--verbose", "-v", action="store_true", help="Verbose logs (timings, sizes, debug)")
    p_run.set_defaults(func=cmd_run)

    # extract
    p_ext = sub.add_parser("extract", help="Extract signals for one commentator")
    p_ext.add_argument("--dataset", "-d", required=True, help="Path to dataset")
    p_ext.add_argument("--handle", "-H", required=True, help="Commentator handle (e.g. clkleinmonaco)")
    p_ext.add_argument("--output", "-o", help="Output JSON path")
    p_ext.set_defaults(func=cmd_extract)

    # orchestrate
    p_orch = sub.add_parser("orchestrate", help="Orchestrate from extraction JSONs")
    p_orch.add_argument("--extractions", "-e", nargs="+", required=True, help="Extraction JSON paths or dir")
    p_orch.add_argument("--output", "-o", help="Output path for positioning plan")
    p_orch.set_defaults(func=cmd_orchestrate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
