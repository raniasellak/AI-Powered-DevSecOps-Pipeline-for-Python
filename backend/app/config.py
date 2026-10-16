from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret_key: str
    database_url: str = "sqlite:///./dev.db"
    access_token_expire_minutes: int = 15
    jwt_algorithm: str = "HS256"
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()