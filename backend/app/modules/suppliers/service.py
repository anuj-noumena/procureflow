from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.persistence import scoped, paginate
from app.core.schemas import Paging
from .models import Supplier
from .domain import normalized_name, SupplierStatus
from .schemas import SupplierData


def save(db: Session, tenant: str, data: SupplierData, identifier: str | None = None):
    supplier = (
        scoped(db, Supplier, tenant, identifier)
        if identifier
        else Supplier(organization_id=tenant)
    )
    supplier.name, supplier.name_key = data.name, normalized_name(data.name)
    supplier.tax_id, supplier.status, supplier.category = (
        data.tax_id,
        data.status,
        data.category,
    )
    supplier.contacts = [c.model_dump() for c in data.contacts]
    supplier.addresses = data.addresses
    db.add(supplier)
    db.flush()
    return supplier


def listing(db: Session, tenant: str, paging: Paging, status: SupplierStatus | None):
    query = select(Supplier).where(Supplier.organization_id == tenant)
    if paging.q:
        query = query.where(
            or_(
                Supplier.name.icontains(paging.q, autoescape=True),
                Supplier.category.icontains(paging.q, autoescape=True),
            )
        )
    if status:
        query = query.where(Supplier.status == status)
    return paginate(db, query, Supplier, paging)
