from typing import Annotated, Generic, TypeVar, Literal
from decimal import Decimal
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

Label = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


def exact_price(value):
    if isinstance(value, float):
        raise ValueError("Send decimal amounts as strings.")
    return value


Price = Annotated[
    Decimal,
    BeforeValidator(exact_price),
    Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False),
]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


class Paging(Input):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    q: str = Field("", max_length=200)
    sort: Literal["newest", "oldest"] = "newest"
