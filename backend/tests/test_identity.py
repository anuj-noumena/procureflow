from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.identity.models import Membership
from app.modules.identity.domain import Actor, Role
from app.core.errors import Problem
import pytest


def test_login_and_membership(client, workspace):
    headers, data = workspace()
    login = {k: data[k] for k in ("email", "password", "organization")}
    assert client.post("/api/v1/auth/login", json=login).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/login", json={**login, "organization": "unknown"}
        ).status_code
        == 401
    )
    assert (
        client.get("/api/v1/auth/me", headers=headers).json()["role"]
        == "organization_admin"
    )
    with Session(client.app.state.engine) as db:
        member = db.scalar(select(Membership))
        member.active = False
        db.commit()
    assert client.get("/api/v1/organization", headers=headers).status_code == 401


def test_permissions():
    with pytest.raises(Problem):
        Actor("tenant", "member", Role.REQUESTER).require("approval.decide")
