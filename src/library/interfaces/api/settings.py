from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiUser(BaseModel):
    login: str
    permissions: list[str]


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    API_HOST: str
    API_PORT: int
    USERS: list[ApiUser] = Field(default_factory=list[ApiUser])
