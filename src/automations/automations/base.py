from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..context import AutomationContext
from ..models import AutomationResult, AutomationSpec


class Automation(ABC):
    spec: AutomationSpec

    @abstractmethod
    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        raise NotImplementedError
