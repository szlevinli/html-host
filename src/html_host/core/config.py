from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    admin_password: str
    jwt_secret: str
    jwt_expire_days: int = 7
    base_url: str
    upload_dir: str
    db_path: str
    max_file_size_mb: int = 2


settings = Settings()
