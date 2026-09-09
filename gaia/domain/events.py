"""Append-oriented event models with causality tracking for GAIA OS."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Actor(StrEnum):
    """Actor identity triggering an event."""

    USER = "user"
    GAIA = "gaia"
    SYSTEM = "system"
    CODEX = "codex"
    ANTIGRAVITY = "antigravity"


class EventType(StrEnum):
    """Canonical event types for GAIA OS."""

    USER_MESSAGE = "USER_MESSAGE"
    GAIA_RESPONSE = "GAIA_RESPONSE"
    TOOL_CALLED = "TOOL_CALLED"
    NOTE_CREATED = "NOTE_CREATED"
    IDEA_CREATED = "IDEA_CREATED"
    TASK_CREATED = "TASK_CREATED"
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_SELECTED = "PROJECT_SELECTED"
    STATE_UPDATED = "STATE_UPDATED"
    ACTION_FAILED = "ACTION_FAILED"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class Event(BaseModel):
    """Append-only audit and learning event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=_new_id)
    event_type: EventType | str
    timestamp: str = Field(default_factory=_utc_now_iso)
    correlation_id: str = Field(description="UUID linking the entire interaction transaction")
    causation_id: str | None = Field(
        default=None, description="UUID of the direct causal predecessor event"
    )
    actor: Actor | str = Field(default=Actor.SYSTEM)
    payload: dict[str, Any] = Field(default_factory=dict)
