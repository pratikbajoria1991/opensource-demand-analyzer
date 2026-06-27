from __future__ import annotations

from typing import Any

from os_analyzer.demand_scorer import score_demand
from os_analyzer.gap_analyzer import analyze_gaps, extract_hot_requests
from os_analyzer.github_client import GitHubClient


def analyze_repository(
    client: GitHubClient,
    repo: dict[str, Any],
    expected_features: list[str],
) -> dict[str, Any]:
    owner = repo["owner"]["login"]
    name = repo["name"]
    full_name = repo["full_name"]

    readme = client.get_readme(owner, name)
    feature_issues = client.search_issues(
        owner,
        name,
        'label:"enhancement" OR label:"feature request" OR "feature request" in:title',
    )
    if not feature_issues:
        feature_issues = client.search_issues(owner, name, '"feature request" OR enhancement')

    demand = score_demand(repo)
    gaps = analyze_gaps(expected_features, readme, feature_issues)
    hot_requests = extract_hot_requests(feature_issues)

    return {
        "full_name": full_name,
        "name": name,
        "owner": owner,
        "url": repo["html_url"],
        "description": repo.get("description") or "",
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "pushed_at": repo.get("pushed_at"),
        "topics": repo.get("topics", []),
        "demand": demand.to_dict(),
        "feature_gaps": [g.to_dict() for g in gaps],
        "hot_feature_requests": hot_requests,
    }


def analyze_category(
    client: GitHubClient,
    category: dict[str, Any],
    per_category: int = 8,
) -> list[dict[str, Any]]:
    repos = client.search_repositories(category["query"], per_page=per_category)
    expected = category.get("expected_features", [])
    return [analyze_repository(client, repo, expected) for repo in repos]