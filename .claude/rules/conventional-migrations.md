---
paths:
  - "src/*/*/models/**/*.py"
---

# Conventional Migrations Rules

- Migrations are only touched when a file in `models/` changes. If models are
  unchanged, don't create, edit, or regenerate a migration.
- When a model changes: `uv run alembic revision --autogenerate -m "<description>"`.
  Never write a migration file by hand.
- Never edit, rename, or delete an existing file in `alembic/versions/`. If a
  past migration was wrong, generate a new one that corrects it.
- Don't run `alembic upgrade` / `alembic downgrade` as part of this — only
  generate the migration file.