"""
Конфігурація застосунку через змінні середовища.

Поглиблений рівень: замість того, щоб хардкодити MODEL_NAME та інші
параметри константами в main.py, вони виносяться в об'єкт налаштувань,
який читає значення зі змінних середовища (з префіксом OK11_) або
з файлу .env. Це узгоджується з принципом конфігурації через середовище
(https://12factor.net/uk/config) — стандартною практикою продакшн-сервісів.

Приклад використання:
    OK11_MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english uvicorn app.main:app

Документація pydantic-settings:
https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OK11_",
        env_file=".env",
        extra="ignore"
    )

    model_name: str = (
        "distilbert-base-uncased-finetuned-sst-2-english"
    )

    max_batch_size: int = 50

    log_level: str = "INFO"

    slow_request_ms: float = 100.0
