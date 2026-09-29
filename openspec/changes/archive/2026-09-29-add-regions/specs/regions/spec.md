# Spec Delta

## Purpose

Lets the bot offer the two-step city choice: first a region of Ukraine, then a city in that region, from the official
KATOTTH list.

## ADDED Requirements

### Requirement: Listing regions

`GET /regions` SHALL return the regions as a paginated list sorted by `name` in ascending order by default. Each item
SHALL have `id`, `katotth_code`, `name`, `name_en` and `code_type` (`O` for an oblast or the Autonomous Republic of
Crimea, `K` for Kyiv and Sevastopol).

#### Scenario: All regions on one page

- **WHEN** `GET /regions` is called with `page_size=100`
- **THEN** the response is 200 and lists every region, sorted by name

#### Scenario: Region fields

- **WHEN** a region is listed
- **THEN** it has `id`, `katotth_code`, `name`, `name_en` and `code_type`

### Requirement: Listing the cities of a region

`GET /regions/{region_id}/cities` SHALL return only the cities of that region as a paginated list sorted by `name` in
ascending order by default. Each item SHALL have `id`, `region_id`, `katotth_code`, `name` and `name_en`. An unknown
`region_id` SHALL return 404 `NOT_FOUND`. For Kyiv and Sevastopol the list SHALL contain exactly one city: the city
itself.

#### Scenario: Cities of a region

- **WHEN** the cities of a region are listed
- **THEN** every item has that region's `region_id` and the items are sorted by name

#### Scenario: City with special status

- **WHEN** the cities of Kyiv are listed
- **THEN** the list has exactly one city, Kyiv

#### Scenario: Unknown region

- **WHEN** the cities of a region ID that does not exist are listed
- **THEN** the response is 404 with `code` `NOT_FOUND`

### Requirement: Regions and cities data file

The repository SHALL contain `data/regions/katotth_<YYYY-MM-DD>.json`, where the date is the KATOTTH edition. It SHALL
be a JSON list of regions; each region SHALL have exactly `katotth_code`, `name`, `name_en`, `code_type` and `cities`,
and each city exactly `katotth_code`, `name` and `name_en`. Every value SHALL satisfy the database rules of the
corresponding column, codes SHALL be `UA` followed by 17 digits and unique within regions and within cities, and each
region of type `K` SHALL have exactly one city with the region's own name.

#### Scenario: File matches the models

- **WHEN** the data file is read
- **THEN** every region and city has exactly the model's fields, and every value fits its column

#### Scenario: Region with special status

- **WHEN** the Kyiv region in the data file is read
- **THEN** it has `code_type` `K` and one city named `Київ`
