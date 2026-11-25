from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from app.core.dependencies import DB, Reader, Writer
from app.core.persistence import scoped
from app.core.schemas import Page, Paging
from .models import CatalogItem
from .schemas import CatalogData, CatalogView
from . import service

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("", response_model=Page[CatalogView])
def listing(
    db: DB,
    actor: Reader,
    paging: Annotated[Paging, Depends()],
    kind: Literal["product", "service"] | None = None,
):
    return service.listing(db, actor.tenant, paging, kind)


@router.get("/{identifier}", response_model=CatalogView)
def read(identifier: str, db: DB, actor: Reader):
    return scoped(db, CatalogItem, actor.tenant, identifier)


@router.post("", response_model=CatalogView, status_code=201)
def create(data: CatalogData, db: DB, actor: Writer):
    return service.save(db, actor.tenant, data)


@router.put("/{identifier}", response_model=CatalogView)
def edit(identifier: str, data: CatalogData, db: DB, actor: Writer):
    return service.save(db, actor.tenant, data, identifier)
