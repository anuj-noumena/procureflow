from fastapi import Request
from sqlalchemy.orm import Session


def database(request: Request):
    with Session(request.app.state.engine, expire_on_commit=False) as db:
        with db.begin():
            yield db
