"""create_idea tool implementation for GAIA OS."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from gaia.domain.entities import Idea
from gaia.domain.events import EventType
from gaia.tools.base import BaseTool, ToolContext, ToolResult


class CreateIdeaInput(BaseModel):
    """Input contract for create_idea."""

    title: str = Field(
        ..., min_length=1, max_length=300, description="Title or summary of the idea"
    )
    description: str = Field(
        default="", max_length=5000, description="Detailed description or context"
    )
    tags: list[str] = Field(default_factory=list, description="Keywords or topic tags")
    project_id: str | None = Field(default=None, description="Optional associated project UUID")


class CreateIdeaTool(BaseTool):
    """Tool to record an unrefined thought, concept, or feature idea."""

    @property
    def name(self) -> str:
        return "create_idea"

    @property
    def description(self) -> str:
        return "Record an idea, raw thought, exploration concept, or inspiration."

    @property
    def input_model(self) -> type[BaseModel]:
        return CreateIdeaInput

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            validated = CreateIdeaInput.model_validate(arguments)
        except ValidationError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid arguments for {self.name}: {e.errors()}",
            )

        if validated.project_id:
            proj = await context.project_repo.get_project(validated.project_id)
            if not proj:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Project with ID '{validated.project_id}' does not exist.",
                )

        idea = Idea(
            title=validated.title,
            description=validated.description,
            tags=validated.tags,
            project_id=validated.project_id,
        )
        saved = await context.idea_repo.create_idea(idea)

        return ToolResult(
            success=True,
            output={
                "id": saved.id,
                "title": saved.title,
                "description": saved.description,
                "project_id": saved.project_id,
                "tags": saved.tags,
                "message": f"Idea '{saved.title}' recorded successfully.",
            },
            event_type=EventType.IDEA_CREATED,
            event_payload={"idea_id": saved.id, "title": saved.title, "tags": saved.tags},
        )
