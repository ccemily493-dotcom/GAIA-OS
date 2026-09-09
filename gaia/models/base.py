"""Base protocols and data types for GAIA OS model providers and completions."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatMessage:
    """Chat message exchanged with a model provider."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolCall:
    """A tool call proposed by a model provider."""

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelCompletion:
    """Raw completion result returned by a ModelProvider."""

    raw_content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ModelProvider(Protocol):
    """Protocol for model inference backends (local or cloud)."""

    async def complete(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelCompletion: ...
