# Project rules — FastAPI + uv

Trust level 1 ("Assistant"): propose, then wait for a human decision before changing more
than one file or running anything that is not on the allow-list in `.claude/settings.json`.

## Commands (uv only — never pip, poetry, or venv activation)

- `uv run uvicorn magicvibe.main:app --reload` — dev server (http://127.0.0.1:8000). Never start a second one.
- `uv run pytest` — run this before declaring a task done, and quote the output.
- `uv run ruff check .` — linter (replaces flake8/pylint/isort).
- `uv run ruff format --check *` — auto formatter (replaces black).
- `uv run mypy .` — static type checking.
- `uv lock --check` — check that dependencies are up to date.
- `uv sync` — install/sync dependencies from `uv.lock`.
- `uv run alembic revision --autogenerate -m "<message>"` — generate a migration after a model change.

## Definition of done

- All tests pass (`pytest` is green). New logic is covered by tests under `tests/`.
- Linting and type checking report no errors (`ruff and mypy` are green).
- Evidence, not claims: report the command you ran and its exit code / test count.

## Boundaries

Enforced by `.claude/settings.json` (ask/deny) — see there for the exact rules:
removing dependencies, `uv sync`, editing `pyproject.toml` / `alembic.ini`,
touching `.env*` files, `git push`, `rm -rf`, `alembic upgrade/downgrade`.

Not mechanically enforced — judgment required:

- Never delete or skip tests to make a task appear done.
- Never weaken or disable a linter/type-check rule to make `ruff`/`mypy` pass.
  Fix the underlying issue instead.
