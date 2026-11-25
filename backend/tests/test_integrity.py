import secrets
from datetime import datetime, timezone, timedelta
import jwt
import pytest
from sqlalchemy import select, func, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from app.modules.approvals.models import Approval
from app.modules.requisitions.models import RequestRecord
from app.modules.catalog.models import CatalogItem
from app.core.problem import Problem
from test_approvals import reviewer
from test_requisitions import draft


def test_migration_round_trip(client):
    cfg = Config("alembic.ini")
    command.check(cfg)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    command.check(cfg)
    assert client.get("/docs").status_code == 200
    assert (
        "/api/v1/approvals/{identifier}/decision"
        in client.get("/openapi.json").json()["paths"]
    )


def test_enrollment_and_tenant_selection(client, workspace):
    a, alice = workspace()
    b, _ = workspace("south")
    res = client.post(
        "/api/v1/members/enroll",
        headers=b,
        json=dict(email=alice["email"], role="requester"),
    )
    assert res.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        json=dict(
            email=alice["email"], password=alice["password"], organization="south"
        ),
    ).json()["access_token"]
    h = {"Authorization": "Bearer " + token}
    assert (
        client.get("/api/v1/auth/me", headers=h).json()["organization_name"] == "South"
    )
    assert client.get("/api/v1/members", headers=h).status_code == 403
    assert client.get("/api/v1/approvals", headers=h).status_code == 403
    assert client.get("/api/v1/members", headers=a).status_code == 200
    res = client.put(
        "/api/v1/members/" + res.json()["id"],
        headers=b,
        json=dict(role="requester", active=False),
    )
    assert res.status_code == 200
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    assert client.get("/api/v1/auth/me", headers=a).status_code == 200


def test_token_checks(client, workspace):
    h, _ = workspace()
    token = h["Authorization"].split()[1]
    key = client.app.state.settings.jwt_secret
    data = jwt.decode(token, key, algorithms=["HS256"], issuer="procureflow")
    data["exp"] = datetime.now(timezone.utc) - timedelta(seconds=2)
    for invalid in [
        jwt.encode(data, key, algorithm="HS256"),
        jwt.encode(data, secrets.token_hex(32), algorithm="HS256"),
    ]:
        assert (
            client.get(
                "/api/v1/auth/me", headers={"Authorization": "Bearer " + invalid}
            ).status_code
            == 401
        )
    assert client.get("/api/v1/organization").status_code == 401


def test_database_refuses_cross_tenant_reference(client, workspace):
    a, _ = workspace()
    b, _ = workspace("south")
    payload = draft(client, a)
    req = client.post("/api/v1/requisitions", headers=a, json=payload).json()
    other = draft(client, b)["department_id"]
    with Session(client.app.state.engine) as db:
        row = db.get(RequestRecord, req["id"])
        row.department_id = other
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert row.department_id == payload["department_id"]


def test_inactive_supplier_and_invalid_assignment(client, workspace):
    a, _ = workspace()
    b, _ = workspace("south")
    actor = client.get("/api/v1/auth/me", headers=a).json()
    vendor = {"name": "Supplier", "category": "Tools", "status": "active"}
    v = client.post("/api/v1/suppliers", headers=a, json=vendor).json()["id"]
    body = {**draft(client, a), "supplier_id": v}
    assert (
        client.post(
            "/api/v1/requisitions",
            headers=b,
            json={**draft(client, b), "supplier_id": v},
        ).status_code
        == 404
    )
    req = client.post("/api/v1/requisitions", headers=a, json=body).json()
    path = "/api/v1/requisitions/" + req["id"] + "/submit"
    assert (
        client.post(
            path, headers=a, json=dict(version=1, approver_id=actor["id"])
        ).status_code
        == 422
    )
    other = client.get("/api/v1/auth/me", headers=b).json()["id"]
    assert (
        client.post(
            path, headers=a, json=dict(version=1, approver_id=other)
        ).status_code
        == 404
    )
    client.put(
        "/api/v1/suppliers/" + v, headers=a, json={**vendor, "status": "suspended"}
    )
    reviewer_id, _ = reviewer(client, a, "north")
    assert (
        client.post(
            path, headers=a, json=dict(version=1, approver_id=reviewer_id)
        ).status_code
        == 409
    )
    with Session(client.app.state.engine) as db:
        assert db.get(RequestRecord, req["id"]).status == "draft"
        assert db.scalar(select(func.count()).select_from(Approval)) == 0


def test_rollback_after_flushed_writes(client, workspace):
    a, _ = workspace()
    reviewer_id, _ = reviewer(client, a, "north")
    req = client.post("/api/v1/requisitions", headers=a, json=draft(client, a)).json()

    def fail_after_flush(session, context):
        if any(isinstance(record, Approval) for record in session.new):
            raise Problem(409, "Injected failure after database writes.")

    event.listen(Session, "after_flush", fail_after_flush)
    try:
        response = client.post(
            "/api/v1/requisitions/" + req["id"] + "/submit",
            headers=a,
            json=dict(version=1, approver_id=reviewer_id),
        )
    finally:
        event.remove(Session, "after_flush", fail_after_flush)
    assert response.status_code == 409 and "Injected" in response.text
    with Session(client.app.state.engine) as db:
        stored = db.get(RequestRecord, req["id"])
        assert (
            stored.status == "draft"
            and stored.version == 1
            and len(stored.history) == 1
        )
        assert db.scalar(select(func.count()).select_from(Approval)) == 0


def test_catalog_and_tenant_reference(client, workspace):
    a, _ = workspace()
    b, _ = workspace("south")
    data = dict(
        code="svc",
        name="Design",
        category="Services",
        kind="service",
        unit="hour",
        currency="EUR",
        reference_price="80.10",
    )
    item = client.post("/api/v1/catalog", headers=a, json=data)
    assert item.status_code == 201, item.text
    path = "/api/v1/catalog/" + item.json()["id"]
    assert (
        client.put(
            path, headers=a, json={**data, "reference_price": "85.20"}
        ).status_code
        == 200
    )
    assert client.get(path, headers=b).status_code == 404
    assert (
        client.get("/api/v1/catalog?q=svc&kind=service", headers=a).json()["total"] == 1
    )
    payload = draft(client, b)
    payload["lines"][0]["catalog_item_id"] = item.json()["id"]
    assert (
        client.post("/api/v1/requisitions", headers=b, json=payload).status_code == 404
    )
    with Session(client.app.state.engine) as db:
        assert str(db.get(CatalogItem, item.json()["id"]).reference_price) == "85.20"


def test_reject_extra_tenant_or_derived_fields(client, workspace):
    h, _ = workspace()
    payload = draft(client, h)
    for extra in [
        {"organization_id": "foreign"},
        {"estimated_total": "0.01"},
        {"status": "approved"},
    ]:
        assert (
            client.post(
                "/api/v1/requisitions", headers=h, json={**payload, **extra}
            ).status_code
            == 422
        )
    assert (
        client.post(
            "/api/v1/requisitions",
            headers=h,
            json={**payload, "lines": [{**payload["lines"][0], "unit_price": 0.1}]},
        ).status_code
        == 422
    )
    with Session(client.app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(RequestRecord)) == 0
