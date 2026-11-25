import secrets
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import pytest
from app.modules.approvals.models import Approval
from app.modules.approvals.domain import ApprovalRequest, Decision
from app.core.problem import Problem
from test_requisitions import draft


def reviewer(client, h, slug):
    data = dict(
        email="review@" + slug + ".test",
        name="Reviewer",
        role="department_manager",
        password=secrets.token_urlsafe(16),
    )
    m = client.post("/api/v1/members", headers=h, json=data)
    assert m.status_code == 201, m.text
    result = client.post(
        "/api/v1/auth/login",
        json={**{k: data[k] for k in ("email", "password")}, "organization": slug},
    )
    return m.json()["id"], {"Authorization": "Bearer " + result.json()["access_token"]}


def pending(client, workspace):
    h, _ = workspace()
    rid, review = reviewer(client, h, "north")
    req = client.post("/api/v1/requisitions", headers=h, json=draft(client, h)).json()
    path = "/api/v1/requisitions/" + req["id"]
    submit = dict(version=req["version"], approver_id=rid)
    res = client.post(path + "/submit", headers=h, json=submit)
    assert res.status_code == 200, res.text
    assert client.post(path + "/submit", headers=h, json=submit).status_code == 409
    approval = client.get("/api/v1/approvals", headers=review).json()["items"][0]
    return h, review, res.json(), approval


@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_decision_history(client, workspace, outcome):
    h, review, req, a = pending(client, workspace)
    path = "/api/v1/approvals/" + a["id"] + "/decision"
    data = dict(version=a["version"], decision=outcome, comment="Budget review")
    assert client.post(path, headers=h, json=data).status_code == 403
    assert client.post(path, headers=review, json=data).status_code == 200
    assert client.post(path, headers=review, json=data).status_code == 409
    with Session(client.app.state.engine) as db:
        row = db.get(Approval, a["id"])
        assert row.status == row.requisition.status == outcome
        assert row.decided_at and row.requisition.history[-1].comment == "Budget review"
        assert [e.event for e in row.requisition.history] == [
            "created",
            "submitted",
            "pending_approval",
            outcome,
        ]
        assert db.scalar(select(func.count()).select_from(Approval)) == 1


def test_cancel_then_decide(client, workspace):
    h, review, req, a = pending(client, workspace)
    assert (
        client.post(
            "/api/v1/requisitions/" + req["id"] + "/cancel",
            headers=h,
            json={"version": req["version"]},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/approvals/" + a["id"] + "/decision",
            headers=review,
            json=dict(version=1, decision="approved"),
        ).status_code
        == 409
    )
    with Session(client.app.state.engine) as db:
        row = db.get(Approval, a["id"])
        assert (
            row.requisition.status == row.status == "cancelled"
            and row.decided_at is None
        )


def test_decision_rule():
    with pytest.raises(Problem):
        ApprovalRequest("me", "me", "pending").decide("me", Decision.APPROVE, "")
    with pytest.raises(Problem):
        ApprovalRequest("me", "other", "pending").decide("me", Decision.REJECT, " ")


def test_competing_decisions(client, workspace):
    _, review, req, a = pending(client, workspace)
    barrier = Barrier(2)

    def act(decision):
        barrier.wait()
        return client.post(
            "/api/v1/approvals/" + a["id"] + "/decision",
            headers=review,
            json=dict(
                version=a["version"], decision=decision, comment="Concurrent review"
            ),
        ).status_code

    with ThreadPoolExecutor(2) as pool:
        codes = list(pool.map(act, ["approved", "rejected"]))
    assert sorted(codes) == [200, 409]
    with Session(client.app.state.engine) as db:
        row = db.get(Approval, a["id"])
        assert (
            row.requisition.status == row.status and len(row.requisition.history) == 4
        )
