"""
Claude Code hook: logger.

Reads a hook event (JSON) from stdin and appends a compact JSON line
describing what happened to <project_root>/<LOG_DIR_NAME>/<LOG_FILE_NAME>.

Never fails the hook: any internal error is swallowed and the script
exits with code 0.

Blocking hooks can record why they blocked a call:

    from logger import log_blocked      # works: the hook's own dir is on sys.path
    log_blocked(event, "reads .env")
    sys.exit(2)
"""

__author__ = "boltelvee"
__version__ = "1.0"

import json
import os
import re
import sys
from datetime import UTC, datetime

LOG_DIR_NAME = ".agent-log"
LOG_FILE_NAME = "actions.jsonl"
MAX_COMMAND_LENGTH = 200
MAX_ARG_LENGTH = 100
ARG_KEYS = ("skill", "subagent_type", "query", "description", "plan", "prompt")


def read_event_from_stdin() -> dict:
    """
    Read and parse the hook event JSON from stdin.

    Returns an empty dict if stdin is empty, not valid JSON or not a JSON object.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return event if isinstance(event, dict) else {}


def resolve_project_root(event: dict) -> str:
    """
    Determine the project root directory.

    Priority: CLAUDE_PROJECT_DIR env var -> event's "cwd" -> current dir.
    """
    return os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()


def normalize_path(path: str) -> str:
    """
    Normalize a filesystem path to a comparable form.

    - Converts backslashes to forward slashes.
    - Converts drive letters to a consistent "C:/" style (uppercase),
      handling both "/c/..." (Git Bash style) and "c:/..." forms.
    - Strips a trailing slash.
    """
    normalized = str(path).replace("\\", "/")
    normalized = re.sub(
        r"^/([a-zA-Z])/", lambda m: f"{m.group(1).upper()}:/", normalized
    )
    normalized = re.sub(
        r"^([a-zA-Z]):/", lambda m: f"{m.group(1).upper()}:/", normalized
    )
    return normalized.rstrip("/")


def build_root_prefixes(event: dict, project_root: str) -> list[str]:
    """
    Build the list of normalized root paths (with trailing slash)
    against which absolute paths are matched to produce relative paths.
    """
    candidate_roots = [project_root, event.get("cwd")]
    return [normalize_path(r) + "/" for r in candidate_roots if r]


def make_relative_path_resolver(root_prefixes: list[str]):
    """
    Return a function that converts an absolute path to a path
    relative to one of the known project roots (or the normalized
    absolute path, if none of the roots match).
    """

    def to_relative_path(path: str | None) -> str | None:
        if not path:
            return None
        normalized = normalize_path(path)
        for prefix in root_prefixes:
            if normalized.startswith(prefix):
                return normalized[len(prefix) :]
        return normalized

    return to_relative_path


def extract_exit_status(event: dict):
    """
    Determine the "exit" field value for a PostToolUseFailure event.

    Returns an int exit code if one can be parsed from the error message,
    otherwise "interrupted" or "error".
    """
    error_message = str(event.get("error") or "")
    match = re.search(r"^Exit code (\d+)", error_message)
    if match:
        return int(match.group(1))
    return "interrupted" if event.get("is_interrupt") else "error"


def first_line(value, limit: int) -> str:
    """First non-empty line of a value, cut to `limit` characters."""
    for line in str(value).splitlines():
        if line.strip():
            return line.strip()[:limit]
    return ""


def base_entry(event: dict, event_name: str) -> dict:
    """Fields shared by every log line."""
    return {
        "ts": datetime.now(UTC).isoformat(),
        "event": event_name,
        "id": event.get("tool_use_id"),
        "session": str(event.get("session_id") or "")[:8],
        "mode": event.get("permission_mode"),
        "tool": event.get("tool_name", "unknown"),
    }


def build_log_entry(event: dict, to_relative_path) -> dict:
    """
    Build the dict that will be serialized as one log line.
    """
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    event_name = event.get("hook_event_name", "unknown")
    entry = base_entry(event, event_name)

    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if file_path:
        entry["path"] = to_relative_path(file_path)

    if tool_input.get("command"):
        entry["cmd"] = str(tool_input["command"])[:MAX_COMMAND_LENGTH]

    if tool_input.get("pattern"):
        entry["pattern"] = tool_input["pattern"]

    if tool_input.get("url"):
        entry["url"] = tool_input["url"]

    if not any(key in entry for key in ("path", "cmd", "pattern", "url")):
        for key in ARG_KEYS:
            if tool_input.get(key):
                entry["arg"] = first_line(tool_input[key], MAX_ARG_LENGTH)
                break

    if event_name == "PostToolUse":
        entry["exit"] = 0
    elif event_name == "PostToolUseFailure":
        entry["exit"] = extract_exit_status(event)

    duration_ms = event.get("duration_ms")
    if isinstance(duration_ms, (int, float)):
        entry["ms"] = duration_ms

    return entry


def append_log_entry(project_root: str, entry: dict) -> None:
    """
    Append the entry as one JSON line to the log file.

    Silently does nothing on failure (e.g. no write permission),
    since a logging hook must never break the tool call it observes.
    """
    try:
        log_dir = os.path.join(project_root, LOG_DIR_NAME)
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, LOG_FILE_NAME)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


def log_blocked(event: dict, reason: str) -> None:
    """
    Record that a PreToolUse hook blocked this call, and why.

    Called by blocking hooks right before `sys.exit(2)`. Never raises.
    """
    try:
        entry = base_entry(event, "Blocked")
        entry["reason"] = first_line(reason, MAX_ARG_LENGTH)
        append_log_entry(resolve_project_root(event), entry)
    except Exception:
        pass


def main() -> None:
    try:
        event = read_event_from_stdin()
        if not event.get("hook_event_name"):
            sys.exit(0)
        project_root = resolve_project_root(event)
        root_prefixes = build_root_prefixes(event, project_root)
        to_relative_path = make_relative_path_resolver(root_prefixes)
        append_log_entry(project_root, build_log_entry(event, to_relative_path))
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
