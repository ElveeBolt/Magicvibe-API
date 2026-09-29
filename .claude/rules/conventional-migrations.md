---
paths:
  - "src/*/*/models/**/*.py"
---

# Conventional Migrations Rules

- Migrations are only touched when a file in `models/` changes. If models are
  unchanged, don't create, edit, or regenerate a migration.
- When a model changes: `uv run alembic revision --autogenerate -m "<description>"`.
  Never write a migration file by hand. One exception: autogenerate does not
  detect a check constraint added to an existing table, so append exactly
  `op.create_check_constraint(...)` (upgrade) and `op.drop_constraint(...)`
  (downgrade) — the model's name and expression — to the newly generated, not
  yet merged file, and cover it with a test that expects it by name.
- Never edit, rename, or delete an existing file in `alembic/versions/`. If a
  past migration was wrong, generate a new one that corrects it.
- Don't run `alembic upgrade` / `alembic downgrade` as part of this — only
  generate the migration file.