from pathlib import Path

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DatabaseSettings(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="magicvibe")
    username: str = Field(default="postgres")
    password: SecretStr = Field(default_factory=lambda: SecretStr("postgres"))
    echo: bool = False


class AuthSettings(BaseModel):
    service_token: SecretStr


class Settings(BaseSettings):
    debug: bool = False
    auth: AuthSettings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
