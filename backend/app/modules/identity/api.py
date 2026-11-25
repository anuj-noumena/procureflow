from fastapi import APIRouter, Request
from sqlalchemy import select
from app.core.dependencies import DB, Admin, Current
from app.core.schemas import Input
from . import service
from .models import Membership
from .schemas import (
    Login,
    Register,
    Token,
    MemberCreate,
    MemberChange,
    MemberView,
    SessionView,
    Email,
)
from .domain import Role, PERMISSIONS

router = APIRouter(tags=["Identity"])


@router.post("/auth/register", response_model=Token, status_code=201)
def register(data: Register, db: DB, request: Request):
    return service.register(db, data, request.app.state.settings.jwt_secret)


@router.post("/auth/login", response_model=Token)
def login(data: Login, db: DB, request: Request):
    return service.login(db, data, request.app.state.settings.jwt_secret)


@router.get("/auth/me", response_model=SessionView)
def me(db: DB, actor: Current):
    return service.session_view(db, actor)


@router.get("/members", response_model=list[MemberView])
def members(db: DB, actor: Admin):
    return [
        service.view(m)
        for m in db.scalars(
            select(Membership).where(Membership.organization_id == actor.tenant)
        )
    ]


@router.post("/members", response_model=MemberView, status_code=201)
def add(data: MemberCreate, db: DB, actor: Admin):
    return service.view(service.create_member(db, actor.tenant, data))


class Enrollment(Input):
    email: Email
    role: Role


@router.post("/members/enroll", response_model=MemberView, status_code=201)
def enroll(data: Enrollment, db: DB, actor: Admin):
    return service.view(service.enroll(db, actor.tenant, data.email, data.role))


@router.put("/members/{identifier}", response_model=MemberView)
def change(identifier: str, data: MemberChange, db: DB, actor: Admin):
    return service.view(service.change_member(db, actor, identifier, data))


class Choice(Input):
    id: str
    name: str


@router.get("/approvers", response_model=list[Choice])
def approvers(db: DB, actor: Current):
    eligible = [r for r, p in PERMISSIONS.items() if "approval.decide" in p]
    return [
        dict(id=m.id, name=m.user.name)
        for m in db.scalars(
            select(Membership)
            .join(Membership.user)
            .where(
                Membership.organization_id == actor.tenant,
                Membership.active.is_(True),
                Membership.role.in_(eligible),
                Membership.id != actor.member,
                Membership.user.has(active=True),
            )
            .order_by(Membership.created_at)
        )
    ]
