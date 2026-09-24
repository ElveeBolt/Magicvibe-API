"""
Summarize .agent-log/actions.jsonl as compact plain text, readable in a console
and cheap to paste into Claude's context. Most important things come first.

Usage: python report.py [--session last|ID] [--since ISO] [--file PATH] [--width 100]
Exit codes: 0 ok · 2 log not found · 3 bad arguments
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = Path(".agent-log/actions.jsonl")

PRE = "PreToolUse"
POST = {"PostToolUse", "PostToolUseFailure"}
BLOCKED = "Blocked"

RISKY_CMD = re.compile(
    r"(?:^|[\s;&|(])(rm|curl|wget|sudo|chmod|chown|git\s+push|git\s+reset\s+--hard)\b"
)
PIPE = re.compile(r"(?<!\|)\|(?!\|)")
HEREDOC_START = re.compile(r"""\s*"?\$\(cat\s*<<-?\s*['"]?\w+['"]?\s*$""")

WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
ROUTINE_DIRS = {"src", "tests"}
HOME = Path.home()
ROUTINE_OUTSIDE = (HOME / ".claude" / "plans",)
UNSAFE_MODE = "bypassPermissions"


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", help='"last" or a session id (prefix is enough)')
    parser.add_argument("--since", help="only entries at or after this ISO date/time")
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_LOG_PATH, help="path to the log"
    )
    parser.add_argument(
        "--width", type=int, default=100, help="max length of a command (default 100)"
    )
    try:
        return parser.parse_args(argv)
    except SystemExit as e:
        sys.exit(3 if e.code not in (0, None) else 0)


def parse_ts(value):
    """ISO string -> aware UTC datetime, or None."""
    if not value:
        return None
    try:
        val = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError, TypeError:
        return None


def get_entry_path(entry):
    """Extract path or notebook_path from entry."""
    return entry.get("path") or entry.get("notebook_path")


def load_entries(file_path: Path, since):
    """Read the JSONL log, returning (entries, invalid_line_count)."""
    entries, invalid = [], 0
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                entry = json.loads(line_str)
            except json.JSONDecodeError:
                invalid += 1
                continue
            if not isinstance(entry, dict):
                invalid += 1
                continue

            entry["_dt"] = parse_ts(entry.get("ts"))
            # Якщо задано --since, відкидаємо записи до цієї дати або без дати
            if since and (not entry["_dt"] or entry["_dt"] < since):
                continue
            entries.append(entry)
    return entries, invalid


def filter_session(entries, session):
    if not session:
        return entries
    if session == "last":
        for e in reversed(entries):
            if e.get("session"):
                session = e["session"]
                break
        else:
            return []
    return [e for e in entries if str(e.get("session") or "").startswith(session)]


# ---------- classification ----------


def is_failed(entry):
    return (
        entry.get("event") == "PostToolUseFailure"
        or entry.get("is_error") is True
        or entry.get("exit") not in (None, 0)
    )


def resolve_project_root(file_path: Path) -> Path:
    """Detect repo root if .agent-log is present, else fall back to file's parent or cwd."""
    resolved = file_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".agent-log":
            return parent.parent
    return Path.cwd()


def display_path(path_str: str, root: Path) -> str:
    """Project-relative when inside the project, ~/... when in the home dir."""
    try:
        p = (root / path_str).resolve()
        if p.is_relative_to(root):
            return str(p.relative_to(root))
        if p.is_relative_to(HOME):
            return f"~{os.sep}{p.relative_to(HOME)}"
        return str(p)
    except ValueError, RuntimeError:
        return path_str


def write_needs_review(path_str: str, root: Path) -> bool:
    try:
        full = (root / path_str).resolve()
        if any(full.is_relative_to(d) for d in ROUTINE_OUTSIDE):
            return False
        if not full.is_relative_to(root):
            return True
        rel = full.relative_to(root)
        parts = rel.parts
        return not parts or parts[0] not in ROUTINE_DIRS
    except ValueError, RuntimeError:
        return True


def one_line(text, width):
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if not lines:
        return ""
    s = lines[0]
    if len(lines) > 1 and HEREDOC_START.search(s):
        s = HEREDOC_START.sub("", s) + f' "{lines[1]}"'
    elif len(lines) > 1:
        s += " …"
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= width else s[: width - 1] + "…"


def describe(entry, root: Path):
    for key in ("cmd", "pattern", "url", "arg"):
        if entry.get(key):
            return str(entry[key])
    p = get_entry_path(entry)
    return display_path(p, root) if p else ""


