from datetime import date
from decimal import Decimal
from sqlalchemy import (
    String,
    Numeric,
    Date,
    UniqueConstraint,
    ForeignKeyConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, Owned, tenant_key, owned_reference
from app.modules.identity.models import Membership


class RequestRecord(Owned, Base):
    __tablename__ = "requisitions"
    __table_args__ = (
        tenant_key(),
        UniqueConstraint("organization_id", "number"),
        owned_reference("requester_id", "memberships"),
        owned_reference("department_id", "departments"),
        owned_reference("supplier_id", "suppliers"),
        CheckConstraint("estimated_total >= 0"),
    )
    number: Mapped[str] = mapped_column(String(40))
    requester_id: Mapped[str] = mapped_column(String(36))
    department_id: Mapped[str] = mapped_column(String(36))
    supplier_id: Mapped[str | None] = mapped_column(String(36))
    description: Mapped[str] = mapped_column(String(200))
    required_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    estimated_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(24), index=True)
    version: Mapped[int] = mapped_column(default=1)
    requester: Mapped[Membership] = relationship(viewonly=True, lazy="selectin")

    @property
    def requester_name(self) -> str:
        return self.requester.user.name

    __mapper_args__ = {"version_id_col": version}
    lines: Mapped[list["LineRecord"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="LineRecord.position",
    )
    history: Mapped[list["History"]] = relationship(
        order_by="History.sequence", cascade="all, delete-orphan"
    )


class LineRecord(Owned, Base):
    __tablename__ = "requisition_lines"
    __table_args__ = (
        owned_reference("requisition_id", "requisitions"),
        owned_reference("catalog_item_id", "catalog_items"),
        CheckConstraint(
            "quantity > 0 AND unit_price >= 0 AND tax_percent BETWEEN 0 AND 100"
        ),
    )
    requisition_id: Mapped[str] = mapped_column(String(36), index=True)
    position: Mapped[int]
    catalog_item_id: Mapped[str | None] = mapped_column(String(36))
    description: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[Decimal] = mapped_column(Numeric(9, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    request: Mapped[RequestRecord] = relationship(back_populates="lines")


class History(Owned, Base):
    __tablename__ = "requisition_history"
    __table_args__ = (
        owned_reference("requisition_id", "requisitions"),
        owned_reference("actor_id", "memberships"),
        UniqueConstraint("organization_id", "requisition_id", "sequence"),
    )
    requisition_id: Mapped[str] = mapped_column(String(36), index=True)
    sequence: Mapped[int]
    actor_id: Mapped[str] = mapped_column(String(36))
    event: Mapped[str] = mapped_column(String(40))
    comment: Mapped[str] = mapped_column(String(2000), default="")
    actor: Mapped[Membership] = relationship(viewonly=True, lazy="selectin")

    @property
    def actor_name(self) -> str:
        return self.actor.user.name
