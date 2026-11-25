from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base, Owned, tenant_key


class Supplier(Owned, Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        tenant_key(),
        UniqueConstraint("organization_id", "name_key"),
        UniqueConstraint("organization_id", "tax_id"),
    )
    name: Mapped[str] = mapped_column(String(200))
    name_key: Mapped[str] = mapped_column(String(600))
    category: Mapped[str] = mapped_column(String(200))
    tax_id: Mapped[str | None] = mapped_column(String(64))
    contacts: Mapped[list] = mapped_column(JSON)
    addresses: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
