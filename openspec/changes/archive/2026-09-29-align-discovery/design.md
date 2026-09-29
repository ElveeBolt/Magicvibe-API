# Design

## Context

- `DiscoveryRepository.get_next_candidate` joins `User.profile`, filters active/visible/not self/not reacted, the
  viewer's gender and birth-date window, and "no preference of theirs rejects me" (so candidates without preferences
  pass), then orders by "superliked me" and `random()`.
- `DiscoveryService` builds the filters from the acting user (`CurrentUserDep` carries profile and preference); it
  treats missing viewer preferences as defaults.
- `UserPublicSchema` is `{id, profile}`; `MatchedUserSchema` extends it.

## Goals / Non-Goals

**Goals:** one query per request, as today; the whole fit expressed in SQL.

**Non-Goals:** performance work beyond the existing indexes (NFR-01 targets are not measured here); who-liked-me.

## Decisions

### Inner join on preferences, explicit conditions both ways

The query joins `User.profile` and `User.preference` (inner joins: no profile or no preferences → not a candidate)
and adds:

- viewer's wishes on the candidate: `birth_date` in the window from the viewer's ages; `gender`, `city_id`,
  `dating_goal` equal to the viewer's when the viewer's value is not null;
- candidate's wishes on the viewer: `min_age <= viewer_age <= max_age`; `gender`, `city_id`, `dating_goal` null or
  equal to the viewer's profile value.

The negated `NOT EXISTS` form goes: with an inner join the positive form reads as the rule does. The viewer's age is
computed once per request from the profile (as today), the candidates' through the birth-date window.

### Random order only

`ORDER BY random() LIMIT 1`. Removing the superlike ranking follows the PRD ("random order").

### Response is the public profile or `null`

The route's `response_model` is `UserPublicSchema | None`; FastAPI renders `None` as `null`. `UserPublicSchema` gains
`last_seen_at`. `discovery/schemas/` (only `NextCandidateSchema`) is deleted rather than left empty.

## Risks / Trade-offs

- [Users mid-registration (profile, no preferences) are invisible until they set preferences] → intended, agreed with
  the owner and written into the PRD.
- [`ORDER BY random()` scans all fitting rows] → unchanged from today; revisit with real load (NFR-01).
