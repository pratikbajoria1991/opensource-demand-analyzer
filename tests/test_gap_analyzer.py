from os_analyzer.gap_analyzer import analyze_gaps, extract_hot_requests


def test_detects_undocumented_feature():
    gaps = analyze_gaps(
        expected_features=["hybrid search", "sso"],
        readme="# My Project\n\nA vector database.",
        feature_issues=[],
    )
    features = {g.feature for g in gaps}
    assert "hybrid search" in features
    assert "sso" in features


def test_detects_likely_missing_from_issues():
    issues = [
        {
            "number": 42,
            "title": "Feature request: add SSO support",
            "body": "We need SSO for enterprise customers",
            "reactions": {"total_count": 5},
            "labels": [{"name": "enhancement"}],
        }
    ]
    gaps = analyze_gaps(
        expected_features=["sso"],
        readme="# App\n\nDeveloper tool.",
        feature_issues=issues,
    )
    assert gaps[0].status == "likely_missing"
    assert gaps[0].confidence >= 0.8


def test_extract_hot_requests():
    issues = [
        {
            "number": 1,
            "title": "Enhancement: plugin system",
            "body": "missing plugin ecosystem",
            "html_url": "https://example.com/1",
            "reactions": {"total_count": 10},
            "labels": [],
        },
        {
            "number": 2,
            "title": "Bug: crash on startup",
            "body": "segfault",
            "html_url": "https://example.com/2",
            "reactions": {"total_count": 1},
            "labels": [],
        },
    ]
    hot = extract_hot_requests(issues)
    assert len(hot) == 1
    assert hot[0]["number"] == 1