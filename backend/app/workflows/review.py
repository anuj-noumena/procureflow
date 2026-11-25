"""Coordinate the requisition and approval aggregates in the caller's transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import now
from app.core.persistence import scoped
from app.core.problem import Problem
from app.modules.identity.domain import Actor, PERMISSIONS
from app.modules.identity.models import Membership
from app.modules.requisitions import repository
from app.modules.requisitions.domain import Requisition, State
from app.modules.requisitions.service import record_event, validate_supplier
from app.modules.approvals.models import Approval
from app.modules.approvals.domain import ApprovalRequest, Decision
from app.modules.approvals.schemas import Submit, Decide


def submit(db: Session, actor: Actor, identifier: str, data: Submit):
    req = repository.get(db, actor.tenant, identifier, data.version)
    actor.may_change(req.requester_id)
    pending = Requisition(State(req.status)).submit(len(req.lines))
    validate_supplier(db, actor.tenant, req.supplier_id)
    reviewer = scoped(db, Membership, actor.tenant, data.approver_id)
    if (
        reviewer.id in {req.requester_id, actor.member}
        or not reviewer.active
        or not reviewer.user.active
        or "approval.decide" not in PERMISSIONS[reviewer.role]
    ):
        raise Problem(422, "Choose an active independent approver.")
    record_event(req, actor, "submitted")
    req.status = pending
    record_event(req, actor, "pending_approval")
    db.add(
        Approval(
            organization_id=actor.tenant, requisition_id=req.id, approver_id=reviewer.id
        )
    )
    db.flush()
    return req


def cancel(db: Session, actor: Actor, identifier: str, version: int):
    req = repository.get(db, actor.tenant, identifier, version)
    actor.may_change(req.requester_id)
    cancelled = Requisition(State(req.status)).cancel()
    if req.status == State.PENDING:
        approval = db.scalars(
            select(Approval).where(
                Approval.organization_id == actor.tenant,
                Approval.requisition_id == req.id,
            )
        ).one()
        approval.status = "cancelled"
    record_event(req, actor, "cancelled")
    req.status = cancelled
    db.flush()
    return req


def decide(db: Session, actor: Actor, identifier: str, data: Decide):
    actor.require("approval.decide")
    approval = scoped(db, Approval, actor.tenant, identifier)
    req = approval.requisition
    domain = ApprovalRequest(approval.approver_id, req.requester_id, approval.status)
    outcome = domain.decide(actor.member, data.decision, data.comment)
    if approval.version != data.version:
        raise Problem(409, "Approval changed. Refresh and retry.")
    state = Requisition(State(req.status)).decide(data.decision == Decision.APPROVE)
    record_event(req, actor, outcome, data.comment)
    req.status = state
    approval.status, approval.comment, approval.decided_at = (
        outcome,
        data.comment,
        now(),
    )
    db.flush()
    return approval
