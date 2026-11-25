from decimal import Decimal as D
import pytest
from app.core.problem import Problem
from app.modules.identity.domain import Actor, Role
from app.modules.requisitions.domain import Estimate, estimated_total
from app.modules.suppliers.domain import normalized_name


@pytest.mark.parametrize(
    "quantity,price,tax",
    [
        ("0", "1", "0"),
        ("1", "-1", "0"),
        ("1", "1", "101"),
        ("0.0001", "1", "0"),
        ("1", "1.001", "0"),
        ("1", "Infinity", "0"),
    ],
)
def test_invalid_estimate(quantity, price, tax):
    with pytest.raises(Problem):
        Estimate(D(quantity), D(price), D(tax))


def test_aggregate_total_limit():
    line = Estimate(D("100000"), D("6000000.00"), D("0"))
    with pytest.raises(Problem):
        estimated_total([line, line])


def test_request_owner_and_supplier_rules():
    requester = Actor("tenant", "m1", Role.REQUESTER)
    requester.may_change("m1")
    with pytest.raises(Problem):
        requester.may_change("m2")
    with pytest.raises(Problem):
        normalized_name("  ")
