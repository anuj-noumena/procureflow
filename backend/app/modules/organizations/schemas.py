from typing import Literal
from app.core.schemas import Input, Output, Label, Currency


class Profile(Input):
    name: Label
    currency: Currency
    status: Literal["active", "paused"]


class Named(Input):
    name: Label


class Unit(Output):
    id: str
    name: str


class ProfileView(Profile):
    id: str
    slug: str
    departments: list[Unit]
    branches: list[Unit]
