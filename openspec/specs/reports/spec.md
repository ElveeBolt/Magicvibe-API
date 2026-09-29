# reports Specification

## Purpose

Defines how a user files a report against another user and how an administrator reviews it; a report never hides
anyone and never fails for the reporter except for reporting oneself.

## Requirements

### Requirement: Filing a report

`POST /reports` SHALL create a report from the acting user against `target_id` with a `reason` and an optional
`comment`, with status `open`, and return 201. When the acting user already has an open report against the same
target, it SHALL NOT create another one and SHALL return 200 with the existing open report. Reporting a banned user
SHALL succeed. Reporting oneself SHALL return 400 `SELF_ACTION`. An unknown `target_id` SHALL return 404 `NOT_FOUND`.

#### Scenario: First report

- **WHEN** the acting user reports another user
- **THEN** the response is 201 with a report whose `status` is `open`

#### Scenario: Repeated report while open

- **WHEN** the acting user reports the same user again while their first report is open
- **THEN** the response is 200 with the first report and only one open report from them against that user exists

#### Scenario: Report after review

- **WHEN** the acting user reports a user again after their earlier report was resolved
- **THEN** the response is 201 with a new open report

#### Scenario: Reporting a banned user

- **WHEN** the acting user reports a banned user
- **THEN** the response is 201

#### Scenario: Reporting oneself

- **WHEN** the acting user reports their own user ID
- **THEN** the response is 400 with `code` `SELF_ACTION`

#### Scenario: Unknown target

- **WHEN** the acting user reports a user ID no account has
- **THEN** the response is 404 with `code` `NOT_FOUND`

#### Scenario: Simultaneous repeated reports

- **WHEN** the same acting user sends two reports against the same user at the same time
- **THEN** both succeed and exactly one open report from them against that user exists

### Requirement: Reviewing a report

`PATCH /reports/{report_id}` SHALL set the status of a report to `resolved` or `dismissed`. Any other status value
SHALL be rejected with 400 `VALIDATION_ERROR`. An unknown `report_id` SHALL return 404 `NOT_FOUND`.

#### Scenario: Resolve a report

- **WHEN** an open report is patched with `status` `resolved`
- **THEN** the response is 200 with `status` `resolved`

#### Scenario: Reopen a report

- **WHEN** a report is patched with `status` `open`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`
