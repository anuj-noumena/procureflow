from enum import StrEnum
from app.core.problem import Problem


class SupplierStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


def normalized_name(value: str) -> str:
    key = " ".join(value.casefold().split())
    if not key:
        raise Problem(422, "A supplier needs a legal name.")
    return key


def require_active(status: str):
    if status != SupplierStatus.ACTIVE:
        raise Problem(409, "The selected supplier must be active.")
