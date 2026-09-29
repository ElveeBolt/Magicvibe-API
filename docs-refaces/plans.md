# Plans

This document describes the plans, their daily like limits, available features, and activation rules.

- Terms: [Glossary → Plans](./glossary.md#plans)
- Subscriptions table: [Data model → `subscription` domain](./architecture/models.md#subscription-domain)

## Plan table

| Plan    | Code      | Duration    | Likes per day | Superlikes per day | Who liked me |
|---------|-----------|-------------|---------------|--------------------|--------------|
| Free    | `free`    | no end date | 5             | 0                  | no           |
| Premium | `premium` | 7 days      | 20            | 5                  | yes          |

## Which plan applies

- Every user is on the free plan unless they have current premium.
- When premium ends, the user returns to the free plan.

## Daily limits

- Limits reset at midnight Kyiv time (Europe/Kyiv).
- Dislikes are unlimited on every plan.
- A superlike counts only toward the superlike limit, not the like limit.
- When a limit is reached, the user is told and informed when it resets.

## Granting premium

- There is no payment yet. A user asks support in Telegram, and an administrator grants premium.
- Premium lasts for the duration in the plan table and starts at the moment it is granted. It cannot be
  granted for a future date.
- A user has at most one current premium period. An administrator can end it early; the change applies immediately.
- When premium ends, the user can ask support again and receive another period. There is no limit on how many times
  premium can be granted.
- Free users who open "Who liked me" are offered premium.

## In code

Plans are constants in `subscription/constants.py`, and their values must match the
[plan table](#plan-table) exactly:

```python
@dataclass(frozen=True)
class Plan:
    code: PlanCode
    name: str
    duration_days: int | None  # None = no end date
    daily_like_limit: int
    daily_superlike_limit: int
    can_see_likers: bool  # access to "Who liked me"


@dataclass(frozen=True)
class FreePlan(Plan):
    code: PlanCode = PlanCode.FREE
    name: str = "Free"
    duration_days: int | None = None
    daily_like_limit: int = 5
    daily_superlike_limit: int = 0
    can_see_likers: bool = False


@dataclass(frozen=True)
class PremiumPlan(Plan):
    code: PlanCode = PlanCode.PREMIUM
    name: str = "Premium"
    duration_days: int | None = 7
    daily_like_limit: int = 20
    daily_superlike_limit: int = 5
    can_see_likers: bool = True


PLANS: dict[PlanCode, Plan] = {
    PlanCode.FREE: FreePlan(),
    PlanCode.PREMIUM: PremiumPlan(),
}
```

A subscription refers to its plan by code: `subscriptions.plan` (enum [
`PlanCode`](./architecture/models.md#plancode))
→ `PLANS[subscription.plan]`.

When the plans change, update the plan table first, then the classes in `subscription/constants.py`. New limits
apply to all users after the deploy. A new duration applies only to premium granted after the deploy, because
`expires_at` of existing subscriptions is already stored.