def call_key(entry, root: Path):
    """Accurately distinguishes tool calls (Bash cmd, Grep pattern, Write path, etc.)."""
    return entry.get("tool"), one_line(describe(entry, root), 300)


# ---------- aggregation ----------


def summarize(entries, file_path: Path, invalid):
    root = resolve_project_root(file_path)

    post_idx = [i for i, e in enumerate(entries) if e.get("event") in POST]
    executed_ids = {entries[i].get("id") for i in post_idx} - {None}
    block_reasons = {
        e["id"]: e.get("reason")
        for e in entries
        if e.get("event") == BLOCKED and e.get("id")
    }
    last_executed = post_idx[-1] if post_idx else -1

    tools = defaultdict(lambda: {"calls": 0, "failed": 0, "blocked": 0, "ms": 0})
    sessions = {}
    blocked, pending, failures, sensitive = [], [], [], []
    writes = defaultdict(Counter)
    files, days = set(), Counter()
    last_ok = {}
    unsafe = 0
    has_ms = False

    for i, e in enumerate(entries):
        tool = e.get("tool", "unknown")
        event = e.get("event")
        p = get_entry_path(e)
        if p:
            files.add(display_path(p, root))

        if event == PRE:
            call_id = e.get("id")
            if call_id and call_id not in executed_ids:
                if call_id in block_reasons or i <= last_executed:
                    e["_reason"] = block_reasons.get(call_id)
                    blocked.append(e)
                    tools[tool]["blocked"] += 1
                else:
                    pending.append(e)
            continue

        if event not in POST:
            continue

        tools[tool]["calls"] += 1
        if isinstance(e.get("ms"), (int, float)):
            tools[tool]["ms"] += e["ms"]
            has_ms = True
        if e["_dt"]:
            days[e["_dt"].strftime("%m-%d")] += 1

        sess = sessions.setdefault(
            e.get("session") or "(no id)",
            {
                "first": e["_dt"],
                "last": e["_dt"],
                "calls": 0,
                "failed": 0,
                "modes": Counter(),
            },
        )
        sess["calls"] += 1
        sess["last"] = e["_dt"] or sess["last"]
        if e.get("mode"):
            sess["modes"][e["mode"]] += 1
        if e.get("mode") == UNSAFE_MODE:
            unsafe += 1

        ck = call_key(e, root)
        if is_failed(e):
            tools[tool]["failed"] += 1
            sess["failed"] += 1
            failures.append((i, e))
        else:
            last_ok[ck] = i

        if tool == "Bash" and RISKY_CMD.search(e.get("cmd") or ""):
            sensitive.append(e)
        if tool in WRITE_TOOLS and p and write_needs_review(p, root):
            writes[display_path(p, root)][tool] += 1

    stamps = [e["_dt"] for e in entries if e["_dt"]]

    # Визначаємо відносний шлях для заголовка звіту
    rel_file = file_path
    try:
        rel_file = file_path.resolve().relative_to(root)
    except ValueError:
        pass

    return {
        "file": str(rel_file),
        "root": root,
        "first": min(stamps) if stamps else None,
        "last": max(stamps) if stamps else None,
        "days": days,
        "executed": len(post_idx),
        "invalid": invalid,
        "tools": tools,
        "has_ms": has_ms,
        "sessions": sessions,
        "unsafe": unsafe,
        "sensitive": sensitive,
        "writes": writes,
        "unfixed": [e for i, e in failures if last_ok.get(call_key(e, root), -1) <= i],
        "fixed": [e for i, e in failures if last_ok.get(call_key(e, root), -1) > i],
        "blocked": blocked,
        "pending": pending,
        "files": files,
    }


# ---------- rendering ----------


def fmt_dt(dt):
    return dt.strftime("%m-%d %H:%M") if dt else "--"


def fmt_ms(ms):
    return f"{ms / 1000:.0f}s" if ms < 60_000 else f"{ms / 60_000:.1f}m"


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def entry_line(e, root, width, prefix=""):
    what = one_line(describe(e, root), width) or "(no details logged)"
    return f"  {fmt_dt(e['_dt'])}  {e.get('tool', 'unknown')}  {prefix}{what}"


def exit_label(e):
    return f"exit={e['exit']}  " if e.get("exit") not in (None, 0) else "failed  "


