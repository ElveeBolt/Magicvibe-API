# Glossary

One term — one meaning. Use these words in code, specs, tasks and docs; avoid the synonyms listed under "Not". The
Ukrainian column is the wording for the bot interface.

Rules behind the terms: [PRD](./prd.md).

## System

| Term          | Ukrainian (bot) | Meaning                                                                                            | Not                                  |
|---------------|-----------------|----------------------------------------------------------------------------------------------------|--------------------------------------|
| Bot           | Бот             | The Telegram bot (separate repository). The only user interface.                                   | —                                    |
| API           | —               | This backend. Owns all data and business rules. Never calls Telegram.                              | "server", "backend service" in specs |
| Administrator | Адміністратор   | A person who manages reports, bans and premium through the API.                                    | "moderator" as a separate role       |
| KATOTTH       | КАТОТТГ         | Official Ukrainian codifier of administrative-territorial units; the source of regions and cities. | "KATOTTG"                            |
| Service token | —               | The bearer token the bot sends on every request (`AUTH__SERVICE_TOKEN`). Never logged.             | "API key"                            |

## Accounts

| Term             | Ukrainian (bot)    | Meaning                                                                                                                                                                      | Not                     |
|------------------|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|
| User             | Користувач         | An account in MagicVibe, tied to exactly one Telegram account.                                                                                                               | "member", "client"      |
| Acting user      | —                  | The user on whose behalf a request is made, identified by `X-Telegram-User-Id`.                                                                                              | "current user" in docs  |
| Telegram data    | —                  | Name, username, language and Telegram ID taken from Telegram. Shown to others only after a match.                                                                            | Profile                 |
| Telegram Premium | —                  | The paid Telegram subscription (`is_premium` flag). Unrelated to MagicVibe plans.                                                                                            | Premium plan            |
| Hidden profile   | Прихований профіль | A profile the user has hidden. Excluded from discovery only; still shown in "Who liked me" and in matches. The user can still browse, react and see matches.                 | Account deletion        |
| Account deletion | Видалення акаунта  | Permanent removal of the account and all its data. Not allowed while the user is banned. Cannot be undone; `/start` afterwards creates a new account.                        | "soft delete", "restore" |

## Profile and search

| Term             | Ukrainian (bot)  | Meaning                                                                                                                   | Not                  |
|------------------|------------------|---------------------------------------------------------------------------------------------------------------------------|----------------------|
| Profile          | Анкета           | What others see: name, age, gender, city, dating goal, optional bio and up to 3 photos.                                   | Telegram data        |
| Public profile   | —                | The part of the profile shown in discovery and "who liked me", plus when the user was last online. Never contains Telegram data or like messages. | —                    |
| Complete profile | Заповнена анкета | A profile with all required fields filled. Required both to be shown in discovery and to use it. Bio and photos are not required. | —                    |
| Dating goal      | Мета знайомства  | Exactly one of: relationship, friendship, casual, chatting.                                                               | "interest", "intent" |
| Region           | Область          | An oblast, the Autonomous Republic of Crimea, Kyiv or Sevastopol. The first step of city selection.                       | "district", "state"  |
| City             | Місто            | A city from KATOTTH within a region. Villages and districts are not cities.                                               | "location", "town"   |
| Preference       | Кого шукаю       | Who the user is looking for: gender, age range, city, dating goal. Each may be "any". Set separately from the profile.    | "filter", "settings" |
| Two-way fit      | —                | Both users match each other's preferences. Required for a profile to be shown.                                            | "mutual match"       |

## Discovery and reactions

| Term         | Ukrainian (bot)       | Meaning                                                                                                                                 | Not                         |
|--------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| Discovery    | Перегляд анкет        | Showing profiles one at a time in random order.                                                                                         | "feed", "search", "swiping" |
| Discoverable | —                     | A user who can be shown to others: status active (not banned), profile not hidden, profile complete.                    | "visible" alone             |
| Candidate    | —                     | A discoverable profile that fits the acting user in both directions and was not reacted to yet.                                         | —                           |
| Reaction     | Реакція               | A user's decision on another profile: like, superlike or dislike. One per pair, cannot be changed.                                      | "swipe", "vote"             |
| Like         | Лайк                  | A positive reaction. May carry a message.                                                                                               | —                           |
| Superlike    | Суперлайк             | A like marked as special. Has its own daily limit (see [Plans](./plans.md)).                                                            | —                           |
| Dislike      | Дизлайк               | A negative reaction. The profile is not shown again while the reaction exists.                                                          | "skip", "pass"              |
| Like message | Повідомлення до лайка | A short text attached to a like or superlike. Visible to the recipient only after a match.                                              | "chat message"              |
| Match        | Метч                  | Two users who liked each other. Both receive each other's Telegram contact. Users cannot cancel it; it is hidden while one of the users is banned and disappears only when one of the accounts is deleted. | "pair", "connection"        |
| Who liked me | Хто мене лайкнув      | Premium list of users who liked the acting user and whom the acting user has not reacted to yet. Banned users are excluded.             | Outgoing likes              |

## Plans

| Term           | Ukrainian (bot) | Meaning                                                                                                  | Not               |
|----------------|-----------------|----------------------------------------------------------------------------------------------------------|-------------------|
| Plan           | Тариф           | A set of limits and features. Plans are defined in [Plans](./plans.md).                                  | "tier", "package" |
| Free           | Безкоштовний    | The default plan.                                                                                        | —                 |
| Premium        | Преміум         | The paid plan, paid outside MagicVibe and granted by an administrator.                                   | Telegram Premium  |
| Subscription   | Підписка        | A period during which a user has premium. Starts when granted, never in the future. It is current while `starts_at <= now() < expires_at`; at most one is current, and granting premium while one is current is rejected. | Plan              |
| Effective plan | —               | The plan that applies now: premium during a current subscription, otherwise free.                        | —                 |
| Daily limit    | Денний ліміт    | Maximum likes or superlikes per day, set per plan (see [Plans](./plans.md)).                             | "quota"           |

## Moderation

| Term          | Ukrainian (bot)        | Meaning                                                                                                        | Not              |
|---------------|------------------------|----------------------------------------------------------------------------------------------------------------|------------------|
| Report        | Скарга                 | A complaint from one user about another, with a reason. Does not hide anyone.                                  | "flag"           |
| Report reason | Причина скарги         | Why a user filed a report. Values: [`ReportReason`](./architecture/models.md#reportreason).                    | Ban reason       |
| Ban reason    | Причина блокування     | Why an administrator set a ban. A separate list: [`BanReason`](./architecture/models.md#banreason).            | Report reason    |
| Ban           | Блокування             | A restriction set by an administrator, always with a ban reason. The user cannot do anything in the bot, including deleting the account. Deletes nothing: the user's data is kept but hidden from others until the ban is lifted; other users cannot react to them. Has no end date: lasts until lifted. Starting the bot again (`/start`) does not lift it and does not update their Telegram data; the user is told about the ban. | Telegram block   |
| Lift          | Зняти блокування       | Ending a ban by an administrator. The only way a ban ends.                                                     | "unban" in specs |
