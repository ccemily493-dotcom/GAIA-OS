"""Context packet abstraction for GAIA OS v0.1 Context Fabric preparation."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class ContextPacket(BaseModel):
    """Minimal contextual packet emitted by context producers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=_new_id)
    source: str = Field(min_length=1, description="Origin of context (e.g. system, user, ide)")
    type: str = Field(min_length=1, description="Type descriptor of the packet payload")
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(
        default=0, ge=0, le=100, description="Priority weight (0=low, 100=highest)"
    )
    created_at: str = Field(default_factory=_utc_now_iso)
