import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    origins: list[str]
    environment: str

    @classmethod
    def load(cls):
        key = os.environ.get("PF_JWT_SECRET", "")
        if len(key.encode()) < 32 or key.startswith("<"):
            raise RuntimeError(
                "Set PF_JWT_SECRET to a random secret of at least 32 bytes."
            )
        return cls(
            os.getenv("PF_DATABASE_URL", "sqlite:///./procureflow.db"),
            key,
            os.getenv("PF_CORS_ORIGINS", "http://localhost:5173").split(","),
            os.getenv("PF_ENV", "development"),
        )
