"""
Claude Code hook: blocks reading or editing .env secrets files.

A PreToolUse hook for the Read/Edit/Write/MultiEdit tools. If the tool's
target path is a ".env" (or ".env.<suffix>") file -- other than the safe
".env.example" template -- the tool call is blocked.

Exit code 2 is the Claude Code convention for "block this tool call and
show the agent the stderr message as the reason". Exit code 0 means
"allow the tool call to proceed".
"""

import json
import os
import re
import sys

__author__ = "boltelvee"
__version__ = "1.0.0"

SECRETS_FILENAME_PATTERN = re.compile(r"^\.env(\..+)?$")
ALLOWED_SECRETS_FILENAME = ".env.example"
BLOCK_EXIT_CODE = 2
ALLOW_EXIT_CODE = 0


def read_event_from_stdin() -> dict | None:
    """
    Read and parse the hook event JSON from stdin.

    Returns None if stdin is empty or contains invalid JSON, signalling
    that the hook should exit without taking any action.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_target_path(event: dict) -> str:
    """
    Extract the file path the tool call is targeting.

    Checks "file_path" (Read/Edit/Write/MultiEdit) and falls back to
    "notebook_path" (NotebookEdit). Normalizes backslashes so the
    filename check below works the same on Windows-style paths.
    """
    tool_input = event.get("tool_input", {})
    raw_path = tool_input.get("file_path") or tool_input.get("notebook_path", "")
    return str(raw_path).replace("\\", "/")


def is_protected_secrets_file(path: str) -> bool:
    """
    True if `path` points to a .env secrets file that must be blocked.

    ".env.example" is explicitly allowed since it's a template with no
    real secrets in it.
    """
    filename = os.path.basename(path)
    if filename == ALLOWED_SECRETS_FILENAME:
        return False
    return bool(SECRETS_FILENAME_PATTERN.match(filename))


def describe_attempted_action(tool_name: str) -> str:
    """
    Return a human-readable verb describing what the agent tried to do.
    """
    return "read" if tool_name == "Read" else "edit"


def block_tool_call(path: str, tool_name: str) -> None:
    """
    Write the block reason to stderr and exit with the "blocked" code.
    """
    verb = describe_attempted_action(tool_name)
    sys.stderr.write(
        f"Blocked by hook: {path} is a secrets file; the agent must not {verb} it. "
        "Use .env.example instead and ask the quote to update .env manually.\n"
    )
    sys.exit(BLOCK_EXIT_CODE)


def main() -> None:
    event = read_event_from_stdin()
    if event is None:
        sys.exit(ALLOW_EXIT_CODE)

    path = extract_target_path(event)

    if is_protected_secrets_file(path):
        block_tool_call(path, event.get("tool_name", ""))

    sys.exit(ALLOW_EXIT_CODE)


if __name__ == "__main__":
    main()
