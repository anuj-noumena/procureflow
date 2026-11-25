from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.core.db import engine_for
from app.core.errors import API_ERRORS, install_errors


def create_app(settings: Settings | None = None):
    settings = settings or Settings.load()
    app = FastAPI(title="ProcureFlow", version="0.1.0", docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.state.engine = engine_for(settings.database_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
    from app.core.docs import install_docs

    install_docs(app)
    install_errors(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    from app.modules.organizations.api import router as organizations
    from app.modules.identity.api import router as identity
    from app.modules.suppliers.api import router as suppliers
    from app.modules.catalog.api import router as catalog
    from app.modules.requisitions.api import router as requisitions
    from app.modules.approvals.api import router as approvals

    for router in (
        organizations,
        identity,
        suppliers,
        catalog,
        requisitions,
        approvals,
    ):
        app.include_router(router, prefix="/api/v1", responses=API_ERRORS)
    return app
