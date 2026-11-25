from enum import StrEnum
from dataclasses import dataclass
from app.core.problem import Problem


class Role(StrEnum):
    ADMIN = "organization_admin"
    PROCUREMENT = "procurement_manager"
    MANAGER = "department_manager"
    REQUESTER = "requester"
    FINANCE = "finance_user"


READ = {"directory.read", "requisition.read"}
PERMISSIONS = {
    Role.REQUESTER: READ | {"requisition.write"},
    Role.FINANCE: READ,
    Role.MANAGER: READ | {"requisition.write", "approval.decide"},
    Role.PROCUREMENT: READ
    | {"directory.write", "requisition.write", "approval.decide", "requisition.manage"},
    Role.ADMIN: READ
    | {
        "directory.write",
        "requisition.write",
        "approval.decide",
        "requisition.manage",
        "organization.manage",
    },
}


@dataclass(frozen=True)
class Actor:
    tenant: str
    member: str
    role: Role

    def require(self, permission: str):
        if permission not in PERMISSIONS[self.role]:
            raise Problem(403, "Your role does not permit this action.")

    def may_change(self, owner: str):
        self.require("requisition.write")
        if self.member != owner and "requisition.manage" not in PERMISSIONS[self.role]:
            raise Problem(
                403,
                "Only the requester or a procurement administrator can change this request.",
            )
