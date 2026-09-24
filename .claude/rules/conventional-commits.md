# Conventional Commits Rules

Use Conventional Commits. This project uses python-semantic-release — wrong commit format breaks automated versioning.

- Header: `type(scope): description`, 72 characters max.
- Scope: domain name from `src/<package>/<domain>/`, or omitted.
- Description: imperative mood ("add", not "added"), lowercase, no trailing period. Say what the commit does, not which
  files changed.
- Body (optional): why the change was made, wrapped at 72 characters. Add one for non-obvious fixes and breaking
  changes.

Version impact (python-semantic-release, conventional parser):

- `feat` → minor
- `fix` → patch
- `chore`, `docs`, `refactor`, `test`, `style`, `ci`, `build`, `revert`  → no release
- Breaking change → major: `feat(domain)!: ...` or a `BREAKING CHANGE: <what broke>` footer.
  Never introduce one without being asked.

## Pre-commit Hooks

- Never bypass hooks: no `--no-verify`, no `-n`, no `SKIP=<hook-id>`.
- If a hook modifies files, `git add` them and retry. Max 2 retries, then stop and report.
- If a hook fails, fix the cause. Never silence it with `# noqa`, `# type: ignore`,
  or by loosening tool config.