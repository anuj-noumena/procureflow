from datetime import date, datetime
from decimal import Decimal
from pydantic import Field, field_validator
from app.core.schemas import Input, Output, Label, Price, Currency
from .domain import State


class LineInput(Input):
    description: Label
    catalog_item_id: str | None = None
    quantity: Decimal = Field(gt=0, max_digits=9, decimal_places=3, allow_inf_nan=False)
    unit: Label
    unit_price: Price
    tax_percent: Decimal = Field(
        default=Decimal("0"), ge=0, le=100, decimal_places=2, allow_inf_nan=False
    )

    @field_validator("quantity", "tax_percent", mode="before")
    @classmethod
    def exact_decimal(cls, value):
        if isinstance(value, float):
            raise ValueError("Send decimal amounts as strings.")
        return value


class Draft(Input):
    department_id: str
    description: Label
    required_date: date
    currency: Currency
    supplier_id: str | None = None
    lines: list[LineInput] = Field(max_length=100)


class Version(Input):
    version: int = Field(ge=1)


class Edit(Draft, Version):
    pass


class LineView(LineInput):
    id: str
    line_total: Decimal


class EventView(Output):
    event: str
    actor_name: str
    actor_id: str
    sequence: int
    comment: str
    created_at: datetime


class Summary(Output):
    id: str
    number: str
    requester_name: str
    requester_id: str
    department_id: str
    supplier_id: str | None
    description: str
    required_date: date
    currency: str
    estimated_total: Decimal
    status: State
    version: int
    created_at: datetime
    modified_at: datetime


class Detail(Summary):
    lines: list[LineView]
    history: list[EventView]
