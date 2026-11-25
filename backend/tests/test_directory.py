from sqlalchemy.orm import Session
from sqlalchemy import select, func
import pytest
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.domain import normalized_name, require_active
from app.core.problem import Problem


def test_supplier_rules():
    assert normalized_name("  APEX   Tools ") == "apex tools"
    for status in ["draft", "inactive", "suspended"]:
        with pytest.raises(Problem):
            require_active(status)


def test_supplier_scope_and_duplicate(client, workspace):
    a, _ = workspace()
    b, _ = workspace("south")
    url = "/api/v1/suppliers"
    data = dict(name="Apex Tools", category="Hardware", status="active", tax_id="ax21")
    r = client.post(url, json=data, headers=a)
    assert r.status_code == 201, r.text
    path = url + "/" + r.json()["id"]
    assert (
        client.post(
            url, json={**data, "name": "APEX  TOOLS", "tax_id": None}, headers=a
        ).status_code
        == 409
    )
    assert client.get(path, headers=b).status_code == 404
    assert client.put(path, json=data, headers=b).status_code == 404
    assert client.get(url, headers=b).json()["total"] == 0
    assert client.post(url, json=data, headers=b).status_code == 201
    assert (
        client.put(path, headers=a, json={**data, "status": "inactive"}).status_code
        == 200
    )
    assert (
        client.get(url + "?q=pex&status=inactive&size=1", headers=a).json()["total"]
        == 1
    )
    with Session(client.app.state.engine) as db:
        assert db.get(Supplier, r.json()["id"]).status == "inactive"
        assert db.scalar(select(func.count()).select_from(Supplier)) == 2
