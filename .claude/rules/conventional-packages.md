# Conventional Packages Rules

All dependencies are managed exclusively through `uv`. Never edit the
`dependencies` / `[dependency-groups]` sections of `pyproject.toml` by hand —
always use `uv add` / `uv remove`, so `uv.lock` stays in sync.

## Adding dependencies

Always use the correct dependency group:

- **Production** packages (used at runtime): `uv add <package>`
- **Test** packages (pytest, httpx, etc.): `uv add --group test <package>`
- **Lint/typing** packages (ruff, mypy, etc.): `uv add --group lint <package>`

Note: `dev` is configured in this project's `pyproject.toml` as a meta-group
that includes `test` and `lint` via PEP 735 `include-group`. Never add
packages to `dev` directly — always target the specific group (`test` or
`lint`) so packages stay sorted by purpose.

Before adding a package, check it isn't already present in another group
(e.g. `uv tree` or grep `pyproject.toml`) to avoid duplicate entries.

Do not pin exact versions (`package==x.y.z`) unless explicitly requested;
let `uv add` resolve the latest compatible version.

## Removing dependencies

- `uv remove <package>` for production dependencies
- `uv remove --group <group> <package>` for a specific group

## Lockfile

`uv add` and `uv remove` update `uv.lock` automatically — don't run
`uv lock` separately after them. Only run `uv lock` explicitly if
dependencies were changed some other way (e.g. a manual edit that had to
happen for a reason outside normal `add`/`remove` flow).