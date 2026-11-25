from typing import Annotated, Literal
from pydantic import StringConstraints
from app.core.schemas import Input, Label, Notes, Price, Currency


class CatalogData(Input):
    code: Annotated[str, StringConstraints(min_length=1, max_length=64, to_upper=True)]
    kind: Literal["product", "service"]
    name: Label
    description: Notes = ""
    category: Label
    unit: Label
    reference_price: Price
    currency: Currency


class CatalogView(CatalogData):
    id: str
