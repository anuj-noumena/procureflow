from fastapi import APIRouter
from app.core.dependencies import Admin, Current, DB
from .models import Department, Branch
from .schemas import Profile, ProfileView, Unit, Named
from . import service

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.get("", response_model=ProfileView)
def read(db: DB, actor: Current):
    return service.profile(db, actor.tenant)


@router.put("", response_model=ProfileView)
def update(data: Profile, db: DB, actor: Admin):
    return service.update(db, actor.tenant, data)


@router.post("/departments", response_model=Unit, status_code=201)
def department(data: Named, db: DB, actor: Admin):
    return service.add_unit(db, Department, actor.tenant, data)


@router.post("/branches", response_model=Unit, status_code=201)
def branch(data: Named, db: DB, actor: Admin):
    return service.add_unit(db, Branch, actor.tenant, data)
