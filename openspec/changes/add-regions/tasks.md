# Tasks

## 1. Docs first

- [ ] 1.1 `docs/architecture/models.md`: `name_en` of `regions` and `cities` is the Latin transliteration of `name`
  (Resolution of the Cabinet of Ministers of Ukraine No. 55 of 27.01.2010), since KATOTTH has no English names;
  verify neither table says "English, as in KATOTTH"
- [ ] 1.2 `docs/architecture/region_data.md`: the JSON format (regions with nested cities, model field names), how it
  is built from the official xlsx (categories `O`/`K`/`M`, which code is taken, Kyiv and Sevastopol as their own
  city), the transliteration rule, and that `load.py` is not written yet; `CLAUDE.md` "Known drift" gets "no
  `data/regions/load.py` yet"; verify both documents say so

## 2. Data file

- [ ] 2.1 Add `data/regions/katotth_2026-07-07.json` built from the official 07.07.2026 codifier by the rules of 1.2;
  verify 27 regions and 463 cities, and `Черкаська` / `Черкаси` have the codes `UA71000000000010357` /
  `UA71080490010015879`

## 3. Region domain

- [ ] 3.1 `region/enums.py` (`RegionCodeType`), `region/models/region.py` (`Region`), `region/models/region_city.py`
  (`RegionCity`), `region/constants.py` (name and code lengths); register the models in `alembic/env.py`; verify mypy
- [ ] 3.2 Generate the migration with autogenerate on a throwaway `postgres:18.6` container; verify it creates
  `regions`, `cities`, `region_code_type_enum` and `ix_cities_region_id`, and the test session applies it
- [ ] 3.3 Repositories, `RegionService` with `list_cities`, schemas (`RegionReadSchema`, `RegionCityReadSchema`, filter
  schemas with `order_by` `name` and `order` `asc`), router, dependencies; register in `uow.py` and `router.py`;
  verify `app.openapi()` lists `/regions` and `/regions/{region_id}/cities`
- [ ] 3.4 `tests/factories.py`: `create_region`, `create_city`; `tests/region/test_router.py` and `test_services.py`
  for every `regions` endpoint scenario; `tests/region/test_models.py` for the unique codes and the foreign key;
  verify `uv run --no-sync pytest tests/region` passes
- [ ] 3.5 `tests/region/test_data.py`: the data file scenarios (exact fields, column lengths, code format, unique
  codes, `code_type` values, one city for each `K` region); verify it passes

## 4. Integration checks

- [ ] 4.1 Run `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run mypy src/magicvibe` and `npx openspec validate add-regions --strict`; all exit 0
