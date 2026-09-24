# Commit message examples

`<package>` is the project's package under `src/`. Domain names below are illustrative;
the real list comes from `find_domain_scopes.py`.

## Contents

- Domain changes
- Tests and migrations
- Non-domain code
- Dependencies and build
- CI and docs
- Several domains
- Breaking changes
- Reverts

## Domain changes

Input: new endpoint in `src/<package>/user/`
Output: `feat(user): add email verification endpoint`

Input: `src/<package>/message/service.py` — retries sent the same message twice
Output:

```
fix(message): prevent duplicate delivery on retry

The retry loop re-sent messages that had already been acknowledged.
Check the delivery status before each attempt.
```

Input: queries moved from `src/<package>/order/service.py` to a new `repository.py`
Output: `refactor(order): extract repository layer`

Input: formatter run over `src/<package>/user/`
Output: `style(user): apply consistent formatting to service layer`

## Tests and migrations

Input: `tests/order/test_refunds.py` only
Output: `test(order): add coverage for refund edge cases`
Why: tests belong to the domain they test.

Input: `migrations/versions/0042_payment_tables.py`
Output: `fix(payment): correct migration ordering for payment tables`
Why: the migration lives outside the domain folder but only touches payment tables.

Input: `tests/core/test_uow.py` only
Output: `test(core): cover unit of work rollback`

## Non-domain code

Input: `src/<package>/core/uow.py`
Output: `fix(core): release session when commit fails`

Input: `src/<package>/settings.py`, `.env.example`
Output: `refactor(config): load secrets from environment variables`

Input: `src/<package>/logging_config.py`
Output: `feat(config): add json log formatter`

## Dependencies and build

Input: `pyproject.toml` dependencies section, `uv.lock`
Output: `chore(deps): bump fastapi to 0.115`

Input: `[build-system]` in `pyproject.toml`
Output: `build: switch packaging backend to hatchling`

## CI and docs

Input: `.github/workflows/tests.yml`
Output: `ci: add pytest coverage gate`

Input: `README.md`
Output: `docs: update local setup instructions`

Input: docstrings in `src/<package>/user/service.py` only
Output: `docs(user): document ban reasons`
Why: docs inside a domain get the domain scope.

## Several domains

Input: nothing staged; changes in `src/<package>/user/` and `src/<package>/order/` are independent
Output: two commits, staged separately:

```
feat(user): add profile avatar upload
fix(order): round totals per line item
```

Input: the user staged `src/<package>/user/events.py` and `src/<package>/order/events.py` together
Output: `feat: sync user and order events`
Report: "Staged changes span user and order; kept as one commit without scope."

## Breaking changes

Input: removed `/api/v1/orders/export` in `src/<package>/order/router.py`
Output:

```
feat(order)!: remove v1 export endpoint

Clients must use /api/v2/orders/export, which supports pagination.

BREAKING CHANGE: /api/v1/orders/export is removed.
```

## Reverts

Input: revert of commit `1a2b3c4` (`feat(user): add email verification endpoint`)
Output:

```
revert: add email verification endpoint

This reverts commit 1a2b3c4.
```

Why: git's default "Revert ..." header does not pass the Conventional Commits check.