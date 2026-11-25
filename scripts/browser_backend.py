"""Run a fresh SQLite workspace for Playwright, independent of local dev data."""

import os
import secrets
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import uvicorn
from alembic import command
from alembic.config import Config

backend = Path(__file__).resolve().parents[1] / "backend"
os.chdir(backend)
sys.path.insert(0, str(backend))
from app.seed import main as seed
from app.main import create_app

if __name__ == "__main__":
    with TemporaryDirectory(prefix="pf-browser-") as directory:
        os.environ.update(
            PF_DATABASE_URL="sqlite:///" + directory + "/test.db",
            PF_ENV="development",
            PF_JWT_SECRET=secrets.token_hex(32),
            PF_SEED_PASSWORD=os.environ["PF_E2E_PASSWORD"],
        )
        command.upgrade(Config("alembic.ini"), "head")
        seed()
        uvicorn.run(create_app(), host="127.0.0.1", port=8187, log_level="warning")
