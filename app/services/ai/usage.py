"""Registro simple de uso de agentes IA (en memoria)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AICallRecord:
    agent: str
    ok: bool
    detail: str
    at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


_LAST_CALLS: list[AICallRecord] = []
_MAX = 20


def record_ai_call(agent: str, ok: bool, detail: str = "") -> None:
    _LAST_CALLS.insert(0, AICallRecord(agent=agent, ok=ok, detail=detail[:200]))
    del _LAST_CALLS[_MAX:]


def ai_status() -> dict:
    return {
        "calls": [
            {
                "agent": item.agent,
                "ok": item.ok,
                "detail": item.detail,
                "at": item.at,
            }
            for item in _LAST_CALLS[:8]
        ],
        "total_recorded": len(_LAST_CALLS),
    }
