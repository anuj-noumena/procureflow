from typing import Annotated
from pydantic import Field, StringConstraints
from app.core.schemas import Input, Label
from app.modules.identity.schemas import Email
from .domain import SupplierStatus


class Contact(Input):
    name: Label
    email: Email
    phone: str = Field(default="", max_length=50)


class SupplierData(Input):
    name: Label
    category: Label
    tax_id: (
        Annotated[str, StringConstraints(min_length=1, max_length=64, to_upper=True)]
        | None
    ) = None
    contacts: list[Contact] = Field(default_factory=list, max_length=20)
    addresses: list[Label] = Field(default_factory=list, max_length=20)
    status: SupplierStatus = SupplierStatus.DRAFT


class SupplierView(SupplierData):
    id: str
