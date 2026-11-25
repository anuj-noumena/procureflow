from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from app.core.problem import Problem

CENT = Decimal("0.01")
MAX_TOTAL = Decimal("999999999999.99")


class State(StrEnum):
    DRAFT = "draft"
    PENDING = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Estimate:
    quantity: Decimal
    unit_price: Decimal
    tax_percent: Decimal

    def __post_init__(self):
        for value, maximum, places in [
            (self.quantity, Decimal("999999.999"), 3),
            (self.unit_price, Decimal("99999999.99"), 2),
            (self.tax_percent, Decimal("100"), 2),
        ]:
            if (
                not isinstance(value, Decimal)
                or not value.is_finite()
                or value < 0
                or value > maximum
                or value != value.quantize(Decimal(1).scaleb(-places))
            ):
                raise Problem(
                    422, "Line quantity, price or tax is outside its supported range."
                )
        if not self.quantity:
            raise Problem(422, "Quantity must be positive.")

    @property
    def total(self) -> Decimal:
        amount = (
            self.quantity * self.unit_price * (1 + self.tax_percent / 100)
        ).quantize(CENT, rounding=ROUND_HALF_UP)
        if amount > MAX_TOTAL:
            raise Problem(422, "Line total exceeds the supported maximum.")
        return amount


@dataclass(frozen=True)
class Requisition:
    status: State

    def editable(self):
        if self.status != State.DRAFT:
            raise Problem(409, "Only draft requisitions can be edited.")

    def submit(self, count: int) -> State:
        self.editable()
        if count < 1:
            raise Problem(422, "Add a line before submitting.")
        return State.PENDING

    def cancel(self) -> State:
        if self.status not in {State.DRAFT, State.PENDING}:
            raise Problem(409, "This requisition cannot be cancelled.")
        return State.CANCELLED

    def decide(self, approved: bool) -> State:
        if self.status != State.PENDING:
            raise Problem(409, "This requisition is no longer awaiting approval.")
        return State.APPROVED if approved else State.REJECTED


def estimated_total(lines: list[Estimate]) -> Decimal:
    amount = sum((line.total for line in lines), Decimal("0.00"))
    if amount > MAX_TOTAL:
        raise Problem(422, "Requisition total exceeds the supported maximum.")
    return amount
