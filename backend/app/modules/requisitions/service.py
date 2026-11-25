from sqlalchemy.orm import Session
from app.core.db import now, uid
from app.core.persistence import scoped
from app.modules.catalog.models import CatalogItem
from app.modules.identity.domain import Actor
from app.modules.organizations.models import Department
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.domain import require_active
from .domain import Requisition, Estimate, State, estimated_total
from .models import RequestRecord, LineRecord, History
from .repository import get
from .schemas import Draft, Edit


def record_event(record: RequestRecord, actor: Actor, event: str, comment: str = ""):
    record.history.append(
        History(
            organization_id=actor.tenant,
            actor_id=actor.member,
            event=event,
            comment=comment,
            sequence=len(record.history) + 1,
        )
    )
    record.modified_at = now()


def validate_supplier(db: Session, tenant: str, identifier: str | None):
    if identifier:
        require_active(scoped(db, Supplier, tenant, identifier).status)


def apply_draft(db: Session, record: RequestRecord, data: Draft):
    tenant = record.organization_id
    scoped(db, Department, tenant, data.department_id)
    validate_supplier(db, tenant, data.supplier_id)
    estimates = []
    lines = []
    for index, line in enumerate(data.lines):
        if line.catalog_item_id:
            scoped(db, CatalogItem, tenant, line.catalog_item_id)
        estimate = Estimate(line.quantity, line.unit_price, line.tax_percent)
        estimates.append(estimate)
        lines.append(
            LineRecord(
                **line.model_dump(),
                organization_id=tenant,
                position=index + 1,
                line_total=estimate.total,
            )
        )
    record.estimated_total = estimated_total(estimates)
    record.description, record.currency, record.required_date = (
        data.description,
        data.currency,
        data.required_date,
    )
    record.department_id, record.supplier_id, record.lines = (
        data.department_id,
        data.supplier_id,
        lines,
    )


def create(db: Session, actor: Actor, data: Draft):
    actor.require("requisition.write")
    record = RequestRecord(
        organization_id=actor.tenant,
        requester_id=actor.member,
        number="PR-" + uid()[:13].upper(),
        status=State.DRAFT,
    )
    apply_draft(db, record, data)
    record_event(record, actor, "created")
    db.add(record)
    db.flush()
    return record


def edit(db: Session, actor: Actor, identifier: str, data: Edit):
    record = get(db, actor.tenant, identifier, data.version)
    actor.may_change(record.requester_id)
    Requisition(State(record.status)).editable()
    apply_draft(db, record, data)
    record_event(record, actor, "edited")
    db.flush()
    return record
