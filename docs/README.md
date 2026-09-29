# Documentation

Product and architecture documentation of the MagicVibe API. Start with the PRD for what the product does, then the
architecture documents for how the code is built.

## Product

| Document                   | What it holds                                                              |
|----------------------------|----------------------------------------------------------------------------|
| [PRD](./prd.md)            | Why MagicVibe exists, who it is for, scope and the business rules          |
| [Plans](./plans.md)        | Free and premium plans, daily limits, how premium is granted               |
| [Glossary](./glossary.md)  | One meaning per term, the words to avoid and the Ukrainian bot wording     |

## Architecture

| Document                                              | What it holds                                                        |
|-------------------------------------------------------|----------------------------------------------------------------------|
| [Conventions](./architecture/conventions.md)          | Package and domain structure, layers, models, schemas, API style     |
| [Data model](./architecture/models.md)                | Every table, constraint and enum                                     |
| [Errors](./architecture/errors.md)                    | Error response body, error codes and their HTTP statuses             |
| [Testing](./architecture/testing.md)                  | How the API is tested: database, layout, what each test covers       |
| [Non-functional requirements](./architecture/nfr.md)  | Performance, integrity, privacy, logging and other quality rules     |
| [Plan constants](./architecture/plan_constants.md)    | How the plans are implemented in code                                |
| [Regions data](./architecture/region_data.md)         | Where regions and cities come from and how they are loaded           |

## Process

| Document                                   | What it holds                                                  |
|--------------------------------------------|----------------------------------------------------------------|
| [Versioning](./process/versioning.md)      | Version numbers, compatibility with the bot, commits, releases |
