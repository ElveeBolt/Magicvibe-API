# Proposal

## Why

[PRD → Region and city](../../../docs/prd.md#63-region-and-city) has users choose a region, then a city in it, from
the official KATOTTH list; [Data model → `region` domain](../../../docs/architecture/models.md#region-domain) defines
`regions` and `cities`, and [Regions data](../../../docs/architecture/region_data.md) a data file in `data/regions/`.
None of it exists, and the profile's `city_id` (next change, `complete-profile-fields`) needs the `cities` table.

## What Changes

- New `region` domain: `Region` (`regions`) and `RegionCity` (`cities`) models with the `RegionCodeType` enum (`O`,
  `K`), as in `models.md`; repositories registered in the unit of work.
- Read-only endpoints for the two-step choice: `GET /regions` and `GET /regions/{region_id}/cities`, both paginated
  and sorted by name.
- `data/regions/katotth_2026-07-07.json`: the regions and cities of the KATOTTH edition of 7 July 2026, taken from the
  official file of the Ministry
  (`https://mindev.gov.ua/storage/app/sites/1/uploaded-files/kodifikator-07-07.xlsx`), as a JSON list of regions with
  their cities nested, using the column names of the models: 27 regions (25 of category `O`, Kyiv and Sevastopol of
  category `K`) and 463 cities (the 461 cities of category `M` plus Kyiv and Sevastopol as the one city of their
  region). Nothing is typed by hand.
- `name_en`: the official codifier has no English names, so `name_en` is the Latin transliteration of `name` by the
  official Ukrainian rules (Resolution of the Cabinet of Ministers of Ukraine No. 55 of 27 January 2010) — for example
  `Черкаська` → `Cherkaska`, `Кам’янське` → `Kamianske`. `models.md` says "English, as in KATOTTH"; that wording is
  corrected first.
- Not in this change: `data/regions/load.py`. The owner writes the loader; this change only provides the data file
  and the schema. Until then the tables stay empty outside tests.
- A migration (autogenerate) creating both tables and the enum type.

## Capabilities

### New Capabilities

- `regions`: listing regions and the cities of a region for the two-step city choice.

### Modified Capabilities

None.

## Impact

- Code: new `src/magicvibe/region/`, `uow.py`, `router.py`, `alembic/env.py` (model imports), a new migration.
- Data: new `data/regions/katotth_2026-07-07.json` (repository root).
- Tests: `tests/region/` (router, services, models, and a check of the data file against the model rules); factories
  for made-up regions and cities.
- Docs: `models.md` (`name_en` is a transliteration), `region_data.md` (file format, how it is built from the official
  file, transliteration rule, `load.py` not written yet), `CLAUDE.md` "Known drift" (no `load.py` yet).
