# Router

`router.py` — the handler parses, calls the service, returns a schema:

```python
router = APIRouter(prefix="/messages", tags=["message"])


@router.post("/", response_model=EntityReadSchema, status_code=status.HTTP_201_CREATED)
async def create_entity(service: EntityServiceDep, data: EntityCreateSchema):
    return await service.create(data=data)
```