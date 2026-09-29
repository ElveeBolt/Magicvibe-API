# Spec Delta

## Purpose

Defines the query parameters shared by every paginated list endpoint of the API, starting with the allowed range of
the page size.

## ADDED Requirements

### Requirement: Page size range

Every paginated list endpoint SHALL accept a `page_size` query parameter from 1 to 100 inclusive. When `page_size` is
omitted, the endpoint SHALL use 10. A `page_size` outside that range SHALL be rejected as an invalid request, and no
items SHALL be returned. The status and body of that rejection are those of a request validation error.

#### Scenario: Largest allowed page size

- **WHEN** a list endpoint is called with `page_size=100`
- **THEN** the request succeeds and the response has `page_size` 100 and at most 100 items

#### Scenario: Page size above the limit

- **WHEN** a list endpoint is called with `page_size=101`
- **THEN** the request is rejected as a validation error on `page_size` and no items are returned

#### Scenario: Page size below the limit

- **WHEN** a list endpoint is called with `page_size=0`
- **THEN** the request is rejected as a validation error on `page_size` and no items are returned

#### Scenario: Page size omitted

- **WHEN** a list endpoint is called without `page_size`
- **THEN** the request succeeds and the response has `page_size` 10
