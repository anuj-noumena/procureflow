from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.persistence import scoped, paginate
from app.core.schemas import Paging
from app.core.problem import Problem
from .domain import State
from .models import RequestRecord


def get(
    db: Session, tenant: str, identifier: str, version: int | None = None
) -> RequestRecord:
    record = scoped(db, RequestRecord, tenant, identifier)
    if version is not None and version != record.version:
        raise Problem(409, "The requisition changed. Refresh and retry.")
    return record


def listing(db: Session, tenant: str, paging: Paging, status: State | None):
    query = select(RequestRecord).where(RequestRecord.organization_id == tenant)
    if status:
        query = query.where(RequestRecord.status == status)
    if paging.q:
        query = query.where(
            or_(
                RequestRecord.description.icontains(paging.q, autoescape=True),
                RequestRecord.number.icontains(paging.q, autoescape=True),
            )
        )
    return paginate(db, query, RequestRecord, paging)
