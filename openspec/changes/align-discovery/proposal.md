# Proposal

## Why

[PRD → Discovery](../../../docs/prd.md#66-discovery) shows profiles one at a time in random order, only when both users
fit each other's preferences (gender, age, city, dating goal), only to a user who has a profile and preferences, and
with the owner's last online time; [Errors](../../../docs/architecture/errors.md) returns `PREFERENCES_REQUIRED` for a
user without preferences and `null` when nothing is left. The code puts users who superliked the viewer first, checks
only gender and age, lets a viewer without preferences browse with defaults, shows candidates without preferences,
wraps the result in `{"candidate": …}`, and omits the last online time.

## What Changes

- `GET /discovery/next` returns the candidate's public profile directly (`id`, `last_seen_at`, `profile`), or `null`
  when there is none. **BREAKING**: no `{"candidate": …}` wrapper (0.x).
- The viewer needs a profile (409 `PROFILE_REQUIRED`) and preferences (409 `PREFERENCES_REQUIRED`); a hidden viewer
  can browse.
- Two-way fit on all four criteria: the candidate's gender, age, city and dating goal match the viewer's preferences,
  and the viewer's match the candidate's; a `null` criterion means any.
- Only candidates who have preferences are shown — without them the fit in the candidate's direction cannot be
  checked, and such a user cannot browse yet either. **Decided with the owner**; `prd.md` (6.6) and `glossary.md`
  (Candidate) are updated first.
- Random order only; the "superliked me first" ranking is removed.
- Unchanged: banned, hidden and already-reacted users are excluded; reports hide nobody.

## Capabilities

### New Capabilities

- `discovery`: who may browse, who is a candidate, the order, and the response of `GET /discovery/next`.

### Modified Capabilities

None. (`api-errors` already lists `PROFILE_REQUIRED` for browsing without a profile; `PREFERENCES_REQUIRED` is in the
`ErrorCode` enum and is now raised.)

## Impact

- Code: `discovery` (repository query, service, router; the `schemas/` folder with `NextCandidateSchema` goes),
  `user/schemas/user.py` (`UserPublicSchema` gets `last_seen_at`).
- API: the `GET /discovery/next` body; matches (`MatchedUserSchema` extends the public schema) also get
  `last_seen_at`.
- Docs: `prd.md` 6.6 and `glossary.md` (Candidate) for the rule above.
- No model or migration changes.
