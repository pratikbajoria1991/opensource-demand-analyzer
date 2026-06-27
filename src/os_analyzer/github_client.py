from __future__ import annotations

import os
import time
from typing import Any

import requests

GITHUB_API = "https://api.github.com"


class GitHubClient:
    """Thin wrapper around the GitHub REST API with basic rate-limit handling."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = path if path.startswith("http") else f"{GITHUB_API}{path}"
        response = self.session.get(url, params=params, timeout=30)

        if response.status_code == 403 and "rate limit" in response.text.lower():
            reset = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - int(time.time()) + 1, 1)
            time.sleep(wait)
            response = self.session.get(url, params=params, timeout=30)

        response.raise_for_status()
        return response.json()

    def search_repositories(
        self, query: str, per_page: int = 10, page: int = 1
    ) -> list[dict[str, Any]]:
        data = self._get(
            "/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page,
            },
        )
        return data.get("items", [])

    def get_readme(self, owner: str, repo: str) -> str:
        try:
            data = self._get(f"/repos/{owner}/{repo}/readme")
            import base64

            content = data.get("content", "")
            encoding = data.get("encoding", "base64")
            if encoding == "base64":
                return base64.b64decode(content).decode("utf-8", errors="replace")
            return content
        except requests.HTTPError:
            return ""

    def search_issues(
        self, owner: str, repo: str, query_suffix: str, per_page: int = 15
    ) -> list[dict[str, Any]]:
        q = f"repo:{owner}/{repo} is:issue is:open {query_suffix}"
        data = self._get(
            "/search/issues",
            params={"q": q, "sort": "reactions", "order": "desc", "per_page": per_page},
        )
        return data.get("items", [])

    def rate_limit(self) -> dict[str, Any]:
        return self._get("/rate_limit")