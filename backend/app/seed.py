"""Repeatable, development-only fixtures. A complete seed is one transaction."""

import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.db import engine_for
from app.modules.organizations.models import Organization, Department, Branch
from app.modules.identity.domain import Role
from app.modules.identity.models import User, Membership
from app.modules.identity.security import hash_password
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.domain import normalized_name
from app.modules.catalog.models import CatalogItem
from app.modules.requisitions.domain import Estimate
from app.modules.requisitions.models import RequestRecord, LineRecord, History
from app.modules.approvals.models import Approval


def key(name: str) -> str:
    return str(uuid5(NAMESPACE_URL, "urn:procureflow:dev:" + name))


def populate(db: Session, slug: str, name: str, password: str) -> bool:
    org_id = key(slug)
    existing = db.scalar(select(Organization).where(Organization.slug == slug))
    if existing:
        if existing.id != org_id:
            raise RuntimeError(
                "Seed workspace slug belongs to an existing organization."
            )
        return False
    start = datetime(2026, 11, 2, 9, tzinfo=timezone.utc)

    def attrs(label: str):
        return dict(
            id=key(slug + "/" + label),
            organization_id=org_id,
            created_at=start,
            modified_at=start,
        )

    db.add(
        Organization(
            id=org_id,
            slug=slug,
            name=name,
            currency="USD",
            created_at=start,
            modified_at=start,
        )
    )
    db.flush()
    for title in ["Operations", "Facilities", "Technology"]:
        db.add(Department(**attrs(title), name=title))
    db.add(Branch(**attrs("hq"), name="Head office"))
    people = [
        ("admin", "Avery Chen", Role.ADMIN),
        ("buyer", "Sam Patel", Role.PROCUREMENT),
        ("reviewer", "Casey Morgan", Role.MANAGER),
        ("requester", "Alex Rivera", Role.REQUESTER),
        ("finance", "Maya Shah", Role.FINANCE),
    ]
    for handle, person, role in people:
        user = User(
            id=key(slug + "/user/" + handle),
            email=f"{handle}@{slug}.example",
            name=person,
            password_hash=hash_password(password),
            created_at=start,
            modified_at=start,
        )
        db.add(Membership(**attrs(handle), user=user, role=role))
    vendors = [
        ("Eastbank Supply", "Office supplies", "active"),
        ("Fieldwork Systems", "Technology", "active"),
        ("Arc Workshop", "Facilities", "draft"),
        ("Cedar Stationers", "Office supplies", "inactive"),
    ]
    for i, (vendor, category, status) in enumerate(vendors, 1):
        db.add(
            Supplier(
                **attrs("vendor/" + str(i)),
                name=vendor,
                name_key=normalized_name(vendor),
                category=category,
                tax_id=f"DEV-{i:03}",
                status=status,
                contacts=[
                    {
                        "name": "Sales desk",
                        "email": f"sales@vendor{i}.example",
                        "phone": "",
                    }
                ],
                addresses=["18 Market Street"],
            )
        )
    products = [
        ("MON-27", "27-inch monitor", "Technology", "each", "285.50", "product"),
        ("FUR-04", "Task chair", "Facilities", "each", "194.00", "product"),
        ("SVC-01", "Equipment servicing", "Maintenance", "hour", "75.00", "service"),
    ]
    for code, title, category, unit, price, kind in products:
        db.add(
            CatalogItem(
                **attrs(code),
                code=code,
                name=title,
                description=title,
                category=category,
                unit=unit,
                reference_price=Decimal(price),
                currency="USD",
                kind=kind,
            )
        )
    db.flush()
    samples = [
        ("Studio monitor refresh", "draft", 0, 4),
        ("Meeting room seating", "pending_approval", 1, 8),
        ("Quarterly equipment service", "approved", 2, 6),
        ("Additional task chairs", "rejected", 1, 12),
        ("Spare monitor allocation", "cancelled", 0, 2),
    ]
    for index, (title, status, product, qty) in enumerate(samples, 1):
        code, item, _, unit, price, _ = products[product]
        timestamp = start + timedelta(days=index)
        calc = Estimate(Decimal(qty), Decimal(price), Decimal("5.00"))
        rid = key(slug + "/request/" + str(index))
        requester = key(slug + "/requester")
        reviewer = key(slug + "/reviewer")
        req = RequestRecord(
            id=rid,
            organization_id=org_id,
            number=f"PR-2026-{index:04}",
            description=title,
            status=status,
            currency="USD",
            department_id=key(slug + "/Operations"),
            requester_id=requester,
            supplier_id=key(slug + "/vendor/2"),
            required_date=date(2026, 12, 10) + timedelta(days=index),
            estimated_total=calc.total,
            created_at=timestamp,
            modified_at=timestamp,
        )
        req.lines = [
            LineRecord(
                **attrs(f"line/{index}"),
                catalog_item_id=key(slug + "/" + code),
                description=item,
                position=1,
                unit=unit,
                quantity=calc.quantity,
                unit_price=calc.unit_price,
                tax_percent=calc.tax_percent,
                line_total=calc.total,
            )
        ]
        events = ["created"]
        if status in {"pending_approval", "approved", "rejected"}:
            events.extend(["submitted", "pending_approval"])
        if status in {"approved", "rejected", "cancelled"}:
            events.append(status)
        for seq, event in enumerate(events, 1):
            when = timestamp + timedelta(minutes=seq - 1)
            decision = event in {"approved", "rejected"}
            comment = (
                (
                    "Budget confirmed."
                    if event == "approved"
                    else "Revise the proposed quantity."
                )
                if decision
                else ""
            )
            req.history.append(
                History(
                    id=key(f"{slug}/event/{index}/{seq}"),
                    organization_id=org_id,
                    sequence=seq,
                    event=event,
                    actor_id=reviewer if decision else requester,
                    comment=comment,
                    created_at=when,
                    modified_at=when,
                )
            )
        req.modified_at = req.history[-1].created_at
        db.add(req)
        db.flush()
        if "submitted" in events:
            final = status in {"approved", "rejected"}
            db.add(
                Approval(
                    id=key(f"{slug}/approval/{index}"),
                    organization_id=org_id,
                    requisition_id=rid,
                    approver_id=reviewer,
                    status=status if final else "pending",
                    decided_at=req.modified_at if final else None,
                    comment=req.history[-1].comment if final else "",
                    created_at=timestamp + timedelta(minutes=2),
                    modified_at=req.modified_at,
                )
            )
    return True


def main():
    settings = Settings.load()
    password = os.environ.get("PF_SEED_PASSWORD", "")
    if (
        os.environ.get("PF_ENV") != "development"
        or not 12 <= len(password) <= 128
        or password.startswith("<")
    ):
        raise SystemExit(
            "Seeding requires PF_ENV=development and a development password (12–128 characters)."
        )
    engine = engine_for(settings.database_url)
    with Session(engine) as db, db.begin():
        count = sum(
            populate(db, slug, name, password)
            for slug, name in [
                ("northline", "Northline Studio"),
                ("harbor", "Harbor Works"),
            ]
        )
    engine.dispose()
    print(f"Seeded {count} workspaces. Existing seed workspaces were preserved.")


if __name__ == "__main__":
    main()
