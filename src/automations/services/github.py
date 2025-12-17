from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class GitHubRepoCount:
    count: int
    repos: list[dict[str, Any]]


class GitHubClient:
    def __init__(self, token: str, username: str) -> None:
        self._token = token
        self._username = username
        self._owned_repos_cache: list[dict[str, Any]] | None = None

    def count_owned_repos(self) -> GitHubRepoCount:
        owned = self.list_owned_repos()
        return GitHubRepoCount(count=len(owned), repos=owned)

    def list_owned_repos(self) -> list[dict[str, Any]]:
        if self._owned_repos_cache is not None:
            return self._owned_repos_cache

        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._fetch_page(page)
            if not batch:
                break
            repos.extend(batch)
            page += 1

        self._owned_repos_cache = [repo for repo in repos if self._is_owned(repo)]
        return self._owned_repos_cache

    def _fetch_page(self, page: int) -> list[dict[str, Any]]:
        url = "https://api.github.com/user/repos"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "automations",
        }
        params = {
            "per_page": 100,
            "page": page,
            "type": "owner",
        }
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code >= 400:
            raise RuntimeError(
                f"GitHub API error {response.status_code}: {response.text.strip()}"
            )
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError("Unexpected GitHub API response")
        return data

    def _is_owned(self, repo: dict[str, Any]) -> bool:
        owner = repo.get("owner")
        if not isinstance(owner, dict):
            return False
        login = owner.get("login")
        if not isinstance(login, str):
            return False
        return login.lower() == self._username.lower()
