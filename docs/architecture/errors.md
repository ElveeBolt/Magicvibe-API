# Errors

How the MagicVibe API reports errors. The bot decides what to show and what to do next by the error **code**; it never
parses or shows the `detail` text.

## Response body

Every error response has the same JSON body:

```json
{"code": "USER_BANNED", "detail": "Account is banned", "ban": {"reason": "spam", "comment": null}}
```

| Field    | Meaning                                                                                                   |
|----------|-----------------------------------------------------------------------------------------------------------|
| `code`   | Stable, machine-readable reason in `UPPER_SNAKE_CASE`. The bot branches on it.                            |
| `detail` | Short English message for developers and logs. Never shown to users; the bot has its own Ukrainian texts. |
| extra    | Fields some codes add so the bot can react without another request (see the table below).                 |

The HTTP status is still meaningful: it gives the category, and `code` gives the exact reason. Errors raised by the
framework itself use the same body: an unknown path returns `NOT_FOUND`, a wrong method `METHOD_NOT_ALLOWED`.

## Codes

General codes belong to no domain and are defined in `core`. Every other code is defined by the domain that owns the
rule (the **Domain** column); other domains import it from there.

### General

| Code                    | Status | When                                                                      | Extra fields |
|-------------------------|--------|---------------------------------------------------------------------------|--------------|
| `INVALID_SERVICE_TOKEN` | 401    | The service token is missing or wrong                                     | —            |
| `VALIDATION_ERROR`      | 400    | The request does not pass the schema (see [below](#validation-errors))    | `errors`     |
| `BAD_REQUEST`           | 400    | A business rule rejects the request and no specific code applies          | —            |
| `NOT_FOUND`             | 404    | The resource does not exist and no specific code applies                  | —            |
| `METHOD_NOT_ALLOWED`    | 405    | The path exists but not with this HTTP method                             | —            |
| `CONFLICT`              | 409    | The request conflicts with the current state and no specific code applies | —            |
| `INTERNAL_ERROR`        | 500    | An unexpected error. No internals are exposed                             | `request_id` |

### Accounts

| Code             | Status | Domain | When                                                                                    | Extra fields               |
|------------------|--------|--------|-----------------------------------------------------------------------------------------|----------------------------|
| `USER_NOT_FOUND` | 404    | `user` | The acting user (`X-Telegram-User-Id`) is not registered. The bot registers them first. | —                          |
| `USER_BANNED`    | 403    | `ban`  | The acting user is banned. Returned for every request they make.                        | `ban`: `reason`, `comment` |

### Profile, discovery and reactions

| Code                   | Status | Domain         | When                                                                                               | Extra fields              |
|------------------------|--------|----------------|----------------------------------------------------------------------------------------------------|---------------------------|
| `PROFILE_REQUIRED`     | 409    | `user`         | The action needs a complete profile, and the user has none                                         | —                         |
| `PREFERENCES_REQUIRED` | 409    | `user`         | Discovery needs preferences, and the user has none                                                 | —                         |
| `PHOTO_LIMIT_REACHED`  | 409    | `user`         | The profile already has the maximum number of photos                                               | `max_photos`              |
| `SELF_ACTION`          | 400    | `user`         | The user reacts to or reports themselves                                                           | —                         |
| `ALREADY_REACTED`      | 409    | `reaction`     | The user has already reacted to this person                                                        | —                         |
| `DAILY_LIMIT_REACHED`  | 429    | `reaction`     | The daily like or superlike limit is used up (see [Daily limit](#daily-limit))                     | `limit_type`, `resets_at` |
| `PREMIUM_REQUIRED`     | 403    | `subscription` | The feature is not on the user's plan: "Who liked me", or a superlike on a plan with no superlikes | —                         |

### Administration

| Code                     | Status | Domain         | When                                                          | Extra fields |
|--------------------------|--------|----------------|---------------------------------------------------------------|--------------|
| `PREMIUM_ALREADY_ACTIVE` | 409    | `subscription` | Premium is granted while the user already has current premium | —            |
| `TARGET_USER_BANNED`     | 409    | `subscription` | Premium is granted to a banned user                           | —            |
| `BAN_ALREADY_ACTIVE`     | 409    | `ban`          | A ban is set while the user already has an active ban         | —            |

Reports have no codes of their own: apart from reporting oneself (`SELF_ACTION`), a report always succeeds for the
reporter (see [PRD → Reports](../prd.md#69-reports)).

## Validation errors

A request that does not pass the schema returns 400 with `VALIDATION_ERROR` and one entry per problem:

```json
{
  "code": "VALIDATION_ERROR",
  "detail": "Request validation failed",
  "errors": [{"field": "bio", "type": "string_too_long", "message": "String should have at most 500 characters"}]
}
```

- `field` is the path to the value inside its request part, dot-separated for nested fields (`preference.min_age`).
  The part itself (`body`, `query`, `path`, `header`) is not included. It is empty when the problem concerns the
  whole object (for example `min_age` greater than `max_age`).
- `type` is the Pydantic error type (`string_too_long`, `greater_than_equal`, `extra_forbidden`, …). The bot branches
  on it, not on `message`.

## Daily limit

A used-up daily limit returns **429 Too Many Requests** ([RFC 6585](https://www.rfc-editor.org/rfc/rfc6585#section-4)),
the standard status for an exhausted quota:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 18342

{"code": "DAILY_LIMIT_REACHED", "detail": "Daily like limit reached", "limit_type": "like", "resets_at": "2026-09-30T21:00:00Z"}
```

- `limit_type` is `like` or `superlike`.
- `resets_at` is the next reset (midnight Europe/Kyiv, see [Plans](../plans.md#daily-limits)) in UTC. The bot shows it
  to the user.
- `Retry-After` is the number of seconds until `resets_at`, for HTTP clients that honour it. The bot does not retry
  the request automatically.
- A superlike on a plan whose superlike limit is 0 is not a used-up limit: it returns `PREMIUM_REQUIRED`, so the bot
  offers premium instead of saying "try tomorrow".

## Database constraint violations

A database constraint error (`IntegrityError`) is turned into a code by the constraint name: the reaction pair unique
constraint gives `ALREADY_REACTED`, the active-ban partial unique index gives `BAN_ALREADY_ACTIVE`, and any other
constraint gives `CONFLICT`. The raw database message is logged and never returned.

## Rules

- A code or a field name never changes once released. Removing or renaming one is a breaking change
  ([Versioning](../process/versioning.md#compatibility-with-the-bot)).
- Adding a code is not breaking: the bot handles an unknown code by its HTTP status.
- A new code is added only when the bot must act differently from the general code with the same status.
- Every code is one exception class. It sets the code and inherits the status from its category class in
  `core/exceptions.py` (`ConflictError` → 409, `ForbiddenError` → 403, …), so a code is never sent with another status.
  General codes live in `core/exceptions.py`, the rest in `<domain>/exceptions.py` of the owning domain.
- This document is the list of codes; the code follows it. A test checks that every exception class that sets a code
  uses one from this list with its status, and that no two classes share a code.
- An empty result is not an error: when there are no more profiles, `GET /discovery/next` returns 200 with `null`,
  not a 404.
- API tests check the status and the `code` (and extra fields), never the `detail` text
  ([Testing](./testing.md#api-tests)).
