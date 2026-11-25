from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base, Owned, Record, tenant_key


class Organization(Record, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="active")


class Department(Owned, Base):
    __tablename__ = "departments"
    __table_args__ = (tenant_key(), UniqueConstraint("organization_id", "name"))
    name: Mapped[str] = mapped_column(String(200))


class Branch(Owned, Base):
    __tablename__ = "branches"
    __table_args__ = (tenant_key(), UniqueConstraint("organization_id", "name"))
    name: Mapped[str] = mapped_column(String(200))
