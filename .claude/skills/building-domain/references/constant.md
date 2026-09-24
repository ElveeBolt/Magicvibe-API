# Constant

`constants.py` — `UPPER_CASE` values hardcoded in the rules of this
domain (limits, quotas, page sizes). A value that differs per environment belongs
in settings; a fixed set of choices belongs in `enums.py`.

```python                                                                                                                                                                                                                              
MAX_QUOTES_PER_USER = 100
DEFAULT_PAGE_SIZE = 20                                                                                                                                                                                                                 
```

Import them in `services.py` (`from .constants import MAX_QUOTES_PER_USER`), never
in `router.py` — a limit is a business rule, so only the service enforces it.

If the domain has no such value, do not create the file — an empty
`constants.py` is a placeholder, and placeholders are a violation.