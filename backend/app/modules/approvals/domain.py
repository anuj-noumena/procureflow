from dataclasses import dataclass
from enum import StrEnum
from app.core.problem import Problem


class Decision(StrEnum):
    APPROVE = "approved"
    REJECT = "rejected"


@dataclass(frozen=True)
class ApprovalRequest:
    assigned_to: str
    requester: str
    status: str

    def decide(self, member: str, decision: Decision, comment: str) -> str:
        if member != self.assigned_to or member == self.requester:
            raise Problem(403, "Only the assigned independent approver can decide.")
        if self.status != "pending":
            raise Problem(409, "The approval is already closed.")
        if decision == Decision.REJECT and not comment.strip():
            raise Problem(422, "Give a reason for rejection.")
        return decision.value
