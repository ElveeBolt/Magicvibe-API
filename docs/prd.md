# MagicVibe — Product Requirements Document

| Field        | Value                                      |
|--------------|--------------------------------------------|
| Product      | MagicVibe (dating service inside Telegram) |
| Status       | Draft                                      |
| Last updated | 2026-09-29                                 |

This document describes **why** MagicVibe exists, **who** it is for, **what** is in scope and the **business rules** in
plain language. It does not describe the API contract, data model or implementation.

- Architecture and conventions: [Conventions](./architecture/conventions.md), [Data model](./architecture/models.md),
  [Non-functional requirements](./architecture/nfr.md)
- Terms used below: [Glossary](./glossary.md)

---

## 1. Overview

MagicVibe is a dating service that runs inside Telegram. People meet new people without installing a separate app,
similar in spirit to Tinder or Badoo.

Users interact only with the Telegram bot. The bot relies on the MagicVibe backend, which owns all data and business
rules. Other clients (for example a Telegram Mini App or an admin panel) may use the same backend later.

**What makes MagicVibe different** from existing Telegram dating bots:

- flexible search filters that work in both directions;
- rich profiles;
- user moderation (reports and bans).

## 2. Goals and success metrics

### 2.1 Business goals (MVP)

- Launch the product and build an active audience.
- Earn enough from paid plans to at least cover infrastructure costs.

### 2.2 Success metrics

These are the criteria of success. The MVP does not collect or compute them: nothing is stored or logged for metrics,
and data for the period before metrics are implemented will not be available.

- Monthly and daily active users.
- Active (discoverable) profiles.
- Likes, superlikes and matches per day.
- Conversion to paid plans.

## 3. Target audience

- Adults **18+** living in **Ukraine**.
- Users write in Ukrainian, Russian, surzhyk or neighbouring languages. Their text is kept exactly as written.
- The bot speaks **Ukrainian only**.
- Dating goals: relationship, friendship, casual meetings, just chatting.
- Expected load is unknown at launch; the product must be able to grow to a large audience.

## 4. Scope

### 4.1 In scope (MVP)

- Sign-up with a Telegram account only.
- Profile with required and optional fields.
- Profile images: up to 3 photos, managed separately from the profile.
- City selection in two steps (region → city) from the official Ukrainian list.
- Discovery preferences ("who I am looking for"), set separately from the profile.
- Hiding the profile and deleting the account.
- Browsing profiles one at a time, matched in both directions.
- Like, superlike (both optionally with a message) and dislike. Mutual likes create a match.
- Two plans, **free** and **premium**, with different daily limits and features.
- "Who liked me" list for premium users.
- Premium granted manually by an administrator; the user pays outside MagicVibe.
- Match notifications with the other person's Telegram contact.
- Reports (complaints) against users.
- Moderation: reviewing reports, bans with a reason (no end date; only an administrator can lift a ban).

### 4.2 Out of scope

Product:

- In-app chat or message relay between users.
- Payments inside MagicVibe of any kind. Premium is paid outside the product.
- Interests, education, smoking, drinking — as profile fields or filters.
- Anything based on location coordinates: sharing location, nearest city, distance search.
- Villages, settlements and city districts in the city list; searching cities by text; alternative city names.
- Recommendation or ranking of profiles (order is random).
- Verification of users (selfie, phone, documents).
- Automatic moderation of photos and text, anti-bot or anti-fake protection.
- Unmatch.
- Showing users how many likes they have left today (they are told only when the limit is reached).
- Referral programme, mass broadcasts, notification settings.
- Recording which administrator took an action.
- Admin panel or any web interface.
- Collecting or computing success metrics, and external analytics integrations.

Engineering (MVP):

- The Telegram bot itself (separate repository).
- Health-check endpoint.

### 4.3 Planned for later

- Payments for premium inside MagicVibe.
- Admin panel for moderation and subscriptions.
- Other clients, e.g. a Telegram Mini App.

The MVP must not block these.

## 5. Main user journey

1. The user opens the bot and is registered with their Telegram account.
2. The user fills in the profile and chooses a city.
3. The user optionally uploads profile images.
4. The user sets discovery preferences (who they are looking for).
5. The user browses profiles one by one and likes, superlikes or dislikes each.
6. When two people like each other, the bot notifies both and gives them each other's Telegram contact. Further
   conversation happens in Telegram.

## 6. Business rules

### 6.1 Accounts

- An account is tied to exactly one Telegram account. There are no passwords or phone numbers.
- When a user starts the bot again (`/start`) with the same Telegram account, the stored Telegram details are updated
  instead of creating a new account. A **banned** user who starts the bot again is told about the ban, and their
  stored Telegram details are not updated.
- A user can **hide** their profile. A hidden user is not shown in discovery but is still shown in "Who liked me"
  and in matches, and can still browse, react and see matches.
- A user who is not banned can **delete** their account. Deletion is permanent and total: the account, Telegram data,
  profile, profile images, discovery preferences, reactions given and received, matches, reports by and against the
  user, subscriptions and lifted bans are all deleted. Nothing can be restored.
