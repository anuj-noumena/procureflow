from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.approvals.models import Approval
from app.modules.requisitions.models import RequestRecord
from test_approvals import reviewer, pending
from test_requisitions import draft


def simultaneous(*actions):
    gate = Barrier(len(actions))

    def run(action):
        gate.wait()
        return action().status_code

    with ThreadPoolExecutor(len(actions)) as pool:
        return list(pool.map(run, actions))


def test_concurrent_submissions(client, workspace):
    headers, _ = workspace()
    assigned, _ = reviewer(client, headers, "north")
    req = client.post(
        "/api/v1/requisitions", headers=headers, json=draft(client, headers)
    ).json()

    def submit():
        return client.post(
            "/api/v1/requisitions/" + req["id"] + "/submit",
            headers=headers,
            json=dict(version=req["version"], approver_id=assigned),
        )

    assert sorted(simultaneous(submit, submit)) == [200, 409]
    with Session(client.app.state.engine) as db:
        row = db.get(RequestRecord, req["id"])
        assert [e.event for e in row.history] == [
            "created",
            "submitted",
            "pending_approval",
        ]
        assert db.scalar(select(func.count()).select_from(Approval)) == 1


def test_cancellation_racing_decision(client, workspace):
    headers, review, req, a = pending(client, workspace)

    def cancel():
        return client.post(
            "/api/v1/requisitions/" + req["id"] + "/cancel",
            headers=headers,
            json=dict(version=req["version"]),
        )

    def decide():
        return client.post(
            "/api/v1/approvals/" + a["id"] + "/decision",
            headers=review,
            json=dict(version=a["version"], decision="approved"),
        )

    assert sorted(simultaneous(cancel, decide)) == [200, 409]
    with Session(client.app.state.engine) as db:
        row = db.get(Approval, a["id"])
        assert row.status in {"approved", "cancelled"}
        assert row.status == row.requisition.status == row.requisition.history[-1].event
        assert len(row.requisition.history) == 4
