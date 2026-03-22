from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Hunting with AI"
    database_url: str = "sqlite:///./hunting_with_ai.db"
    api_prefix: str = "/api"
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    project_root: Path = Path(__file__).resolve().parents[3]

    @property
    def frontend_dist(self) -> Path:
        return self.project_root / "frontend" / "dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
