"""The plan constants must match the plan table of docs/plans.md exactly."""

import re
from pathlib import Path

from magicvibe.subscription.constants import PLANS
from magicvibe.subscription.enums import PlanCode

PLANS_DOC = Path(__file__).resolve().parents[2] / "docs" / "plans.md"


def plan_table() -> dict[str, list[str]]:
    """Rows of the "Plan table" section, keyed by the plan code."""
    section = PLANS_DOC.read_text(encoding="utf-8").split("## Plan table", 1)[1]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]
    table = {}
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        table[cells[1].strip("`")] = cells
    return table


def test_every_plan_is_in_the_table() -> None:
    assert set(plan_table()) == {code.value for code in PlanCode}


def test_plans_match_the_table() -> None:
    for code, (name, _, duration, likes, superlikes, likers) in plan_table().items():
        plan = PLANS[PlanCode(code)]
        days = re.fullmatch(r"(\d+) days", duration)
        assert plan.name == name
        assert plan.duration_days == (int(days.group(1)) if days else None)
        assert plan.daily_like_limit == int(likes)
        assert plan.daily_superlike_limit == int(superlikes)
        assert plan.can_see_likers is (likers == "yes")
