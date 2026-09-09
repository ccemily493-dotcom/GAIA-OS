"""Core interaction and intent interpretation types for GAIA OS."""

from dataclasses import dataclass

from gaia.models.base import ToolCall


@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationalResponse:
    """A direct conversational response when no tool is called."""

    message: str


type InterpretationResult = ToolCall | ConversationalResponse

__all__ = ["ConversationalResponse", "InterpretationResult", "ToolCall"]
