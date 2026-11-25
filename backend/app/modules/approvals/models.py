from datetime import datetime
from sqlalchemy import String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, Owned, UTCDateTime
from app.core.db import owned_reference
from app.modules.requisitions.models import RequestRecord


class Approval(Owned, Base):
    __tablename__ = "approvals"
    __table_args__ = (
        owned_reference("requisition_id", "requisitions"),
        owned_reference("approver_id", "memberships"),
        UniqueConstraint("organization_id", "requisition_id"),
        Index("ix_inbox", "organization_id", "approver_id", "status"),
    )
    requisition_id: Mapped[str] = mapped_column(String(36))
    approver_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    comment: Mapped[str] = mapped_column(String(2000), default="")
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": version}
    requisition: Mapped[RequestRecord] = relationship(viewonly=True)
