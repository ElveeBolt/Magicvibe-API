# Spec Delta

## MODIFIED Requirements

### Requirement: Validation errors

A request that does not pass the request schema (body, query, path or header) SHALL be rejected, including a
partial update (`PATCH`) body with a field its schema does not define. It SHALL be rejected with 400
`VALIDATION_ERROR` and an `errors` list with one entry per problem. Each entry SHALL have `field` (the dot-separated
path to the value inside its request part, without the part name such as `body` or `query`; empty when the problem
concerns the whole object), `type` (the machine-readable error type, such as `string_too_long`,
`greater_than_equal`, `extra_forbidden`, `missing`) and `message`.

#### Scenario: Field too long

- **WHEN** a request body has a string field longer than its maximum
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with that field's name and
  `type` `string_too_long`

#### Scenario: Unknown field

- **WHEN** a request body has a field the schema does not define
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with that field's name and
  `type` `extra_forbidden`

#### Scenario: Invalid query parameter

- **WHEN** a list endpoint is called with `page_size=101`
- **THEN** the response is 400 with `code` `VALIDATION_ERROR` and an `errors` entry with `field` `page_size`

#### Scenario: Nested field

- **WHEN** a request body has an invalid value in a nested object
- **THEN** the `errors` entry's `field` joins the path with dots, for example `telegram.first_name`

#### Scenario: Unknown field in a partial update

- **WHEN** a `PATCH` body has a field the schema does not define next to a valid one
- **THEN** the response is 400 with `code` `VALIDATION_ERROR`, an `errors` entry with that field's name and `type`
  `extra_forbidden`, and nothing is changed
