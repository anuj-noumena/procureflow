from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from app.core.dependencies import DB, Requester, Approver
from app.core.persistence import scoped, paginate
from app.core.schemas import Page, Paging
from app.core.problem import Problem
from app.modules.requisitions.models import RequestRecord
from app.modules.requisitions.schemas import Version, Detail
from app.workflows import review
from .models import Approval
from .schemas import Submit, Decide, ApprovalView

router = APIRouter(tags=["Approvals"])


@router.post("/requisitions/{identifier}/submit", response_model=Detail)
def submit(identifier: str, data: Submit, db: DB, actor: Requester):
    return review.submit(db, actor, identifier, data)


@router.post("/requisitions/{identifier}/cancel", response_model=Detail)
def cancel(identifier: str, data: Version, db: DB, actor: Requester):
    return review.cancel(db, actor, identifier, data.version)


@router.get("/approvals", response_model=Page[ApprovalView])
def inbox(
    db: DB,
    actor: Approver,
    paging: Annotated[Paging, Depends()],
    status: Literal["pending", "approved", "rejected", "cancelled"] | None = "pending",
):
    query = (
        select(Approval)
        .join(Approval.requisition)
        .where(
            Approval.organization_id == actor.tenant,
            Approval.approver_id == actor.member,
        )
    )
    if status:
        query = query.where(Approval.status == status)
    if paging.q:
        query = query.where(
            or_(
                RequestRecord.description.icontains(paging.q, autoescape=True),
                RequestRecord.number.icontains(paging.q, autoescape=True),
            )
        )
    return paginate(db, query, Approval, paging)


@router.get("/approvals/{identifier}", response_model=ApprovalView)
def read(identifier: str, db: DB, actor: Approver):
    row = scoped(db, Approval, actor.tenant, identifier)
    if row.approver_id != actor.member:
        raise Problem(403, "This approval belongs to another reviewer.")
    return row


@router.post("/approvals/{identifier}/decision", response_model=ApprovalView)
def decide(identifier: str, data: Decide, db: DB, actor: Approver):
    return review.decide(db, actor, identifier, data)
