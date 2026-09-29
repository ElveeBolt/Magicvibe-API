# Plan constants

How the plans from [Plans](../plans.md) are implemented. The plan table there is the source of the values; this
document only describes where they live in code.

Plans are constants in `subscription/constants.py`, and their values must match the
[plan table](../plans.md#plan-table) exactly:

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

A subscription refers to its plan by code: `subscriptions.plan` (enum [`PlanCode`](./models.md#plancode)) →
`PLANS[subscription.plan]`.

When the plans change, update the [plan table](../plans.md#plan-table) first, then the classes in
`subscription/constants.py`. New limits apply to all users after the deploy. A new duration applies only to premium
granted after the deploy, because `expires_at` of existing subscriptions is already stored.