- After deletion, starting the bot again (`/start`) creates a new account from scratch.
- A **banned** user cannot do anything in the bot, including deleting the account. They are told the reason. Their
  data is kept unchanged but hidden from other users: from discovery, from "Who liked me" and from other users' match
  lists. When the ban is lifted, everything becomes visible again.
- The user can see their current plan and when premium ends.

### 6.2 Profile

Required:

- name (up to 64 characters);
- date of birth (age from 18 to 100, inclusive);
- gender: male, female or other;
- city;
- one dating goal: relationship, friendship, casual or chatting.

Optional: bio (up to 500 characters).

Age is calculated from the date of birth.

Every profile field can be changed at any time. A change follows the same rules as above; a value outside them is
rejected with an error.

### 6.3 Region and city

- Cities come from the official Ukrainian codifier of administrative-territorial units (KATOTTH).
- The user picks a **region** first, then a **city** in that region. There is no text search.
- Regions are oblasts, the Autonomous Republic of Crimea, Kyiv and Sevastopol. Choosing Kyiv or Sevastopol offers that
  one city.
- Only cities are offered, not villages or districts. All cities are included, including temporarily occupied
  territories and Crimea.
- Names are shown in Ukrainian as in the codifier.
- Regions and cities are never deleted or disabled. When a new edition of the codifier adds cities, they are added to
  the list; a city once added stays in the list.

### 6.4 Profile images

- A user has up to 3 photos. Photos are optional; the user can delete all of them.
- All photos are shown together, at once. The user cannot change their order.
- Photos come through Telegram. MagicVibe accepts the same photo formats and sizes as Telegram and adds no limits of its
  own.

### 6.5 Discovery preferences

- Gender: one gender or any.
- Age range: from 18 to 100, inclusive.
- City: one city or any.
- Dating goal: one goal or any.
- Discovery preferences must be set before the user can browse.

### 6.6 Discovery

- Profiles are shown **one at a time, in random order**.
- A shown profile (in discovery and in "Who liked me") also tells when its owner was last online.
- A profile is shown only if the account status is **active** (not banned), the profile is not hidden and **all
  required profile fields are filled in**. A profile with some required fields missing is never shown. Bio and profile
  images are not required.
- **Two-way fit:** the other person must match the user's discovery preferences, **and** the user must match the other
  person's discovery preferences.
- A user who has not set discovery preferences yet is not shown to others: the fit in their direction cannot be
  checked. They appear as soon as they set preferences.
- A profile the user has already reacted to is not shown again while the reaction exists. Reactions are deleted when
  either account is deleted (see 6.1).
- To browse, the user needs a profile with all required fields filled in and discovery preferences. Hidden users can
  still browse.
- A report does not hide anyone. A reported user stays visible to everyone, including the reporter, until an
  administrator bans them.

### 6.7 Reactions and matches

- On each profile the user can **like**, **superlike** or **dislike**.
- A like or superlike may include a short message (up to 500 characters). An empty message is not allowed.
- A reaction cannot be changed or repeated.
- The backend does not check that the other user was shown to the reacting user (in discovery or in "Who liked me");
  the bot reacts only to profiles it has shown.
- When two users like each other (like or superlike, in any combination), it is a **match**. The bot notifies both
  users and gives them each other's Telegram contact; MagicVibe itself never sends messages in Telegram.
- A message attached to a like becomes visible to its recipient **only after a match**.
- Users cannot cancel a match. A match disappears only when one of the two accounts is deleted, and is hidden while
  one of the two users is banned. There is no chat inside MagicVibe.

### 6.8 Plans and premium

Plans, daily limits and how premium is granted are defined only in [Plans](./plans.md).

- **Who liked me** (only on plans that include it, see [Plans](./plans.md)) shows the people who liked or
  superliked **this user** (incoming likes). Once the user reacts to someone from the list (like, superlike or
  dislike), that person leaves the list.
- Superlikes are shown first in the list; within superlikes and within likes, the newest come first.
- Banned users are not shown in "Who liked me".
- The list shows the other person's public profile and whether it was a superlike, but not their message. A like or
  superlike to someone from this list creates a match.
- There is no list of people the user has liked (outgoing likes).

### 6.9 Reports

- A user can report another user with a report reason ([`ReportReason`](./architecture/models.md#reportreason)) and an
  optional comment.
- A user cannot report themselves.
- A report always succeeds for the user who files it, even if the other user is banned or already has an open report
  from this user. While a report from this user is open, a repeated report does not create a second one.
- Administrators review reports and mark them resolved or dismissed.

### 6.10 Bans

- An administrator can ban a user with a ban reason ([`BanReason`](./architecture/models.md#banreason)) and an optional
  comment. Ban reasons are a separate list from report reasons and may differ from it.
- A ban has no end date. It lasts until an administrator lifts it (for example, if it was set by mistake).
- A ban deletes nothing. A banned user is hidden from other users immediately (see 6.1); lifting the ban makes them
  visible again with all their data.
- A user can have only one active ban at a time. After a ban is lifted, the user can be banned again.

### 6.11 Administration

- All administrative actions (reports, bans, premium) are done through the backend. There is no admin interface in the
  MVP.
