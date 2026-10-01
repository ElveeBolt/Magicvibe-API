# Glossary

One term — one meaning. Use these words in code, specs, tasks and docs; avoid the synonyms listed under "Not". The
Ukrainian column is the wording for the bot interface.

A meaning says what a word is, not what happens to it: the rules live in the [PRD](./prd.md) and [Plans](./plans.md),
and a meaning links to them.

## System

| Term          | Ukrainian (bot) | Meaning                                                                                            | Not                                  |
|---------------|-----------------|----------------------------------------------------------------------------------------------------|--------------------------------------|
| Bot           | Бот             | The Telegram bot (separate repository). The only user interface.                                   | —                                    |
| API           | —               | This backend. Owns all data and business rules. Never calls Telegram.                              | "server", "backend service" in specs |
| Administrator | Адміністратор   | A person who manages reports, bans and premium through the API.                                    | "moderator" as a separate role       |
| KATOTTH       | КАТОТТГ         | Official Ukrainian codifier of administrative-territorial units; the source of regions and cities. | "KATOTTG"                            |
| Service token | —               | The bearer token the bot sends on every request (`AUTH__SERVICE_TOKEN`).                           | "API key"                            |

## Accounts

| Term             | Ukrainian (bot)    | Meaning                                                                                    | Not                      |
|------------------|--------------------|--------------------------------------------------------------------------------------------|--------------------------|
| User             | Користувач         | An account in MagicVibe, tied to exactly one Telegram account.                             | "member", "client"       |
| Acting user      | —                  | The user on whose behalf a request is made, identified by `X-Telegram-User-Id`.            | "current user" in docs   |
| Telegram data    | —                  | Name, username, language and Telegram ID taken from Telegram.                              | Profile                  |
| Telegram Premium | —                  | The paid Telegram subscription (`is_premium` flag). Unrelated to MagicVibe plans.          | Premium plan             |
| Hidden profile   | Прихований профіль | A profile its owner has hidden from discovery. Rules: [PRD 6.1](./prd.md#61-accounts).     | Account deletion         |
| Account deletion | Видалення акаунта  | Permanent removal of the account and all its data. Rules: [PRD 6.1](./prd.md#61-accounts). | "soft delete", "restore" |

## Profile and search

| Term             | Ukrainian (bot)  | Meaning                                                                                                           | Not                  |
|------------------|------------------|-------------------------------------------------------------------------------------------------------------------|----------------------|
| Profile          | Анкета           | What others see: name, age, gender, city, dating goal, optional bio and photos.                                   | Telegram data        |
| Public profile   | —                | The part of the profile shown to other users in discovery and "Who liked me", plus when the user was last online. | —                    |
| Complete profile | Заповнена анкета | A profile with all required fields filled. Bio and photos are optional.                                           | —                    |
| Dating goal      | Мета знайомства  | Why the user is dating. Values: [`DatingGoal`](./architecture/models.md#datinggoal).                              | "interest", "intent" |
| Region           | Область          | An oblast, the Autonomous Republic of Crimea, Kyiv or Sevastopol. The first step of city selection.               | "district", "state"  |
| City             | Місто            | A city from KATOTTH within a region. Villages and districts are not cities.                                       | "location", "town"   |
| Preference       | Кого шукаю       | Who the user is looking for: gender, age range, city, dating goal; each may be "any".                             | "filter", "settings" |
| Two-way fit      | —                | Both users match each other's preferences.                                                                        | "mutual match"       |

## Discovery and reactions

| Term         | Ukrainian (bot)       | Meaning                                                                                                                          | Not                         |
|--------------|-----------------------|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| Discovery    | Перегляд анкет        | Showing profiles one at a time.                                                                                                  | "feed", "search", "swiping" |
| Discoverable | —                     | A user who may be shown to others at all. Rules: [PRD 6.6](./prd.md#66-discovery).                                               | "visible" alone             |
| Candidate    | —                     | A user discovery may show to the acting user now. Rules: [PRD 6.6](./prd.md#66-discovery).                                       | —                           |
| Reaction     | Реакція               | A user's decision on another profile: like, superlike or dislike.                                                                | "swipe", "vote"             |
| Like         | Лайк                  | A positive reaction. May carry a message.                                                                                        | —                           |
| Superlike    | Суперлайк             | A like marked as special.                                                                                                        | —                           |
| Dislike      | Дизлайк               | A negative reaction.                                                                                                             | "skip", "pass"              |
| Like message | Повідомлення до лайка | A short text attached to a like or superlike. Rules: [PRD 6.7](./prd.md#67-reactions-and-matches).                               | "chat message"              |
| Match        | Метч                  | Two users who liked each other. Rules: [PRD 6.7](./prd.md#67-reactions-and-matches).                                             | "pair", "connection"        |
| Who liked me | Хто мене лайкнув      | The list of users who liked the acting user and are waiting for their reaction. Rules: [PRD 6.8](./prd.md#68-plans-and-premium). | Outgoing likes              |

## Plans

| Term           | Ukrainian (bot) | Meaning                                                                                                                               | Not               |
|----------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Plan           | Тариф           | A set of limits and features. Plans are defined in [Plans](./plans.md).                                                               | "tier", "package" |
| Free           | Безкоштовний    | The default plan.                                                                                                                     | —                 |
| Premium        | Преміум         | The paid plan (see [Plans](./plans.md)).                                                                                              | Telegram Premium  |
| Subscription   | Підписка        | A period during which a user has premium. When it is current: [Data model → `subscriptions`](./architecture/models.md#subscriptions). | Plan              |
| Effective plan | —               | The plan that applies now: premium during a current subscription, otherwise free.                                                     | —                 |
| Daily limit    | Денний ліміт    | Maximum likes or superlikes per day, set per plan (see [Plans](./plans.md)).                                                          | "quota"           |

## Moderation

| Term          | Ukrainian (bot)    | Meaning                                                                                                                                       | Not              |
|---------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| Report        | Скарга             | A complaint from one user about another, with a reason.                                                                                       | "flag"           |
| Report reason | Причина скарги     | Why a user filed a report. Values: [`ReportReason`](./architecture/models.md#reportreason).                                                   | Ban reason       |
| Ban reason    | Причина блокування | Why an administrator set a ban. A separate list: [`BanReason`](./architecture/models.md#banreason).                                           | Report reason    |
| Ban           | Блокування         | A restriction set by an administrator with a ban reason, until lifted. Rules: [PRD 6.1](./prd.md#61-accounts), [PRD 6.10](./prd.md#610-bans). | Telegram block   |
| Lift          | Зняти блокування   | Ending a ban by an administrator.                                                                                                             | "unban" in specs |
