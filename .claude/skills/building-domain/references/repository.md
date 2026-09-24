# Repository

`repositories.py` — one class per aggregate, parameterised by model and primary key type:

```python
class EntityRepository(AlchemyRepository[Entity, int]):
    model = Entity
```