from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import DB, Reader, Requester
from app.core.schemas import Page, Paging
from . import repository, service
from .schemas import Summary, Detail, Draft, Edit
from .domain import State

router = APIRouter(prefix="/requisitions", tags=["Requisitions"])


@router.get("", response_model=Page[Summary])
def listing(
    db: DB,
    actor: Reader,
    paging: Annotated[Paging, Depends()],
    status: State | None = None,
):
    return repository.listing(db, actor.tenant, paging, status)


@router.get("/{identifier}", response_model=Detail)
def read(identifier: str, db: DB, actor: Reader):
    return repository.get(db, actor.tenant, identifier)


@router.post("", response_model=Detail, status_code=201)
def create(data: Draft, db: DB, actor: Requester):
    return service.create(db, actor, data)


@router.put("/{identifier}", response_model=Detail)
def edit(identifier: str, data: Edit, db: DB, actor: Requester):
    return service.edit(db, actor, identifier, data)
