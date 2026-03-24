from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import requests

from ..base import Automation
from ...context import AutomationContext
from ...models import AutomationSpec


class TelegramIdeaAutomation(Automation):
    spec = AutomationSpec(
        id="telegram_idea",
        title="Telegram Idea of the Day",
        description="Send a random idea note filename to Telegram once per day.",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        cached = ctx.log.latest_event(self.spec.id, "idea_sent")
        if cached and "telegram_idea" not in ctx.force_flags:
            return {"sent": True, "ideas": cached.get("ideas", []), "cached": True}

        settings = ctx.config.settings
        token = settings.get("telegram_bot_token", "")
        chat_id = settings.get("telegram_chat_id", "")

        if not token or not chat_id:
            return {"sent": False, "reason": "missing telegram_bot_token or telegram_chat_id"}

        file_paths: list[str] = settings.get("telegram_idea_files", [])
        rng = random.Random(ctx.run_date.isoformat())
        ideas = _pick_one_per_file(file_paths, rng)
        if not ideas:
            return {"sent": False, "reason": "no idea notes found"}

        text = "\n".join(ideas)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text})
        resp.raise_for_status()

        ctx.log.append(self.spec.id, "idea_sent", {"ideas": ideas})
        return {"sent": True, "ideas": ideas, "cached": False}


def _pick_one_per_file(file_paths: list[str], rng: random.Random) -> list[str]:
    picked = []
    for raw in file_paths:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            continue
        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if lines:
            picked.append(rng.choice(lines))
    return picked
