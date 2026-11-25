from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Organization, Department, Branch
from .schemas import Profile, Named


def profile(db: Session, tenant: str):
    org = db.get(Organization, tenant)

    def units(model):
        return db.scalars(
            select(model).where(model.organization_id == tenant).order_by(model.name)
        ).all()

    return dict(
        id=org.id,
        name=org.name,
        slug=org.slug,
        currency=org.currency,
        status=org.status,
        departments=units(Department),
        branches=units(Branch),
    )


def update(db: Session, tenant: str, data: Profile):
    org = db.get(Organization, tenant)
    org.name, org.currency, org.status = data.name, data.currency, data.status
    db.flush()
    return profile(db, tenant)


def add_unit(
    db: Session, model: type[Department] | type[Branch], tenant: str, data: Named
):
    unit = model(organization_id=tenant, name=data.name)
    db.add(unit)
    db.flush()
    return unit
