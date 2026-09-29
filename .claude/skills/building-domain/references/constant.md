# Constant

`constants.py` — `UPPER_CASE` values hardcoded in the rules of this
domain (limits, quotas, page sizes). A value that differs per environment belongs
in settings; a fixed set of choices belongs in `enums.py`.

```python
MAX_ENTITIES_PER_USER = 100
MAX_ENTITY_TEXT_LENGTH = 500
```

Import them in `services.py` (`from .constants import MAX_ENTITIES_PER_USER`) or in
`schemas/types.py` for length limits, never in `router.py` — a limit is a business
rule. Page size is not a domain constant: pagination comes from the shared filter
schema in `core`.

If the domain has no such value, do not create the file — an empty
`constants.py` is a placeholder, and placeholders are a violation.