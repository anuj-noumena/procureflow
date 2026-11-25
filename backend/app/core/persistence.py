from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.errors import Problem
from app.core.schemas import Paging


def scoped(db: Session, model, tenant: str, identifier: str):
    record = db.scalar(
        select(model).where(model.organization_id == tenant, model.id == identifier)
    )
    if record is None:
        raise Problem(404, "Record not found.")
    return record


def paginate(db: Session, query, model, paging: Paging):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    order = (
        model.created_at.desc() if paging.sort == "newest" else model.created_at.asc()
    )
    rows = db.scalars(
        query.order_by(order, model.id)
        .offset((paging.page - 1) * paging.size)
        .limit(paging.size)
    ).all()
    return {"items": rows, "total": total}
