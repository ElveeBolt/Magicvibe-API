# Plans

This document describes the plans, their daily like limits, available features, and activation rules.

- Terms: [Glossary → Plans](./glossary.md#plans)
- Subscriptions table: [Data model → `subscription` domain](./architecture/models.md#subscription-domain)
- How plans are implemented: [Plan constants](./architecture/plan_constants.md)

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
- Limits are checked against the plan that applies at the moment of the reaction and count the likes and superlikes
  made since the last reset. If premium ends during the day and the user has already used more than the free limit,
  they cannot like or superlike again until the next reset.

## Granting premium

- There is no payment inside the product. A user asks support in Telegram and pays outside the product; then an
  administrator grants premium. The product stores only the granted premium, not the payment.
- Premium lasts for the duration in the plan table and starts at the moment it is granted. It cannot be
  granted for a future date.
- Premium cannot be granted to a banned user.
- A user has at most one current premium period. An administrator can end it early; the change applies immediately.
- When premium ends, the user can ask support again and receive another period. There is no limit on how many times
  premium can be granted.
- Free users who open "Who liked me" are offered premium.
