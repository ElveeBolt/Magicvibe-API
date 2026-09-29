# Versioning and releases

How the MagicVibe API is versioned, how compatibility with the bot works and how releases happen. Versioning visible in
the API itself (no version in URLs, `info.version` in OpenAPI) is part of the API contract.

## Version number

- The API version is the package version in `pyproject.toml`, in [SemVer](https://semver.org/) format
  `MAJOR.MINOR.PATCH`.
- It is set **only** by python-semantic-release in GitHub Actions.
- **Nobody changes the version manually** — not in code, `pyproject.toml`, tags or anywhere else.
- The version in OpenAPI is read from package metadata (`importlib.metadata.version`), never hard-coded.

## Compatibility with the bot

**API major version N works with bot major version N.** API 1.x.x works with bot 1.x.x.

The major version changes only for a **breaking change** — a change after which the current bot stops working with the
API.

| Breaking (major)                                                    | Not breaking (minor / patch)             |
|---------------------------------------------------------------------|------------------------------------------|
| Removing or renaming an endpoint, request field or response field   | New endpoint                             |
| Changing a field's type, format or the meaning of a value           | New optional request field               |
| Making an optional request field required, or adding a required one | New response field                       |
| Removing or renaming an error code or enum value                    | New enum value the bot can safely ignore |
| Changing authentication                                             | Bug fix                                  |

Error codes and their fields are listed in [Errors](../architecture/errors.md).

If you are not sure whether a change is breaking, treat it as breaking and ask.

### Before 1.0.0

While the version is 0.x, the API contract may still change freely and breaking changes do not bump the major version.
The move to 1.0.0 is decided by the owner. From 1.0.0 on, the table above applies.

## Commits

Commits follow [Conventional Commits](https://www.conventionalcommits.org/). The commit type decides the next version,
so choose it carefully.

| Commit                                                   | Version bump | Example                                          |
|----------------------------------------------------------|--------------|--------------------------------------------------|
| `feat:`                                                  | minor        | `feat(reaction): add superlike daily limit`      |
| `fix:`, `perf:`                                          | patch        | `fix(ban): set user status to active on lift`    |
| `feat!:` or a `BREAKING CHANGE:` footer                  | major        | `feat(reaction)!: rename is_super to super_like` |
| `docs:`, `refactor:`, `chore:`, `ci:`, `style:`, `test:` | none         | `docs: add glossary`                             |

- The format is checked locally by the **commitizen** `commit-msg` hook in **pre-commit**.
- A commit that fails the hook is fixed, never bypassed. `--no-verify` is forbidden.
- Commitizen only checks messages; it is never used for bumping.

## Releases

Releases are fully automatic. On push to the main branch, the GitHub Actions workflow runs python-semantic-release,
which:

1. calculates the next version from commit messages since the last release;
2. updates the version in `pyproject.toml` and the changelog;
3. creates the git tag and the GitHub release.

Nobody runs a release, a bump or creates tags locally.

## Rules

- Never change the version number manually.
- Never run `cz bump` or `semantic-release` locally, never create tags.
- Never edit the release workflow or the changelog unless explicitly asked.
- After 1.0.0, never make a breaking change without the owner's approval, and flag any change that might be breaking.