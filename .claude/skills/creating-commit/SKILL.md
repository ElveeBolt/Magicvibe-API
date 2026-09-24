---
name: creating-commits
description: Creates Conventional Commits from the current git changes. Stages one logical change, picks the type from
  the diff and the scope from the project's domain folders or the changed paths, validates the message, and commits. Use
  when the user asks to commit, write or fix a commit message, or save changes to git.
context: fork
agent: general-purpose
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git add *) Bash(git commit *) Bash(cz check *)
  Bash(uv run --no-project python ${CLAUDE_SKILL_DIR}/scripts/find_domain_scopes.py)
argument-hint: "[what to commit, or hints]"
license: MIT
metadata:
  author: boltelvee
  version: "1.0"
---

# Repository state

Status:
!`git status --short`

Staged:
!`git diff --cached --stat`

Recent commits (existing scope conventions):
!`git log --oneline -20`

!`uv run --no-project python ${CLAUDE_SKILL_DIR}/scripts/find_domain_scopes.py`

User request: $ARGUMENTS

# Workflow

Copy this checklist and track your progress:

```
Commit progress:
- [ ] 1. Decide what to commit
- [ ] 2. Inspect the diff
- [ ] 3. Choose type and scope
- [ ] 4. Write the message
- [ ] 5. Validate
- [ ] 6. Commit
- [ ] 7. Report
```

**1. Decide what to commit.**

- If the user request above says what to commit, follow it.
- If files are already staged, commit exactly those. Do not stage or unstage anything: the user chose them.
- If nothing is staged, group the changes into logical commits (one per domain, see Scope) and stage each group by
  explicit path. Never use `git add -A` or `git add .`.
- Never stage secrets (`.env`, keys, credentials) or generated files (build output, caches). List them in the report
  instead.

**2. Inspect the diff.** Run `git diff --cached`. The file paths decide the scope; the content decides the type.

**3. Choose type and scope** using the sections below.

**4. Write the message** following "Message rules".

**5. Validate.** Run `cz check --message "<message>"`. If it fails, fix the message and repeat. If `cz` is not
installed, check the message against "Message rules" yourself.

**6. Commit** with `git commit -m "<header>"`, adding `-m "<body>"` and `-m "<footer>"` when needed.

- A hook reformatted files → re-stage the same files and commit again.
- A hook reports lint or test errors → stop and report them. Do not change code.
- Never use `--no-verify`, `--amend`, or `git push`.

Repeat steps 2–6 for each group from step 1.

**7. Report** each commit's hash and header, plus anything left uncommitted and why.

# Types

The type says what the change does, regardless of where it is:

- `feat` new behavior
- `fix` bug fix
- `perf` faster, same behavior
- `refactor` restructured code, same behavior
- `style` formatting only
- `test` tests only
- `docs` documentation only
- `build` build system or packaging config
- `ci` CI pipelines
- `chore` maintenance, including dependency updates
- `revert` reverts a previous commit

Breaking change: add `!` before the colon (`feat(user)!: ...`) and a `BREAKING CHANGE:` footer.

# Scope

The scope says where the code changed. Take it from the paths in the staged diff:

1. **One domain.** All changes belong to one domain from "Domain scopes" above → use that domain. This includes its
   tests and migrations, even when they live outside the domain folder.
2. **Non-domain code.** Changes in the package root or in a folder that is not a domain → name that area in one
   lowercase singular word: `core/` → `core`, `middlewares/` → `middleware`, `settings.py` or `logging_config.py` →
   `config`. If recent commits already use a scope for this area, reuse it.
3. **Dependencies only.** Only dependency manifests or lock files changed → `deps`.
4. **The type already says where.** CI config or top-level docs such as README → omit the scope (`ci: ...`,
   `docs: ...`).
5. **Several domains.** If you staged the changes, split them into one commit per domain. If the user staged them
   together, keep their staging, omit the scope, and note in the report that it could be split. Never pick one domain
   arbitrarily: that makes the history misleading.

The domain list above is authoritative. Recent commits may contain scopes of domains that were renamed or removed; do
not reuse those.

# Message rules

- Header: `type(scope): description`, 72 characters max.
- Description: imperative mood ("add", not "added"), lowercase, no trailing period. Say what the commit does, not which
  files changed.
- Body (optional): why the change was made, wrapped at 72 characters. Add one for non-obvious fixes and breaking
  changes.
- Footer (optional): `BREAKING CHANGE: ...` or `Refs: #123`.

# Examples

Input: `src/<package>/user/router.py`, `src/<package>/user/service.py` — new endpoint
Output: `feat(user): add email verification endpoint`

Input: `src/<package>/middlewares/request_id.py` — used by every route
Output: `feat(middleware): add global request id middleware`

Input: `src/<package>/user/events.py`, `src/<package>/order/events.py` — one change that cannot be separated
Output: `feat: sync user and order events`

For tests, dependencies, CI and docs, split commits, breaking changes and reverts, see [examples.md](examples.md).