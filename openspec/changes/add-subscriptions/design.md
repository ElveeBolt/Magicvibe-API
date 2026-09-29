# Design

## Context

- `plan_constants.md` gives the exact dataclasses (`Plan`, `FreePlan`, `PremiumPlan`, `PLANS`); `models.md` the table,
  its two checks and the index; `glossary.md` the "current" rule (`starts_at <= now() < expires_at`).
- Ban creation and account deletion already lock the user row with `UserRepository.get_for_update`.
- In tests `now()` is fixed for the whole test transaction.

## Goals / Non-Goals

**Goals:** one definition of "current subscription" and "effective plan" that `add-daily-limits` reuses; the
one-current-subscription rule safe under concurrency.

**Non-Goals:** limits, `PREMIUM_REQUIRED`, "Who liked me"; payments (out of scope).

## Decisions

### Times come from the database

`starts_at` has `server_default=now()` and is never in a schema. `expires_at` is inserted as
`now() + interval '<duration_days> days'`, so both come from the same transaction clock; ending early sets
`expires_at = now()`. *Alternative:* Python `datetime.now(UTC)` — rejected: the two clocks could differ, and `models.md`
says `starts_at` is set only by the database default.

### One current subscription: lock the user, then check

`SubscriptionService.grant` locks the user with `get_for_update` (404 if missing), rejects `banned`
(`TARGET_USER_BANNED`), checks `SubscriptionRepository.get_current(user_id)` (`PREMIUM_ALREADY_ACTIVE`), then inserts.
Two grants for one user serialize on the row lock, as `conventions.md` requires for rules that depend on other rows.

### Effective plan in the service

`SubscriptionService.get_effective_plan(user_id) -> (Plan, Subscription | None)` is the single place that turns the
current subscription into `PLANS[...]`, falling back to `FreePlan`. `GET /users/{user_id}/plan` lives in the
`subscription` router (a domain router may serve paths of another resource, as the reaction router serves
`/matches`) and returns `PlanReadSchema` (`code`, `name`, the limits, `can_see_likers`, `expires_at`).

### Schemas

`SubscriptionCreateSchema`: `user_id`, `plan: Literal[PlanCode.PREMIUM] = PlanCode.PREMIUM`, `comment`. No update
schema: a subscription changes only by ending it. `SubscriptionFilterSchema`: `user_id`, `order_by` `created_at`.

## Risks / Trade-offs

- [Ending a subscription in the same transaction that created it would violate `expires_after_start`] → cannot happen
  through the API (each request is its own transaction); tests move `starts_at` into the past first.
