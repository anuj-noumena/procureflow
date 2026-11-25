from datetime import datetime
from typing import Literal
from app.core.schemas import Notes, Output
from app.modules.requisitions.schemas import Summary, Version
from .domain import Decision


class Submit(Version):
    approver_id: str


class Decide(Version):
    decision: Decision
    comment: Notes = ""


class ApprovalView(Output):
    id: str
    requisition: Summary
    approver_id: str
    status: Literal["pending", "approved", "rejected", "cancelled"]
    comment: str
    created_at: datetime
    decided_at: datetime | None
    version: int
