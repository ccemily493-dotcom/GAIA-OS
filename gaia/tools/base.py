"""Base protocols and types for GAIA OS typed tools."""

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from gaia.domain.events import EventType
from gaia.storage.protocols import (
    IdeaRepository,
    NoteRepository,
    ProjectRepository,
    StateRepository,
    TaskRepository,
)

TInput = TypeVar("TInput", bound=BaseModel)


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolContext:
    """Execution context injected into tools at runtime."""

    correlation_id: str
    causation_id: str | None = None
    project_repo: ProjectRepository
    task_repo: TaskRepository
    idea_repo: IdeaRepository
    note_repo: NoteRepository
    state_repo: StateRepository


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolResult:
    """Outcome of a tool execution."""

    success: bool
    output: Any
    error: str | None = None
    event_type: EventType | None = None
    event_payload: dict[str, Any] | None = None


class BaseTool(Protocol):
    """Protocol that every GAIA typed tool must implement."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def input_model(self) -> type[BaseModel]: ...

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult: ...
