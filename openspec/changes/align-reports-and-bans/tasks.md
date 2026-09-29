# Tasks

## 1. Models and migration

- [ ] 1.1 `report/models/report.py`: add the partial unique index on `(reporter_id, target_id)` where
  `status = 'open'`; `ban/models/ban.py`: remove `expires_at`; verify mypy reports only the call sites fixed below
- [ ] 1.2 Generate the migration with autogenerate on a throwaway `postgres:18.6` container after applying the
  existing ones; verify it drops `bans.expires_at` and creates `ix_reports_reporter_id_target_id` with
  `WHERE status = 'open'`, and the test session applies it

## 2. Reports

- [ ] 2.1 `ReportRepository`: `create_if_no_open` (`ON CONFLICT DO NOTHING` on the partial index) and `get_open`;
  `ReportService.create_by_reporter_id` returns `(report, is_created)`; the router answers 201 or 200;
  `ReportUpdateSchema.status` accepts only `resolved` / `dismissed`; verify with 2.2
- [ ] 2.2 `tests/report/`: `test_router.py` for every `reports` scenario, including a `@pytest.mark.concurrency` test
  of two simultaneous repeated reports; `test_services.py` for the repeated-report and banned-target rules;
  `test_models.py` for the `not_self` check and the partial unique index (a second open report fails, a second
  resolved one does not); verify `uv run --no-sync pytest tests/report` passes

## 3. Bans

- [ ] 3.1 Remove `expires_at` from `BanReadSchema`, `BanCreateSchema` (and its validator) and `BanUpdateSchema`;
  `BanRepository.get_active` filters `lifted_at IS NULL` only; remove `has_unlifted` and use `get_active` in
  `BanService.create`; verify mypy and ruff
- [ ] 3.2 `tests/ban/`: `test_router.py` for every `bans` scenario (create sets status, `expires_at` rejected, second
  active ban, unknown user, lift sets status, lift twice, ban again after lift, old ban still blocks the acting user);
  `test_services.py` for create and lift; verify `uv run --no-sync pytest tests/ban` passes

## 4. Integration checks

- [ ] 4.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate align-reports-and-bans --strict`; all exit 0
