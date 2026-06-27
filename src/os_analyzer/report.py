from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_category_report(
    category: dict[str, Any],
    repositories: list[dict[str, Any]],
) -> dict[str, Any]:
    ranked = sorted(
        repositories,
        key=lambda r: r["demand"]["total"],
        reverse=True,
    )
    return {
        "category_id": category["id"],
        "category_name": category["name"],
        "query": category["query"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "repository_count": len(ranked),
        "most_demanding": ranked[:5],
        "most_gaps": sorted(
            ranked,
            key=lambda r: len(r.get("feature_gaps", [])),
            reverse=True,
        )[:5],
        "all_repositories": ranked,
    }


def build_summary_report(category_reports: list[dict[str, Any]]) -> dict[str, Any]:
    all_repos: list[dict[str, Any]] = []
    for report in category_reports:
        for repo in report["all_repositories"]:
            entry = {**repo, "category_id": report["category_id"]}
            all_repos.append(entry)

    top_demand = sorted(all_repos, key=lambda r: r["demand"]["total"], reverse=True)[:10]
    top_gaps = sorted(
        all_repos,
        key=lambda r: (
            len(r.get("feature_gaps", [])),
            r["demand"]["total"],
        ),
        reverse=True,
    )[:10]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "categories_analyzed": len(category_reports),
        "total_repositories": len(all_repos),
        "top_demanding_projects": [
            {
                "full_name": r["full_name"],
                "url": r["url"],
                "category": r["category_id"],
                "demand_score": r["demand"]["total"],
                "tier": r["demand"]["tier"],
                "stars": r["stars"],
            }
            for r in top_demand
        ],
        "projects_with_most_gaps": [
            {
                "full_name": r["full_name"],
                "url": r["url"],
                "category": r["category_id"],
                "gap_count": len(r.get("feature_gaps", [])),
                "top_gaps": [g["feature"] for g in r.get("feature_gaps", [])[:3]],
                "demand_score": r["demand"]["total"],
            }
            for r in top_gaps
        ],
        "categories": category_reports,
    }


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Open Source Demand & Feature Gap Report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        f"**Categories analyzed:** {summary['categories_analyzed']}  ",
        f"**Repositories scanned:** {summary['total_repositories']}",
        "",
        "## Most Demanding Projects",
        "",
        "| Rank | Project | Category | Demand | Tier | Stars |",
        "|------|---------|----------|--------|------|-------|",
    ]

    for i, p in enumerate(summary["top_demanding_projects"], 1):
        lines.append(
            f"| {i} | [{p['full_name']}]({p['url']}) | {p['category']} "
            f"| {p['demand_score']:.1f} | {p['tier']} | {p['stars']:,} |"
        )

    lines.extend(
        [
            "",
            "## Projects Lacking Features (Highest Gap Signals)",
            "",
            "| Rank | Project | Category | Gaps | Top Missing / Undocumented | Demand |",
            "|------|---------|----------|------|-----------------------------|--------|",
        ]
    )

    for i, p in enumerate(summary["projects_with_most_gaps"], 1):
        gaps = ", ".join(p["top_gaps"]) if p["top_gaps"] else "—"
        lines.append(
            f"| {i} | [{p['full_name']}]({p['url']}) | {p['category']} "
            f"| {p['gap_count']} | {gaps} | {p['demand_score']:.1f} |"
        )

    for cat in summary["categories"]:
        lines.extend(
            [
                "",
                f"## {cat['category_name']}",
                "",
                f"Query: `{cat['query']}`",
                "",
                "### Top by demand",
                "",
            ]
        )
        for repo in cat["most_demanding"][:3]:
            lines.append(
                f"- **{repo['full_name']}** — demand {repo['demand']['total']:.1f}, "
                f"{repo['stars']:,} stars, {len(repo.get('feature_gaps', []))} gap signals"
            )
            for gap in repo.get("feature_gaps", [])[:2]:
                lines.append(f"  - Gap: *{gap['feature']}* ({gap['status']})")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")