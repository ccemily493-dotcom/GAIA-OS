"""create_note tool implementation for GAIA OS."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from gaia.domain.entities import Note
from gaia.domain.events import EventType
from gaia.tools.base import BaseTool, ToolContext, ToolResult


class CreateNoteInput(BaseModel):
    """Input contract for create_note."""

    title: str = Field(..., min_length=1, max_length=300, description="Title of the note")
    content: str = Field(..., min_length=1, description="Body content of the note")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    project_id: str | None = Field(default=None, description="Optional associated project UUID")


class CreateNoteTool(BaseTool):
    """Tool to create and persist a new note."""

    @property
    def name(self) -> str:
        return "create_note"

    @property
    def description(self) -> str:
        return "Create and save a new persistent note, documentation, or meeting record."

    @property
    def input_model(self) -> type[BaseModel]:
        return CreateNoteInput

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            validated = CreateNoteInput.model_validate(arguments)
        except ValidationError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid arguments for {self.name}: {e.errors()}",
            )

        # Check if project exists if project_id is provided
        if validated.project_id:
            proj = await context.project_repo.get_project(validated.project_id)
            if not proj:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Project with ID '{validated.project_id}' does not exist.",
                )

        note = Note(
            title=validated.title,
            content=validated.content,
            tags=validated.tags,
            project_id=validated.project_id,
        )
        saved = await context.note_repo.create_note(note)

        return ToolResult(
            success=True,
            output={
                "id": saved.id,
                "title": saved.title,
                "project_id": saved.project_id,
                "tags": saved.tags,
                "message": f"Note '{saved.title}' created successfully.",
            },
            event_type=EventType.NOTE_CREATED,
            event_payload={"note_id": saved.id, "title": saved.title, "tags": saved.tags},
        )
