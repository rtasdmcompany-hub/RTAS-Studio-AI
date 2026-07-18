"""AI Budget Manager."""

from __future__ import annotations

from app.services.cost_intelligence import store
from app.services.cost_intelligence.models import BudgetProfile, new_id
from app.services.cost_intelligence.version import (
    DEFAULT_DAILY_BUDGET_USD,
    DEFAULT_MONTHLY_BUDGET_USD,
)


def ensure_default_budget() -> BudgetProfile:
    budgets = store.all_budgets()
    if budgets:
        return budgets[0]
    profile = BudgetProfile(
        budget_id=new_id("budget"),
        name="default",
        daily_limit_usd=DEFAULT_DAILY_BUDGET_USD,
        monthly_limit_usd=DEFAULT_MONTHLY_BUDGET_USD,
    )
    return store.save_budget(profile)


def create_budget(
    name: str,
    *,
    daily_limit_usd: float | None = None,
    monthly_limit_usd: float | None = None,
    project_id: str | None = None,
    team_id: str | None = None,
) -> BudgetProfile:
    profile = BudgetProfile(
        budget_id=new_id("budget"),
        name=name or "budget",
        daily_limit_usd=float(daily_limit_usd or DEFAULT_DAILY_BUDGET_USD),
        monthly_limit_usd=float(monthly_limit_usd or DEFAULT_MONTHLY_BUDGET_USD),
        project_id=project_id,
        team_id=team_id,
    )
    return store.save_budget(profile)


def apply_spend(amount_usd: float, *, project_id: str | None = None, team_id: str | None = None) -> list[BudgetProfile]:
    """Charge spend against matching budgets. Returns updated profiles."""
    amount = max(0.0, float(amount_usd))
    updated: list[BudgetProfile] = []
    for b in store.all_budgets():
        if not b.active:
            continue
        if b.project_id and project_id and b.project_id != project_id:
            continue
        if b.team_id and team_id and b.team_id != team_id:
            continue
        # Global budgets (no project/team) always receive spend
        if b.project_id and not project_id:
            continue
        if b.team_id and not team_id:
            continue
        b.spent_daily_usd += amount
        b.spent_monthly_usd += amount
        store.save_budget(b)
        updated.append(b)
    if not updated:
        default = ensure_default_budget()
        default.spent_daily_usd += amount
        default.spent_monthly_usd += amount
        store.save_budget(default)
        updated.append(default)
    return updated


def can_spend(amount_usd: float, *, budget_id: str | None = None) -> dict[str, object]:
    amount = max(0.0, float(amount_usd))
    if budget_id:
        b = store.get_budget(budget_id)
        profiles = [b] if b else []
    else:
        profiles = store.all_budgets() or [ensure_default_budget()]
    allowed = True
    reasons: list[str] = []
    for b in profiles:
        if not b:
            continue
        if b.spent_daily_usd + amount > b.daily_limit_usd:
            allowed = False
            reasons.append(f"{b.name}: daily budget exceeded")
        if b.spent_monthly_usd + amount > b.monthly_limit_usd:
            allowed = False
            reasons.append(f"{b.name}: monthly budget exceeded")
        util = b.spent_daily_usd / b.daily_limit_usd if b.daily_limit_usd else 0
        if util >= b.alert_threshold:
            reasons.append(f"{b.name}: daily alert threshold reached")
    return {
        "allowed": allowed,
        "amount_usd": amount,
        "reasons": reasons,
        "budgets": [b.to_dict() for b in profiles if b],
    }


def list_budgets() -> list[dict]:
    ensure_default_budget()
    return [b.to_dict() for b in store.all_budgets()]
