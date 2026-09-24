# Schema

`schemas/` is built in dependency order. Each file exists only when needed:

1. `schemas/validators.py`: only if a field needs a check that `Field(...)` or
   `StringConstraints(...)` cannot express;
2. `schemas/types.py`: only if a constraint repeats across schemas or a
   validator has to be attached;
3. `schemas/<entity>.py`: always, for every entity.

## Entity schemas Validators

`schemas/validators.py`: plain functions, one value in, the same value
(possibly normalised) out, or `ValueError`.

```python
def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())
```

## Entity schemas Types

`schemas/types.py`: `Annotated` aliases that combine a base type, its
constraints and validators. Limits by business logic come from `constants.py`.

```python
EntityText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_ENTITY_TEXT_LENGTH),
    AfterValidator(collapse_whitespace),
]
```

- Types only: no `BaseModel` subclasses.
- Imports `validators.py` and `constants.py`, never an entity schema.
- Markers and types shared by several domains (`NonNullable`, `BaseSchema`,
  `BaseFilterSchema`) live in `core`, not here.

## Entity schemas

`schemas/<entity>.py`: Pydantic v2, all four schemas. Input schemas use types
from `types.py`; output and filter schemas use plain types.

```python
class EntityCreateSchema(BaseSchema):
    text: EntityText
```

```python
class EntityUpdateSchema(BaseSchema):
    text: Annotated[EntityText | None, NonNullable] = None
```

```python
class EntityReadSchema(BaseSchema):
    id: int
    text: str
```

```python
class EntityFilterSchema(BaseFilterSchema):
    text: str | None = None
```