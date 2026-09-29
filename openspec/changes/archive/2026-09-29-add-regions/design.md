# Design

## Context

- `models.md` defines `regions` (`katotth_code` unique `string(19)`, `name` and `name_en` `string(100)`, `code_type`
  enum `RegionCodeType`) and `cities` (`region_id` → `regions.id` with no `ON DELETE` action, index on `region_id`), in
  `region/models/region.py` and `region/models/region_city.py`. Neither table has timestamps.
- The official codifier is an xlsx sheet with the columns "Перший рівень … Додатковий рівень", "Категорія об’єкта" and
  "Назва об’єкта". Categories used here: `O` (oblast / ARC, first level), `K` (Kyiv, Sevastopol, first level), `M`
  (city, fourth level). The edition of 07.07.2026 has 25 `O`, 2 `K`, 461 `M`; no `M` lies under a `K`.
- `BaseFilterSchema.order` defaults to `desc`.

## Goals / Non-Goals

**Goals:**

- A data file anyone can re-create from the official xlsx with the rules written in `region_data.md`.
- Endpoints the bot can use for the two-step choice without extra requests (every region fits in one page of 100).

**Non-Goals:**

- `data/regions/load.py` (the owner writes it) and the xlsx converter (a one-off; the rules are documented instead).
- Search by text, villages, districts (out of scope in the PRD).

## Decisions

### JSON shape: regions with nested cities, model field names

```json
[
  {
    "katotth_code": "UA71000000000010357",
    "name": "Черкаська",
    "name_en": "Cherkaska",
    "code_type": "O",
    "cities": [
      {"katotth_code": "UA71080490010015879", "name": "Черкаси", "name_en": "Cherkasy"}
    ]
  }
]
```

Regions in codifier order, cities sorted by `katotth_code`. No `id` and no `region_id`: the loader assigns them from
the nesting. The file is written with `ensure_ascii=False` and two-space indents, so a new edition diffs line by line.

### How the file is built from the codifier

- Region: every row with category `O` or `K`; `katotth_code` is the first-level code, `name` the object name.
- City: every row with category `M`; `katotth_code` is the deepest non-empty level code; its region is the row's
  first-level code.
- Kyiv and Sevastopol (`K`) also get themselves as their only city, with the region's code, name and `name_en`
  (`cities.katotth_code` is unique within `cities` only, so reusing the region code is allowed).
- `name_en`: transliteration by Resolution No. 55 — `г`→`h`, `ґ`→`g`, `зг`→`zgh`, `є/ї/й/ю/я` → `ye/yi/y/yu/ya` at
  the start of a word and `ie/i/i/iu/ia` elsewhere, `ь` and apostrophes dropped, capitalization and hyphens kept.

### Endpoints

`RegionFilterSchema` and `RegionCityFilterSchema` fix `order_by` to `Literal["name"]` and default `order` to `asc`.
`RegionService` is an `AlchemyService` over `RegionRepository`; `list_cities(region_id, filters)` checks that the
region exists (404 `NOT_FOUND`) and lists `RegionCityRepository` rows filtered by `region_id`. Both routes sit under
`/regions` and need no acting user, like the other lookup routes.

### Tests use made-up data

`tests/factories.py` gets `create_region` and `create_city` with made-up codes (`region_data.md` allows made-up
regions and cities in the test database). The real data file is checked by a separate test that reads the JSON and
validates it against the model column rules — it needs no database.

## Risks / Trade-offs

- [`name_en` is a transliteration, not an official English name (e.g. `Kyiv` matches, but a traditional exonym would
  not)] → the rule is official and deterministic; the bot speaks Ukrainian only, so `name_en` is for logs and
  possible other clients.
- [No loader yet, so a fresh environment has empty `regions` / `cities`] → documented in `CLAUDE.md` "Known drift";
  profiles with a city (next change) cannot be created there until the owner loads the data.
