from decimal import Decimal
from sqlalchemy import Numeric, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base, Owned, tenant_key


class CatalogItem(Owned, Base):
    __tablename__ = "catalog_items"
    __table_args__ = (
        tenant_key(),
        UniqueConstraint("organization_id", "code"),
        CheckConstraint("reference_price >= 0"),
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(2000))
    kind: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(200))
    reference_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
