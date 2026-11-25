from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import DB, Reader, Writer
from app.core.persistence import scoped
from app.core.schemas import Page, Paging
from .models import Supplier
from .schemas import SupplierView, SupplierData
from .domain import SupplierStatus
from . import service

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=Page[SupplierView])
def listing(
    db: DB,
    actor: Reader,
    paging: Annotated[Paging, Depends()],
    status: SupplierStatus | None = None,
):
    return service.listing(db, actor.tenant, paging, status)


@router.get("/{identifier}", response_model=SupplierView)
def read(identifier: str, db: DB, actor: Reader):
    return scoped(db, Supplier, actor.tenant, identifier)


@router.post("", response_model=SupplierView, status_code=201)
def create(data: SupplierData, db: DB, actor: Writer):
    return service.save(db, actor.tenant, data)


@router.put("/{identifier}", response_model=SupplierView)
def edit(identifier: str, data: SupplierData, db: DB, actor: Writer):
    return service.save(db, actor.tenant, data, identifier)
