# Regions data

Regions and cities come from the official **KATOTTH** codifier (КАТОТТГ) of administrative-territorial units of Ukraine.
What users see is described in the [`regions` spec](../../openspec/specs/regions/spec.md).

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
  deletes or disables a region or city. A developer runs it manually when needed. Migrations never call it.

City data is never invented or typed by hand; it always comes from the official KATOTTH file.

## Keeping the data current

There is no automatic update and no fixed schedule. When needed, a developer checks whether a newer KATOTTH edition has
been published and compares its date with the date in the file name. If there is a newer edition, the developer
prepares a new `katotth_<YYYY-MM-DD>.json` from it and runs `load.py` manually.