from os_analyzer.demand_scorer import score_demand


def test_high_star_repo_scores_high():
    repo = {
        "stargazers_count": 50000,
        "forks_count": 8000,
        "open_issues_count": 400,
        "watchers_count": 1200,
        "pushed_at": "2026-06-01T00:00:00Z",
    }
    score = score_demand(repo)
    assert score.total >= 55
    assert score.tier in {"high", "very_high"}


def test_small_repo_scores_lower():
    repo = {
        "stargazers_count": 10,
        "forks_count": 2,
        "open_issues_count": 1,
        "watchers_count": 3,
        "pushed_at": "2020-01-01T00:00:00Z",
    }
    score = score_demand(repo)
    assert score.total < 35
    assert score.tier == "emerging"