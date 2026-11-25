from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import Problem
from app.core.persistence import scoped
from app.modules.organizations.models import Organization, Department
from .models import User, Membership
from .domain import Role, PERMISSIONS, Actor
from .schemas import Login, Register, MemberCreate, MemberChange
from .security import hash_password, verify, issue, derive


def create_member(db: Session, tenant: str, data: MemberCreate):
    user = db.scalar(select(User).where(User.email == data.email))
    if user:
        raise Problem(
            409,
            "Email already registered. Use the existing-account membership operation.",
        )
    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password.get_secret_value()),
    )
    member = Membership(organization_id=tenant, user=user, role=data.role)
    db.add(member)
    db.flush()
    return member


def enroll(db: Session, tenant: str, email: str, role: Role):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise Problem(404, "Account not found.")
    member = Membership(organization_id=tenant, user=user, role=role)
    db.add(member)
    db.flush()
    return member


def register(db: Session, data: Register, key: str):
    org = Organization(name=data.organization_name, slug=data.organization)
    db.add(org)
    db.flush()
    db.add(Department(organization_id=org.id, name="Operations"))
    member = create_member(
        db,
        org.id,
        MemberCreate(
            name=data.name, email=data.email, password=data.password, role=Role.ADMIN
        ),
    )
    return {"access_token": issue(member.id, member.user_id, key)}


def login(db: Session, data: Login, key: str):
    member = db.scalar(
        select(Membership)
        .join(User)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(User.email == data.email, Organization.slug == data.organization)
    )
    password = data.password.get_secret_value()
    if not member:
        derive(password, bytes(16))
        raise Problem(401, "Invalid account or workspace.")
    if (
        not verify(password, member.user.password_hash)
        or not member.active
        or not member.user.active
    ):
        raise Problem(401, "Invalid account or workspace.")
    return {"access_token": issue(member.id, member.user_id, key)}


def change_member(db: Session, actor: Actor, identifier: str, data: MemberChange):
    member = scoped(db, Membership, actor.tenant, identifier)
    if member.id == actor.member and (not data.active or data.role != Role.ADMIN):
        raise Problem(409, "An administrator cannot revoke their own access.")
    member.role, member.active = data.role, data.active
    db.flush()
    return member


def view(member: Membership):
    return dict(
        id=member.id,
        name=member.user.name,
        email=member.user.email,
        role=member.role,
        active=member.active,
    )


def session_view(db: Session, actor: Actor):
    member = scoped(db, Membership, actor.tenant, actor.member)
    return dict(
        **view(member),
        organization_id=actor.tenant,
        organization_name=db.get(Organization, actor.tenant).name,
        permissions=sorted(PERMISSIONS[actor.role]),
    )
