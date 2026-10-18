#!/usr/bin/env python3
"""Read-only AI-agent token usage scanner.

Scans a Codex-style environment (config, model catalog, thread history,
archived rollouts) and prints a redacted, structured usage report plus
ranked fix suggestions. Never writes anything and never prints secrets.

Usage:
  python3 scan_usage.py [--codex-home ~/.codex]
  python3 scan_usage.py --codex-home /path/to/.codex --rollout-dir /path/rollouts
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

SECRET_KEY = re.compile(r"(api[_-]?key|secret|password|token|authorization|bearer)", re.I)
SK_TOKEN = re.compile(r"sk-[A-Za-z0-9_\-]+")


def redact(value: str) -> str:
    if not isinstance(value, str):
        return value
    value = SK_TOKEN.sub("<redacted>", value)
    return "<redacted>" if SECRET_KEY.search(value) else value


def read_json(path: Path):
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def scan_config(path: Path) -> dict:
    """Line-based, secret-safe scan of a Codex config.toml."""
    out: dict = {"path": str(path), "model": None, "reasoning_effort": None,
                 "plugins": 0, "mcp_servers": 0, "sections": []}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("[plugins") or re.match(r'^\[plugins\.', line):
            out["plugins"] += 1
        if line.startswith("[mcp_servers") or re.match(r'^\[mcp_servers\.', line):
            out["mcp_servers"] += 1
        if line.startswith("["):
            out["sections"].append(line)
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key == "model":
            out["model"] = val
        elif key == "model_reasoning_effort":
            out["reasoning_effort"] = val
        elif key == "model_provider":
            out.setdefault("model_provider", val)
    return out


def scan_models(path: Path) -> list:
    data = read_json(path) or {}
    models = data.get("models") or []
    out = []
    for m in models:
        if not isinstance(m, dict):
            continue
        out.append({
            "slug": m.get("slug"),
            "context_window": m.get("context_window"),
            "default_reasoning_level": m.get("default_reasoning_level"),
            "input_modalities": m.get("input_modalities"),
        })
    return out


def scan_threads(db_path: Path, limit: int = 10) -> dict:
    if not db_path.exists():
        return {"path": str(db_path), "error": "not found"}
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        cur = con.cursor()
        cur.execute(
            "SELECT thread_id, COUNT(*) FROM thread_turns "
            "GROUP BY thread_id ORDER BY 2 DESC LIMIT ?", (limit,)
        )
        top = [[r[0], r[1]] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*) FROM thread_turns")
        total = cur.fetchone()[0]
        con.close()
        return {"path": str(db_path), "total_turns": total, "top_threads": top}
    except Exception as exc:
        return {"path": str(db_path), "error": exc.__class__.__name__}


def iter_usage(obj):
    if isinstance(obj, dict):
        if "input_tokens" in obj and "total_tokens" in obj:
            yield obj
        for v in obj.values():
            yield from iter_usage(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_usage(v)


def scan_rollouts(rollout_dir: Path, context_window: int = 1_048_576) -> dict:
    files = sorted(rollout_dir.glob("*.jsonl")) if rollout_dir.exists() else []
    sessions = []
    # Per-request counters (total_tokens within the context window).
    req_count = req_input = req_output = req_cached = 0
    req_totals: list[int] = []
    # Session-level peaks (may be cumulative counters, not single requests).
    session_peaks: list[int] = []
    for path in files:
        peak_total = 0
        peak_input = 0
        records = 0
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            for u in iter_usage(obj):
                records += 1
                total = int(u.get("total_tokens") or 0)
                inp = int(u.get("input_tokens") or 0)
                peak_total = max(peak_total, total)
                peak_input = max(peak_input, inp)
                if total <= context_window:
                    req_count += 1
                    req_input += inp
                    req_output += int(u.get("output_tokens") or 0)
                    req_cached += int(u.get("cached_input_tokens") or 0)
                    req_totals.append(total)
        if records:
            sessions.append({
                "file": path.name, "usage_records": records,
                "peak_total": peak_total, "peak_input": peak_input,
            })
            session_peaks.append(peak_total)
    session_peaks.sort()
    req_totals.sort()

    def _pct(vals: list, p: float) -> int:
        return vals[min(len(vals) - 1, int(len(vals) * p))] if vals else 0

    cached_ratio = (req_cached / req_input) if req_input else 0.0
    return {
        "rollout_files": len(files),
        "request_records": req_count,
        "request_input_tokens": req_input,
        "request_output_tokens": req_output,
        "cached_ratio": round(cached_ratio, 3),
        "request_total_min": req_totals[0] if req_totals else 0,
        "request_total_median": _pct(req_totals, 0.5),
        "request_total_p90": _pct(req_totals, 0.9),
        "request_total_max": req_totals[-1] if req_totals else 0,
        "session_peak_median": _pct(session_peaks, 0.5),
        "session_peak_max": session_peaks[-1] if session_peaks else 0,
        "has_cumulative_counters": any(p > context_window for p in session_peaks),
        "sessions": sessions[:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only AI-agent usage scanner")
    ap.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    ap.add_argument("--thread-db", default=None)
    ap.add_argument("--rollout-dir", default=None)
    args = ap.parse_args()

    home = Path(args.codex_home).expanduser()
    config_path = home / "config.toml"
    models_path = home / "models.json"
    thread_db = Path(args.thread_db) if args.thread_db else home / "thread_history_1.sqlite"
    rollout_dir = Path(args.rollout_dir) if args.rollout_dir else home / "archived_sessions"

    config = scan_config(config_path)
    models = scan_models(models_path)
    windows = [m.get("context_window") or 0 for m in models if isinstance(m, dict)]
    context_window = max(windows) if windows else 1_048_576
    threads = scan_threads(thread_db)
    rollouts = scan_rollouts(rollout_dir, context_window)

    print("=== AI Token Usage Scan (read-only, secrets redacted) ===")
    print(f"codex_home: {home}")
    print()
    print("[model config]")
    print(f"  default model: {redact(str(config.get('model')))}")
    print(f"  reasoning effort: {redact(str(config.get('reasoning_effort')))}")
    print(f"  model provider: {redact(str(config.get('model_provider')))}")
    print(f"  plugins enabled: {config.get('plugins')} | mcp servers: {config.get('mcp_servers')}")
    if not models:
        print("  catalog: (no model catalog found)")
    for m in models:
        print(f"  catalog: {m['slug']} window={m['context_window']} "
              f"default_effort={m['default_reasoning_level']} modalities={m['input_modalities']}")
    print()
    print("[thread history]")
    if "error" in threads:
        print(f"  {threads['error']}")
    else:
        print(f"  total turns: {threads['total_turns']}")
        for tid, n in threads["top_threads"]:
            print(f"  {n:>5} turns  {tid}")
    print()
    print("[rollout usage]")
    print(f"  files scanned: {rollouts['rollout_files']}")
    print(f"  per-request records: {rollouts['request_records']}")
    print(f"  per-request input tokens: {rollouts['request_input_tokens']:,}")
    print(f"  per-request output tokens: {rollouts['request_output_tokens']:,}")
    print(f"  per-request cached ratio: {rollouts['cached_ratio']}")
    print(f"  per-request total tokens: min={rollouts['request_total_min']:,} "
          f"median={rollouts['request_total_median']:,} "
          f"p90={rollouts['request_total_p90']:,} max={rollouts['request_total_max']:,}")
    print(f"  session cumulative peak: median={rollouts['session_peak_median']:,} "
          f"max={rollouts['session_peak_max']:,}")
    if rollouts["has_cumulative_counters"]:
        print("  note: session peaks above the context window are cumulative "
              "session counters, not single requests.")
    for s in rollouts["sessions"]:
        print(f"  {s['file']}: records={s['usage_records']} "
              f"peak_total={s['peak_total']:,} peak_input={s['peak_input']:,}")

    print()
    print("[fix suggestions - ranked]")
    model = str(config.get("model") or "").lower()
    if any(x in model for x in ("pro", "max", "premium", "ultra")):
        print("1. default model looks top-tier -> switch to a lighter tier for routine work")
    effort = str(config.get("reasoning_effort") or "").lower()
    if effort in {"high", "xhigh", "ultra", "max"}:
        print("2. reasoning effort high -> lower to 'low'; raise only for hard tasks")
    if context_window >= 1_000_000:
        print("3. context window >= 1M -> set a soft ceiling ~10% and compact/archive early")
    if rollouts["cached_ratio"] > 0.9:
        print("4. cached ratio >90% -> context is re-sent every turn; shorten sessions")
    if config.get("plugins", 0) > 10:
        print("5. many plugins enabled -> disable unused ones to cut per-request schema tax")
    if "error" not in threads and threads.get("total_turns", 0):
        long_threads = [t for t in threads["top_threads"] if t[1] >= 80]
        if long_threads:
            print("6. long-lived threads detected -> archive and start fresh threads")
    if not model and not config.get("reasoning_effort"):
        print("- no config.toml found; run inside a Codex home or pass --codex-home")
    return 0


if __name__ == "__main__":
    sys.exit(main())
