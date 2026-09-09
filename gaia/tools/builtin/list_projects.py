"""list_projects tool implementation for GAIA OS."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from gaia.tools.base import BaseTool, ToolContext, ToolResult


class ListProjectsInput(BaseModel):
    """Input contract for list_projects."""

    status: str | None = Field(
        default=None,
        description="Filter projects by status (active, archived, paused, completed), or null for all",
    )


class ListProjectsTool(BaseTool):
    """Tool to list current projects."""

    @property
    def name(self) -> str:
        return "list_projects"

    @property
    def description(self) -> str:
        return "List existing projects and their statuses."

    @property
    def input_model(self) -> type[BaseModel]:
        return ListProjectsInput

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            validated = ListProjectsInput.model_validate(arguments)
        except ValidationError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid arguments for {self.name}: {e.errors()}",
            )

        projects = await context.project_repo.list_projects(status=validated.status)

        output_list = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in projects
        ]

        return ToolResult(
            success=True,
            output={
                "count": len(output_list),
                "projects": output_list,
                "message": f"Found {len(output_list)} projects.",
            },
        )
