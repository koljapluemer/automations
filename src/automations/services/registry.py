from __future__ import annotations

from typing import Any

from .github import GitHubClient


class ServiceRegistry:
    def __init__(self, services_config: dict[str, Any]) -> None:
        self._config = services_config
        self._github_clients: dict[tuple[str, str], GitHubClient] = {}

    def github_client(self, username: str, token: str) -> GitHubClient:
        key = (username, token)
        if key not in self._github_clients:
            self._github_clients[key] = GitHubClient(token=token, username=username)
        return self._github_clients[key]

    def service_config(self, name: str) -> dict[str, Any]:
        raw = self._config.get(name, {})
        return raw if isinstance(raw, dict) else {}
