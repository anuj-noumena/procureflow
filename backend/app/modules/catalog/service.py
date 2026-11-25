from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.persistence import scoped, paginate
from app.core.schemas import Paging
from .models import CatalogItem
from .schemas import CatalogData


def save(
    db: Session, tenant: str, data: CatalogData, identifier: str | None = None
) -> CatalogItem:
    item = (
        scoped(db, CatalogItem, tenant, identifier)
        if identifier
        else CatalogItem(organization_id=tenant)
    )
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.add(item)
    db.flush()
    return item


def listing(db: Session, tenant: str, paging: Paging, kind: str | None):
    query = select(CatalogItem).where(CatalogItem.organization_id == tenant)
    if paging.q:
        query = query.where(
            or_(
                CatalogItem.name.icontains(paging.q, autoescape=True),
                CatalogItem.code.icontains(paging.q, autoescape=True),
            )
        )
    if kind:
        query = query.where(CatalogItem.kind == kind)
    return paginate(db, query, CatalogItem, paging)
