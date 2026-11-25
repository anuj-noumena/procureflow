from typing import Annotated
from pydantic import Field, SecretStr, StringConstraints
from app.core.schemas import Input, Output, Label
from .domain import Role

Email = Annotated[
    str,
    StringConstraints(
        to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")]
Password = Annotated[SecretStr, Field(min_length=12, max_length=128)]


class Login(Input):
    organization: Slug
    email: Email
    password: SecretStr = Field(max_length=128)


class Register(Login):
    name: Label
    organization_name: Label
    password: Password


class Token(Output):
    access_token: str
    token_type: str = "bearer"


class MemberCreate(Input):
    name: Label
    email: Email
    password: Password
    role: Role


class MemberChange(Input):
    role: Role
    active: bool


class MemberView(Output):
    id: str
    name: str
    email: str
    role: Role
    active: bool


class SessionView(MemberView):
    organization_id: str
    organization_name: str
    permissions: list[str]
