# Regions data

Regions and cities come from the official **KATOTTH** codifier (КАТОТТГ) of administrative-territorial units of Ukraine.
What users see is described in [PRD → Region and city](../prd.md#63-region-and-city).

## What is stored

Two tables (see [Data model](./models.md#region-domain)):

- `regions` — oblasts, the Autonomous Republic of Crimea, Kyiv and Sevastopol;
- `cities` — all cities, each linked to its region. Kyiv and Sevastopol are also stored as a city of their own region.

Villages, settlements and city districts are not stored. Names are in Ukrainian, as in KATOTTH.

## Files

```
data/regions/                   # in the repository root
├── katotth_<YYYY-MM-DD>.json   # list of regions and cities
└── load.py                     # loads the list into the database; run manually
```

- **`katotth_<YYYY-MM-DD>.json`** — regions and cities taken from KATOTTH. The date in the name is the date of the
  KATOTTH edition the list was built from, so it shows how current the data is.
- **`load.py`** — reads the JSON file and adds new regions and cities to the `regions` and `cities` tables. It never
  deletes or disables a region or city. A developer runs it manually when needed. Migrations never call it. *Not
  written yet.*

## File format

A JSON list of regions, each with its cities nested. The field names are the column names of the models; there is no
`id` and no `region_id`, the loader takes them from the nesting:

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

Regions follow the order of the codifier; the cities of a region are sorted by `katotth_code`. The file is UTF-8 with
two-space indents, so a new edition diffs line by line.

## Building the file from KATOTTH

The source is the codifier xlsx published by the Ministry (the page "Кодифікатор адміністративно-територіальних
одиниць та територій територіальних громад"). From its sheet:

- **Region** — every row with category (`Категорія об’єкта`) `O` or `K`. `katotth_code` is the first-level code,
  `name` is `Назва об’єкта`, `code_type` is the category.
- **City** — every row with category `M`. `katotth_code` is the deepest non-empty level code; the region is the row's
  first-level code.
- **Kyiv and Sevastopol** (`K`) also get themselves as the only city of their region, with the region's code, name and
  `name_en`.
- **`name_en`** — the codifier has no English names, so it is the transliteration of `name` by Resolution of the
  Cabinet of Ministers of Ukraine No. 55 of 27.01.2010: `г` → `h`, `ґ` → `g`, `зг` → `zgh`, `є`/`ї`/`й`/`ю`/`я` →
  `ye`/`yi`/`y`/`yu`/`ya` at the start of a word and `ie`/`i`/`i`/`iu`/`ia` elsewhere, `ь` and apostrophes are
  dropped, capital letters and hyphens are kept.

The current file, `katotth_2026-07-07.json`, is built from the edition of 7 July 2026: 27 regions and 463 cities.

City data is never invented or typed by hand; it always comes from the official KATOTTH file. The only exception is
the test database: test factories create made-up regions and cities there (see [Testing](./testing.md)).

## Keeping the data current

There is no automatic update and no fixed schedule. When needed, a developer checks whether a newer KATOTTH edition has
been published and compares its date with the date in the file name. If there is a newer edition, the developer
prepares a new `katotth_<YYYY-MM-DD>.json` from it and runs `load.py` manually.