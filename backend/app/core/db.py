from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    ForeignKeyConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    event,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            raise ValueError("UTC timestamp requires timezone")
        return value.astimezone(timezone.utc) if value else None

    def process_result_value(self, value, dialect):
        return (
            value.replace(tzinfo=timezone.utc)
            if value and value.tzinfo is None
            else value
        )


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    modified_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=now, onupdate=now
    )


class Owned(Record):
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )


def tenant_key():
    return UniqueConstraint("organization_id", "id")


def engine_for(url: str):
    sqlite = url.startswith("sqlite")
    engine = create_engine(
        url,
        hide_parameters=True,
        connect_args={"check_same_thread": False, "timeout": 10} if sqlite else {},
    )
    if sqlite:

        @event.listens_for(engine, "connect")
        def foreign_keys(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")

    return engine


def owned_reference(column: str, table: str):
    return ForeignKeyConstraint(
        ["organization_id", column], [table + ".organization_id", table + ".id"]
    )
