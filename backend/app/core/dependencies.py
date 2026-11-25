from typing import Annotated
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.errors import Problem
from app.core.session import database
from app.modules.identity.domain import Actor, Role
from app.modules.identity.models import Membership
from app.modules.identity.security import claims
from app.modules.organizations.models import Organization

DB = Annotated[Session, Depends(database)]
bearer = HTTPBearer(auto_error=False)


def current(
    request: Request,
    db: DB,
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Actor:
    if not auth:
        raise Problem(401, "Sign in to continue.")
    try:
        data = claims(auth.credentials, request.app.state.settings.jwt_secret)
    except jwt.InvalidTokenError:
        raise Problem(401, "Session expired or invalid.")
    member = db.get(Membership, data["mid"])
    if (
        not member
        or member.user_id != data["sub"]
        or not member.active
        or not member.user.active
    ):
        raise Problem(401, "Membership is inactive.")
    org = db.get(Organization, member.organization_id)
    if org.status != "active" and not (
        member.role == Role.ADMIN
        and request.url.path in {"/api/v1/organization", "/api/v1/auth/me"}
    ):
        raise Problem(403, "This workspace is paused.")
    return Actor(member.organization_id, member.id, Role(member.role))


def allow(permission: str):
    def dependency(actor: Annotated[Actor, Depends(current)]):
        actor.require(permission)
        return actor

    return Depends(dependency)


Current = Annotated[Actor, Depends(current)]
Admin = Annotated[Actor, allow("organization.manage")]
Reader = Annotated[Actor, allow("directory.read")]
Writer = Annotated[Actor, allow("directory.write")]
Requester = Annotated[Actor, allow("requisition.write")]
Approver = Annotated[Actor, allow("approval.decide")]
