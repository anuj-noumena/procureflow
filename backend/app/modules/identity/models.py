from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base, Record, Owned, tenant_key


class User(Record, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(default=True)


class Membership(Owned, Base):
    __tablename__ = "memberships"
    __table_args__ = (tenant_key(), UniqueConstraint("organization_id", "user_id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(default=True)
    user: Mapped[User] = relationship(lazy="joined")
