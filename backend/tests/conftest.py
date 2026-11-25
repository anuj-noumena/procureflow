import os
import secrets
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_url(tmp_path):
    pg = os.getenv("PF_TEST_POSTGRES_URL")
    if not pg:
        yield "sqlite:///" + str(tmp_path / "test.db")
        return
    base = make_url(pg)
    if base.drivername != "postgresql+psycopg":
        raise ValueError("Use a test PostgreSQL URL with the psycopg driver.")
    schema = "pf_test_" + uuid4().hex
    engine = create_engine(base)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE SCHEMA " + schema)
    try:
        yield base.update_query_dict(
            {"options": "-csearch_path=" + schema}
        ).render_as_string(hide_password=False)
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP SCHEMA " + schema + " CASCADE")
        engine.dispose()


@pytest.fixture
def client(test_url, monkeypatch):
    monkeypatch.setenv("PF_DATABASE_URL", test_url)
    command.upgrade(Config("alembic.ini"), "head")
    app = create_app(Settings(test_url, secrets.token_hex(32), [], "test"))
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


@pytest.fixture
def workspace(client):
    def make(slug="north"):
        data = dict(
            organization=slug,
            organization_name=slug.title(),
            name="Test Admin",
            email=f"admin@{slug}.test",
            password=secrets.token_urlsafe(16),
        )
        res = client.post("/api/v1/auth/register", json=data)
        assert res.status_code == 201, res.text
        headers = {"Authorization": "Bearer " + res.json()["access_token"]}
        return headers, data

    return make
