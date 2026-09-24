# Dependency

`dependencies.py` — assemble the service here so the router carries no
construction logic.

```python
async def get_entity_service(uow: UOWDep) -> EntityService:
    return EntityService(uow)


EntityServiceDep = Annotated[EntityService, Depends(get_entity_service)]
```