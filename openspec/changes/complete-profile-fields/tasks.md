# Tasks

## 1. Rules for hand-appended check constraints

- [ ] 1.1 `.claude/rules/conventional-migrations.md` and `docs/architecture/conventions.md` → Migrations: a check
  constraint on an existing table, which autogenerate does not detect, is appended by hand to the newly generated,
  not yet merged migration — only `op.create_check_constraint` / `op.drop_constraint` with the model's name and
  expression, and a test proves it exists; verify both documents say so

## 2. Models and migration

- [ ] 2.1 `DatingGoal` in `user/enums.py`; `UserProfile`: `city_id`, `city`, `dating_goal`, `bio` as nullable
  `String(MAX_BIO_LENGTH)` with `bio_not_empty`, no discovery index; `UserPreference`: `city_id`, `city`,
  `dating_goal`; verify mypy
- [ ] 2.2 Generate the migration with autogenerate on a throwaway `postgres:18.6` container, then append only the
  `bio_not_empty` check (upgrade and downgrade); verify the file has the enum type, the columns, the foreign keys, the
  `bio` change, the dropped index and the check, and the test session applies it

## 3. Schemas and service

- [ ] 3.1 Profile and preference schemas: `city_id`, `dating_goal`, optional `bio` (nullable in `PATCH`), read
  schemas with `city: RegionCityReadSchema`; `UserService` checks the city (404 `NOT_FOUND`) on put and patch of both,
  and `set_profile` no longer creates preferences; remove `get_or_create_preference`; verify mypy and ruff
- [ ] 3.2 `tests/factories.py`: `create_profile` and `create_preference` take a city (the profile creates a made-up
  one when none is given) and a dating goal; verify the existing tests pass
- [ ] 3.3 Tests: `tests/user/test_router.py` for every `profile` and `preferences` scenario; `tests/user/test_schemas.py`
  for `Bio`, `Name`, `BirthDate` boundaries (18th birthday today, 101st) and `DatingGoal`; `tests/user/test_models.py`
  for `bio_not_empty`, `age_range`, `age_bounds` and the city foreign key; `tests/discovery/test_router.py`: a
  candidate is returned with its city; verify `uv run --no-sync pytest` passes

## 4. Docs

- [ ] 4.1 `CLAUDE.md` "Known drift": drop `DatingGoal`; verify

## 5. Integration checks

- [ ] 5.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate complete-profile-fields --strict`; all exit 0
