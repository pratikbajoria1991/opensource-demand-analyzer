from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DemandScore:
    total: float
    stars: float
    forks: float
    open_issues: float
    recency: float
    engagement: float
    tier: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 2),
            "stars": round(self.stars, 2),
            "forks": round(self.forks, 2),
            "open_issues": round(self.open_issues, 2),
            "recency": round(self.recency, 2),
            "engagement": round(self.engagement, 2),
            "tier": self.tier,
        }


def _log_norm(value: float, ceiling: float) -> float:
    if value <= 0:
        return 0.0
    return min(math.log10(value + 1) / math.log10(ceiling + 1), 1.0) * 100


def _days_since(iso_date: str | None) -> float:
    if not iso_date:
        return 365.0
    updated = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - updated
    return max(delta.total_seconds() / 86400, 0)


def score_demand(repo: dict[str, Any]) -> DemandScore:
    """Compute a 0-100 demand score from public GitHub signals."""
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    open_issues = repo.get("open_issues_count", 0)
    watchers = repo.get("watchers_count", 0)
    days = _days_since(repo.get("pushed_at"))

    stars_score = _log_norm(stars, 100_000)
    forks_score = _log_norm(forks, 20_000)
    issues_score = _log_norm(open_issues, 5_000)
    recency_score = max(0.0, 100 - (days / 365) * 100)
    engagement_score = _log_norm(watchers + forks, 25_000)

    total = (
        stars_score * 0.35
        + forks_score * 0.20
        + issues_score * 0.15
        + recency_score * 0.15
        + engagement_score * 0.15
    )

    if total >= 75:
        tier = "very_high"
    elif total >= 55:
        tier = "high"
    elif total >= 35:
        tier = "moderate"
    else:
        tier = "emerging"

    return DemandScore(
        total=total,
        stars=stars_score,
        forks=forks_score,
        open_issues=issues_score,
        recency=recency_score,
        engagement=engagement_score,
        tier=tier,
    )