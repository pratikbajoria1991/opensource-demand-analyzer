from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

FEATURE_REQUEST_PATTERNS = [
    r"\bfeature\s*request\b",
    r"\benhancement\b",
    r"\badd\s+support\b",
    r"\bmissing\b",
    r"\bnot\s+supported\b",
    r"\bwish\b",
    r"\broadmap\b",
    r"\brequest:\b",
]

GAP_KEYWORDS = [
    "sso",
    "rbac",
    "multi-tenant",
    "observability",
    "tracing",
    "plugin",
    "self-hosted",
    "offline",
    "streaming",
    "quantization",
    "hybrid search",
    "backup",
    "alerting",
    "api",
    "cli",
    "dashboard",
    "mobile",
    "kubernetes",
    "docker",
    "oauth",
]


@dataclass
class FeatureGap:
    feature: str
    status: str
    evidence: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "status": self.status,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 2),
        }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _mentioned_in_readme(feature: str, readme: str) -> bool:
    readme_norm = _normalize(readme)
    tokens = feature.lower().split()
    if len(tokens) == 1:
        return tokens[0] in readme_norm
    return feature.lower() in readme_norm or all(t in readme_norm for t in tokens)


def _issue_signals(issues: list[dict[str, Any]], feature: str) -> list[str]:
    signals: list[str] = []
    feature_lower = feature.lower()
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body") or ""
        combined = _normalize(f"{title} {body}")
        if feature_lower in combined or any(
            re.search(p, combined) for p in FEATURE_REQUEST_PATTERNS
        ):
            if feature_lower in combined:
                signals.append(f"Issue #{issue.get('number')}: {title}")
    return signals[:5]


def analyze_gaps(
    expected_features: list[str],
    readme: str,
    feature_issues: list[dict[str, Any]],
) -> list[FeatureGap]:
    """Identify likely missing or under-documented features."""
    gaps: list[FeatureGap] = []

    for feature in expected_features:
        in_readme = _mentioned_in_readme(feature, readme)
        issue_hits = _issue_signals(feature_issues, feature)

        if in_readme and not issue_hits:
            continue

        if not in_readme and issue_hits:
            status = "likely_missing"
            confidence = 0.85
            evidence = [f"Not documented in README"] + issue_hits
        elif not in_readme:
            status = "undocumented"
            confidence = 0.55
            evidence = ["Not mentioned in README; no strong issue signal"]
        else:
            status = "requested_by_community"
            confidence = 0.70
            evidence = issue_hits

        gaps.append(
            FeatureGap(
                feature=feature,
                status=status,
                evidence=evidence,
                confidence=confidence,
            )
        )

    return sorted(gaps, key=lambda g: g.confidence, reverse=True)


def extract_hot_requests(issues: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    """Surface high-signal open feature requests from issues."""
    results: list[dict[str, Any]] = []
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body") or ""
        combined = _normalize(f"{title} {body}")
        if any(re.search(p, combined) for p in FEATURE_REQUEST_PATTERNS) or any(
            kw in combined for kw in GAP_KEYWORDS
        ):
            reactions = issue.get("reactions", {}).get("total_count", 0)
            results.append(
                {
                    "number": issue.get("number"),
                    "title": title,
                    "url": issue.get("html_url"),
                    "reactions": reactions,
                    "labels": [l.get("name") for l in issue.get("labels", [])],
                }
            )
    return sorted(results, key=lambda r: r["reactions"], reverse=True)[:limit]