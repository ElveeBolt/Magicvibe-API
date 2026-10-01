# Plan constants

How the plans from [Plans](../plans.md) are implemented. The [plan table](../plans.md#plan-table) is the only source of
the values; this document describes where they live in code and does not repeat them.

Plans are not stored in the database. They are constants in `subscription/constants.py`: one frozen dataclass `Plan`
with a field for every column of the plan table, one subclass per plan with that plan's row as its defaults
(`FreePlan`, `PremiumPlan`), and `PLANS`, which maps each [`PlanCode`](./models.md#plancode) to an instance.

| `Plan` field            | Plan table column  | Notes                                |
|-------------------------|--------------------|--------------------------------------|
| `code`                  | Code               | a `PlanCode` value                   |
| `name`                  | Plan               |                                      |
| `duration_days`         | Duration           | `None` = no end date                 |
| `daily_like_limit`      | Likes per day      |                                      |
| `daily_superlike_limit` | Superlikes per day | `0` = superlikes are not on the plan |
| `can_see_likers`        | Who liked me       |                                      |

`tests/subscription/test_constants.py` reads the plan table and fails when `PLANS` differs from it.

A subscription refers to its plan by code: `subscriptions.plan` → `PLANS[subscription.plan]`.

When the plans change, update the [plan table](../plans.md#plan-table) first, then the classes in
`subscription/constants.py`. New limits apply to all users after the deploy. A new duration applies only to premium
granted after the deploy, because `expires_at` of existing subscriptions is already stored.
