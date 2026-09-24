"""
Claude Code log summary analyzer.

Summarizes LOG_DIR_NAME/LOG_FILE_NAME per tool:
    proposed  = PreToolUse lines ("the agent asked to do X")
    executed  = PostToolUse + PostToolUseFailure lines ("X actually ran")
    blocked   = proposed lines with no matching executed line (same id)
                — denied by a hook, a rule or the human
    failed    = executed lines with a non-zero exit

Usage:
    python .agent-scripts/agent_log_summary.py [LOG_FILE_NAME]
"""

__author__ = "boltelvee"
__version__ = "1.0.0"

import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field

LOG_DIR_NAME = ".agent-log"
LOG_FILE_NAME = "actions.jsonl"


@dataclass
class ToolStats:
    proposed: int = 0
    executed: int = 0
    blocked: int = 0
    failed: int = 0
    ms: float = 0.0
    files: set[str] = field(default_factory=set)


def resolve_log_path() -> str:
    """
    Resolve the path to the actions.jsonl file from CLI args or default.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.path.join(os.getcwd(), LOG_DIR_NAME, LOG_FILE_NAME)


def load_entries(filepath: str) -> list[dict]:
    """
    Read and parse valid JSON lines from the log file.
    """
    if not os.path.exists(filepath):
        sys.stderr.write(
            f"No log at {filepath}. Are the hooks in .claude/settings.json active? "
            "Run one Edit and check again.\n"
        )
        sys.exit(2)

    entries = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                entries.append(json.loads(line_str))
            except json.JSONDecodeError:
                continue
    return entries


def format_table(rows: list[dict], headers: list[str]) -> str:
    """
    Render a clean CLI table similar to console.table().
    """
    col_widths = {
        h: max(len(h), max((len(str(r.get(h, ""))) for r in rows), default=0))
        for h in headers
    }

    header_line = " │ ".join(f"{h:<{col_widths[h]}}" for h in headers)
    separator = "─┼─".join("─" * col_widths[h] for h in headers)

    lines = [header_line, separator]
    for r in rows:
        row_line = " │ ".join(
            f"{r.get(h, '')!s:<{col_widths[h]}}"
            if h == "tool"
            else f"{r.get(h, '')!s}:>{col_widths[h]}"
            for h in headers
        )
        lines.append(row_line)

    return "\n".join(lines)


def main() -> None:
    filepath = resolve_log_path()
    lines = load_entries(filepath)

    executed_ids = {
        e["id"] for e in lines if e.get("event") != "PreToolUse" and e.get("id")
    }

    by_tool: dict[str, ToolStats] = defaultdict(ToolStats)
    blocked: list[dict] = []
    failed: list[dict] = []

    for e in lines:
        tool_name = e.get("tool", "unknown")
        stats = by_tool[tool_name]

        if e.get("event") == "PreToolUse":
            stats.proposed += 1
            if e.get("id") and e["id"] not in executed_ids:
                stats.blocked += 1
                blocked.append(e)
        else:
            stats.executed += 1
            stats.ms += float(e.get("ms") or 0)
            if e.get("exit") != 0:
                stats.failed += 1
                failed.append(e)

        if e.get("path"):
            stats.files.add(e["path"])

    sorted_tools = sorted(
        by_tool.items(),
        key=lambda item: item[1].proposed + item[1].executed,
        reverse=True,
    )

    rows = [
        {
            "tool": tool,
            "proposed": s.proposed,
            "executed": s.executed,
            "blocked": s.blocked,
            "failed": s.failed,
            "time (s)": round(s.ms / 1000, 1),
            "files": len(s.files),
        }
        for tool, s in sorted_tools
    ]

    sessions = {e["session"] for e in lines if e.get("session")}
    executed_total = sum(1 for e in lines if e.get("event") != "PreToolUse")
    start_ts = lines[0].get("ts", "-") if lines else "-"
    end_ts = lines[-1].get("ts", "-") if lines else "-"

    print(
        f"Agent actions: {executed_total} executed, {len(blocked)} proposed but not executed, "  # noqa: E501
        f"{len(failed)} failed — {len(sessions)} session(s), {start_ts} .. {end_ts}\n"
    )

    headers = ["tool", "proposed", "executed", "blocked", "failed", "time (s)", "files"]
    print(format_table(rows, headers))

    if blocked:
        print("\nProposed but not executed (blocked by a hook, a rule or you):")
        for b in blocked:
            target = b.get("cmd") or b.get("path") or b.get("pattern") or ""
            print(f"  {b.get('ts', '')}  {b.get('tool', '')}  {target}")

    if failed:
        print("\nFailed:")
        for f in failed:
            target = f.get("cmd") or f.get("path") or ""
            print(
                f"  {f.get('ts', '')}  {f.get('tool', '')}  exit={f.get('exit')}  {target}"  # noqa: E501
            )


if __name__ == "__main__":
    main()
