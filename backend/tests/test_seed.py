import secrets
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import pytest
from app import seed
from app.modules.organizations.models import Organization
from app.modules.identity.models import Membership
from app.modules.requisitions.models import RequestRecord
from app.modules.approvals.models import Approval


def test_seed_is_repeatable(client, monkeypatch):
    password = secrets.token_urlsafe(16)
    monkeypatch.setenv("PF_JWT_SECRET", secrets.token_hex(32))
    monkeypatch.setenv("PF_ENV", "development")
    monkeypatch.setenv("PF_SEED_PASSWORD", password)
    seed.main()
    seed.main()
    with Session(client.app.state.engine) as db:
        for model, expected in [
            (Organization, 2),
            (Membership, 10),
            (RequestRecord, 10),
            (Approval, 6),
        ]:
            assert db.scalar(select(func.count()).select_from(model)) == expected
        for req in db.scalars(select(RequestRecord)):
            assert req.estimated_total == sum(line.line_total for line in req.lines)
    auth = client.post(
        "/api/v1/auth/login",
        json=dict(
            organization="northline",
            email="reviewer@northline.example",
            password=password,
        ),
    )
    assert auth.status_code == 200
    inbox = client.get(
        "/api/v1/approvals",
        headers={"Authorization": "Bearer " + auth.json()["access_token"]},
    ).json()
    assert (
        inbox["total"] == 1
        and inbox["items"][0]["requisition"]["number"] == "PR-2026-0002"
    )
    monkeypatch.setenv("PF_ENV", "production")
    with pytest.raises(SystemExit):
        seed.main()
