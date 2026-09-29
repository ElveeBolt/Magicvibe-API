from dataclasses import dataclass

from .enums import PlanCode

# The values must match the plan table in docs/plans.md exactly.


@dataclass(frozen=True)
class Plan:
    code: PlanCode
    name: str
    duration_days: int | None  # None = no end date
    daily_like_limit: int
    daily_superlike_limit: int
    can_see_likers: bool  # access to "Who liked me"


@dataclass(frozen=True)
class FreePlan(Plan):
    code: PlanCode = PlanCode.FREE
    name: str = "Free"
    duration_days: int | None = None
    daily_like_limit: int = 5
    daily_superlike_limit: int = 0
    can_see_likers: bool = False


@dataclass(frozen=True)
class PremiumPlan(Plan):
    code: PlanCode = PlanCode.PREMIUM
    name: str = "Premium"
    duration_days: int | None = 7
    daily_like_limit: int = 20
    daily_superlike_limit: int = 5
    can_see_likers: bool = True


PLANS: dict[PlanCode, Plan] = {
    PlanCode.FREE: FreePlan(),
    PlanCode.PREMIUM: PremiumPlan(),
}

MAX_COMMENT_LENGTH = 1000
