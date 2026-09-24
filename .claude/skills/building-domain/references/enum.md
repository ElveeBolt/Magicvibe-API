# Enum

`enums.py` — a fixed set of values shared by the model and the schemas,
so neither side owns the vocabulary. Subclass `StrEnum` so the value is stored
and serialized as its string.

```python                                                                                                                                                                                                                              
class EntityStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"                                                                                                                                                                                                            
```