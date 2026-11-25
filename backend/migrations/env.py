import os
from alembic import context
from app.core.db import Base, engine_for
from app import models

url = os.environ.get("PF_DATABASE_URL", "sqlite:///./procureflow.db")


def render_item(kind, value, context):
    if kind == "type" and type(value).__name__ == "UTCDateTime":
        return "sa.DateTime(timezone=True)"
    return False


if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = engine_for(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            render_item=render_item,
            target_metadata=Base.metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
