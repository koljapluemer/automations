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
        if cached:
            return {"sent": True, "idea": cached.get("idea", ""), "cached": True}

        settings = ctx.config.settings
        token = settings.get("telegram_bot_token", "")
        chat_id = settings.get("telegram_chat_id", "")
        vault_path = Path(str(settings["vault_path"])).expanduser()

        if not token or not chat_id:
            return {"sent": False, "reason": "missing telegram_bot_token or telegram_chat_id"}

        ideas = sorted(p.name for p in vault_path.glob("⊛*") if p.is_file())
        if not ideas:
            return {"sent": False, "reason": "no idea notes found"}

        rng = random.Random(ctx.run_date.isoformat())
        idea = rng.choice(ideas)

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": idea})
        resp.raise_for_status()

        ctx.log.append(self.spec.id, "idea_sent", {"idea": idea})
        return {"sent": True, "idea": idea, "cached": False}
