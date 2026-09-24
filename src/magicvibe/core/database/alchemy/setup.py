from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ....settings import settings

url = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.database.username,
    password=settings.database.password.get_secret_value(),
    host=settings.database.host,
    port=settings.database.port,
    database=settings.database.name,
)


engine = create_async_engine(url=url, echo=settings.database.echo)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
