# Service

`services.py` — for CRUD, implement `AbstractService` so the five operations
keep the same names across every domain. One async with per business operation:

```python
class EntityService(
    AbstractService[
        EntityCreateSchema,
        EntityUpdateSchema,
        EntityReadSchema,
        EntityFilterSchema,
        int
    ]
):
    schema = EntityReadSchema
    uow: UnitOfWork

    @property
    def repository(self) -> EntityRepository:  # type: ignore[override]
        return self.uow.message
```

How the UoW exposes its repositories comes from the reference domain — copy it
rather than inventing an attribute name. For a non-CRUD domain, skip service.