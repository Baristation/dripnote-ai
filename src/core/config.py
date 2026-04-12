from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "dripnote-ai"
    app_env: str = "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    vectorstore_dir: str = "./data/vectorstore"
    train_device: str = "cpu"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def vectorstore_path(self) -> Path:
        return Path(self.vectorstore_dir)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