def render(s, width):
    out = []
    add = out.append
    root = s["root"]

    add(f"Agent log {s['file']} · {fmt_dt(s['first'])} → {fmt_dt(s['last'])} UTC")
    if s["days"]:
        add(
            "Activity: " + " · ".join(f"{d} ×{n}" for d, n in sorted(s["days"].items()))
        )

    failed = len(s["fixed"]) + len(s["unfixed"])
    add(
        f"Calls: {s['executed']} executed · {failed} failed ({len(s['fixed'])} fixed later)"
        f" · {len(s['blocked'])} blocked · {len(s['pending'])} running"
        f" · {s['invalid']} bad lines"
    )

    concerns = [
        plural(n, word)
        for n, word in [
            (len(s["sensitive"]), "sensitive command"),
            (len(s["unfixed"]), "unresolved failure"),
            (
                len(s["writes"]),
                f"write target outside {'/'.join(sorted(ROUTINE_DIRS))}",
            ),
            (len(s["blocked"]), "blocked call"),
            (s["unsafe"], f"call in {UNSAFE_MODE} mode"),
        ]
        if n
    ]
    add(">> Review: " + ", ".join(concerns) if concerns else ">> Nothing needs review.")

    if s["sensitive"]:
        add(f"\nRISKY COMMANDS ({len(s['sensitive'])})")
        for e in s["sensitive"]:
            cmd = e.get("cmd") or ""
            masked = PIPE.search(cmd) and "pipefail" not in cmd
            add(
                entry_line(e, root, width)
                + ("  [exit code masked by pipe]" if masked else "")
            )

    if s["unfixed"]:
        add(f"\nFAILED, NOT FIXED LATER ({len(s['unfixed'])})")
        for e in s["unfixed"]:
            add(entry_line(e, root, width, exit_label(e)))

    if s["writes"]:
        dirs_str = " ".join(f"{d}/" for d in sorted(ROUTINE_DIRS))
        add(f"\nWRITES OUTSIDE {dirs_str} ({len(s['writes'])})")
        for path_str, by_tool in sorted(s["writes"].items()):
            add(
                f"  {path_str}  "
                + " ".join(f"{t}×{n}" for t, n in by_tool.most_common())
            )

    if s["blocked"]:
        add(f"\nBLOCKED by a hook, rule or the human ({len(s['blocked'])})")
        for e in s["blocked"]:
            reason = f"  [{e['_reason']}]" if e.get("_reason") else ""
            add(entry_line(e, root, width) + reason)

    if s["fixed"]:
        add(f"\nFAILED, THEN SUCCEEDED ON RETRY ({len(s['fixed'])})")
        for e in s["fixed"]:
            add(entry_line(e, root, width, exit_label(e)))

    if s["sessions"]:
        add(f"\nSESSIONS ({len(s['sessions'])})")
        for sid, x in sorted(
            s["sessions"].items(),
            key=lambda kv: kv[1]["first"] or datetime.min.replace(tzinfo=timezone.utc),
        ):
            modes = ", ".join(m for m, _ in x["modes"].most_common())
            add(
                f"  {sid}  {fmt_dt(x['first'])} → {fmt_dt(x['last'])}"
                f"  {x['calls']} calls · {x['failed']} failed"
                + (f" · {modes}" if modes else "")
            )

    if s["tools"]:
        rows = sorted(
            s["tools"].items(),
            key=lambda kv: kv[1]["calls"] + kv[1]["blocked"],
            reverse=True,
        )
        w = max(len(name) for name, _ in rows)
        add(
            f"\n  {'TOOL':<{w}}  calls  failed  blocked"
            + ("   time" if s["has_ms"] else "")
        )
        for name, st in rows:
            time = f"  {fmt_ms(st['ms']):>5}" if s["has_ms"] else ""
            add(
                f"  {name:<{w}}  {st['calls']:>5}  {st['failed']:>6}  {st['blocked']:>7}{time}"
            )

    if s["files"]:
        add(f"\nFILES TOUCHED ({len(s['files'])})")
        by_dir = defaultdict(list)
        for path_str in sorted(s["files"]):
            folder, name = os.path.split(path_str)
            by_dir[folder].append(name)
        for folder, names in by_dir.items():
            add(f"  {folder + '/' if folder else './'}  {' '.join(names)}")

    return "\n".join(out)


def main():
    args = parse_args(sys.argv[1:])

    since = None
    if args.since:
        since = parse_ts(args.since)
        if since is None:
            print(
                f"Error: --since must be an ISO date/time, got {args.since!r}",
                file=sys.stderr,
            )
            sys.exit(3)

    if not args.file.exists():
        print(
            f"Error: log not found at {args.file.resolve()}. "
            f"Are the hooks in .claude/settings.json active?",
            file=sys.stderr,
        )
        sys.exit(2)

    entries, invalid = load_entries(args.file, since)
    entries = filter_session(entries, args.session)
    if not entries:
        print("No log entries match the given filters.")
        return
    print(render(summarize(entries, args.file, invalid), args.width))


if __name__ == "__main__":
    main()
