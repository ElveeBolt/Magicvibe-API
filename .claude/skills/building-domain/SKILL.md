---
name: building-domain
description: Build and evolve domain modules under src/<package>/<domain>/. Use when creating a new domain package, adding an entity or model, adding or changing an endpoint, writing service logic, repositories, schemas, schema types or validators, or domain tests.
license: MIT
metadata:
  author: boltelvee
  version: "1.0"
---

# Building a domain

This skill is the procedure: what to decide, in which order to build, and what
counts as done. Layout, layer responsibilities and isolation rules live in
`.claude/rules/domain-structure.md`.

One procedure covers every change: new domain, new entity, new endpoint. The
difference is only how many layers it touches.

## 1. Decide the scope

Decide everything else yourself from the request and the existing code. Do not
stop to ask — a skeleton is cheap to adjust and every decision here is
recoverable. Report the choices at the end so they can be corrected.

Answer only the questions your change raises:

- **New package?** Name it with an English singular snake_case noun that is a
  valid Python identifier: "домен повідомлень" → `message`, "order items" →
  `order_item`.
- **Does it own data?** Assume yes unless the request describes pure
  orchestration or an external integration. If no → no `models/`, no
  `repositories.py`, no migration, and the service takes the client or
  collaborating service it needs instead of a UoW.
- **New entity — own aggregate or nested?** The expensive decision. A nested
  entity goes in `<entity>_<sub>.py` and is reached through the parent's
  repository; a separate aggregate gets its own file, repository and lifecycle.
  Two aggregates in one file cannot be split later without a migration.
- **New endpoint?** The logic goes in `services.py` first. If the behaviour does
  not exist as a service method, the service is what is missing — not the route.

Give the entity only the fields the request implies. Inventing columns costs a
migration to remove.

## 2. Naming

| Thing          | Pattern                 | Example              |
|----------------|-------------------------|----------------------|
| domain package | singular snake_case     | `entity`             |
| model          | PascalCase              | `Entity`             |
| table          | plural snake_case       | `entities`           |
| repository     | `<Model>Repository`     | `EntityRepository`   |
| service        | `<Model>Service`        | `EntityService`      |
| schemas        | `<Model><Intent>Schema` | `EntityCreateSchema` |
| route prefix   | plural                  | `/entities`          |

## 3. Build bottom-up

Work top to bottom through this list, skipping the layers your change does not
touch. The order matters: each layer is written against something that already
exists. Read the reference before writing the layer.

A domain always has `__init__.py`, `router.py`, `services.py` and
`tests/<domain>/__init__.py`; everything else exists only because a line above
justified it.

Data owned by another domain is reached through that domain's service, never
through its models or repositories.

**Model** — the domain owns new data → See [references/model.md](references/model.md)

**Enums** — a fixed set of values appears → See [references/enum.md](references/enum.md)

**Schemas** — an entity is added or its shape changes → See [references/schema.md](references/schema.md)

**Repository** — a new aggregate appears → See [references/repository.md](references/repository.md)

**Constants** — a limit, quota or page size enters the rules → See [references/constant.md](references/constant.md)

**Service** — always → See [references/service.md](references/service.md)

**Dependencies** — a new service, or different auth or scoping →
See [references/dependency.md](references/dependency.md)

**Router** — a new HTTP surface → See [references/router.md](references/router.md)

## 4. Register the model and the router

Both of these fail silently and produce a misleading symptom downstream:

- every model listed in `models/__init__.py` — Alembic autogenerate and the UoW
  see only what is listed there;
- the router added to the aggregator — without it route tests return 404 and the
  failure looks like a broken test.

## 5. Migration

Only if `models/` changed, and only after step 4. Follow the conventional
migrations rule.

Read the generated file. An empty `upgrade()` means the models are not reachable
from `models/__init__.py` — fix that and regenerate.

## 6. Tests

Any change that adds a branch needs one. A rename or a docstring does not.

## 7. Verify

```
uv run ruff check src/<package>/<domain>/ tests/<domain>/
uv run mypy src/<package>/<domain>/
uv run pytest tests/<domain>/
```

Fix what they report and rerun until clean; never report success over a red
check. Then confirm no use of another domain's models, repositories or service
internals.

## 8. Report

One pass, no follow-up questions:

- the domain, entity and table names chosen — nobody else picked them, so they
  have to be visible to be objected to;
- files created or changed;
- the migration revision, if one was generated;
- what was deliberately left out (no models, so no migration; no fixed value
  sets, so no `enums.py`) — so it reads as a decision, not an omission.

## Reference

@.claude/rules/domain-structure.md

@.claude/rules/conventional-commits.md

@.claude/rules/conventional-migrations.md