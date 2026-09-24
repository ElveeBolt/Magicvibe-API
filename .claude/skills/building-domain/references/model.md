# Model

**`models/<entity>.py`** — `Base` already provides `id` and the naming
convention; do not redeclare either.

```python
class Entity(Base):
    __tablename__ = "entities"

    text: Mapped[str] = mapped_column(String(500))
```

Then list the model in `models/__init__.py`. Alembic autogenerate and the UoW see
only what is listed there, and the failure when it is missing is silent.