import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_mem"
    hf_home: str = ".cache/models"
    mem_api_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
# Convert to absolute path if relative
hf_home_path = Path(settings.hf_home)
if not hf_home_path.is_absolute():
    hf_home_path = (Path(__file__).parent.parent / hf_home_path).resolve()
os.environ["HF_HOME"] = str(hf_home_path)
