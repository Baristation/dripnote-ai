from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "dripnote-ai"
    app_env: str = "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    train_device: str = "cpu"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "baristation-products"
    qdrant_vector_size: int = 1536
    qdrant_top_k: int = 5
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_key_prefix: str = "dripnote-ai"
    backend_mysql_host: str = "localhost"
    backend_mysql_port: int = 8005
    backend_mysql_database: str = "baristation"
    backend_mysql_user: str = "ai_readonly"
    backend_mysql_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
