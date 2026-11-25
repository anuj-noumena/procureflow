from decimal import Decimal as D
from sqlalchemy.orm import Session
import pytest
from app.modules.requisitions.domain import (
    Requisition,
    Estimate,
    estimated_total,
    State,
)
from app.modules.requisitions.models import RequestRecord
from app.core.problem import Problem


def test_exact_rounding_per_line():
    line = Estimate(D("0.50"), D("0.01"), D("0"))
    assert line.total == D("0.01")
    assert estimated_total([line, line]) == D("0.02")


@pytest.mark.parametrize(
    "state", [State.APPROVED, State.REJECTED, State.CANCELLED, State.PENDING]
)
def test_only_draft_can_edit_or_submit(state):
    with pytest.raises(Problem):
        Requisition(state).editable()
    with pytest.raises(Problem):
        Requisition(state).submit(1)


def test_transitions():
    assert Requisition(State.PENDING).decide(False) == State.REJECTED
    assert Requisition(State.DRAFT).cancel() == State.CANCELLED
    with pytest.raises(Problem):
        Requisition(State.CANCELLED).decide(True)
    with pytest.raises(Problem):
        Requisition(State.DRAFT).submit(0)


def draft(client, h):
    department = client.get("/api/v1/organization", headers=h).json()["departments"][0][
        "id"
    ]
    return dict(
        department_id=department,
        description="Hardware refresh",
        currency="USD",
        required_date="2027-02-01",
        lines=[
            dict(
                description="Brackets",
                unit="pair",
                quantity="3.500",
                unit_price="12.10",
                tax_percent="8.25",
            )
        ],
    )


def test_draft_atomic_edit(client, workspace):
    a, _ = workspace()
    b, _ = workspace("south")
    payload = draft(client, a)
    url = "/api/v1/requisitions"
    r = client.post(url, headers=a, json=payload)
    assert r.status_code == 201, r.text
    obj = r.json()
    assert obj["estimated_total"] == "45.84"
    path = url + "/" + obj["id"]
    assert client.get(path, headers=b).status_code == 404
    assert client.post(url, headers=b, json=payload).status_code == 404
    edit = {**payload, "version": obj["version"]}
    invalid = {
        **edit,
        "lines": [
            *payload["lines"],
            {**payload["lines"][0], "catalog_item_id": "missing"},
        ],
    }
    assert client.put(path, headers=a, json=invalid).status_code == 404
    assert (
        client.put(
            path,
            headers=a,
            json={**edit, "lines": [{**payload["lines"][0], "quantity": 0}]},
        ).status_code
        == 422
    )
    with Session(client.app.state.engine) as db:
        stored = db.get(RequestRecord, obj["id"])
        assert (
            stored.version == 1 and len(stored.lines) == 1 and len(stored.history) == 1
        )
    assert (
        client.put(path, headers=a, json={**edit, "lines": []}).json()[
            "estimated_total"
        ]
        == "0.00"
    )
    assert client.put(path, headers=a, json=edit).status_code == 409
