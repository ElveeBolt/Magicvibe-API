# Tasks

## 1. Domain, model and migration

- [x] 1.1 `subscription/enums.py` (`PlanCode`), `subscription/constants.py` (the plan classes and `PLANS` exactly as in
  `plan_constants.md`, `MAX_COMMENT_LENGTH`), `subscription/models/subscription.py` with both checks and the index;
  register the model in `alembic/env.py`; verify mypy
- [x] 1.2 Generate the migration on a throwaway `postgres:18.6` container; verify it creates `plan_code_enum`,
  `subscriptions` with `ck_subscriptions_expires_after_start`, `ck_subscriptions_paid_plan_only` and
  `ix_subscriptions_user_id_expires_at`, and the test session applies it

## 2. Service and API

- [x] 2.1 Repository (`get_current`, `has_unexpired`, `create_for`, `end`), `SubscriptionService` (`grant`, `end`,
  `get_effective_plan`, list/get), schemas, router (`/subscriptions`, `/subscriptions/{id}/end`,
  `/users/{user_id}/plan`), dependencies; register in `uow.py` and `router.py`; verify mypy and ruff
- [x] 2.2 `tests/factories.py`: `create_subscription` (with `starts_at` / `expires_at` relative to `now()`);
  `tests/subscription/test_router.py` for every `plans` scenario, with a `@pytest.mark.concurrency` test of
  simultaneous grants; `test_services.py` for the effective plan at the `expires_at` boundary;
  `test_models.py` for both checks; `test_constants.py`: `PLANS` equals the plan table of `docs/plans.md`; verify
  `uv run --no-sync pytest` passes

## 3. Integration checks

- [x] 3.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-subscriptions --strict`; all exit 0
