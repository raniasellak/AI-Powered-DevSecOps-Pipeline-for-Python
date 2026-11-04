from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret_key: str
    database_url: str = "sqlite:///./dev.db"
    access_token_expire_minutes: int = 15
    jwt_algorithm: str = "HS256"
    refresh_token_expire_days: int = 7
    # Liste fermee : jamais "*" (front Flutter web en local par defaut)
    cors_origins: list[str] = ["http://localhost:5000"]

    # extra="ignore" : .env contient aussi des variables pour docker-compose
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()