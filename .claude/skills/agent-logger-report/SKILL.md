---
name: agent-logger-report
description: Summarizes the agent observability log (.agent-log/actions.jsonl) into a compact text report - what needs review (sensitive commands, unresolved failures, writes outside src/tests, blocked calls, bypassPermissions use), then sessions, tool stats and touched files. Use when the user asks what the agent did, wants a session report or an audit of agent actions, or mentions the agent log or actions.jsonl.
license: MIT
allowed-tools: Bash(uv run --no-project python ${CLAUDE_SKILL_DIR}/scripts/report.py *)
metadata:
  author: boltelvee
  version: "1.0"
---

# Agent logger report

## Workflow

1. Run the bundled script. Never parse the JSONL by hand:

   ```bash
   uv run --no-project python ${CLAUDE_SKILL_DIR}/scripts/report.py --file ${CLAUDE_PROJECT_DIR}/.agent-log/actions.jsonl
   ```

   Add options only when the user asks for them:
    - `--session last` for "this session" or "the last session" (the newest entry is this report's own call, so "last"
      is the current session); `--session <id prefix>` for a specific one.
    - `--since <ISO date or time>` for a time window, e.g. `--since 2026-09-12`.

2. Show the output verbatim in a `text` code block under a `## Agent activity report` heading.
3. Below it, add at most 5 bullets explaining the `>> Review:` line, most severe first:
   sensitive commands, unresolved failures, bypassPermissions use, writes outside src/tests, blocked calls.
   Say what each item likely means and whether it needs action; group repeats.
   Items under "FAILED, THEN SUCCEEDED ON RETRY" were fixed: mention them only if asked.
   If the report says "Nothing needs review.", write one line saying so.
4. Do not modify the log file. Do not run any other command unless the user asks.

## Reading the report

- `[exit code masked by pipe]`: the command succeeded only in the sense that its last pipe stage did; the real result is
  unknown.
- `1 running` is normally this report's own call: its PostToolUse entry is written after the script finishes. Ignore it.
- The logger cuts commands at 200 characters, so a long command may end mid-way.
- A blocked call with a `[reason]` was stopped by a hook; without one it was denied by a permission rule or the human.

## Gotchas

- Exit code 2 means the log is missing: say so and suggest checking the hooks in `.claude/settings.json`. Do not create
  the log.
- Exit code 3 means bad arguments: fix the flag and rerun once.