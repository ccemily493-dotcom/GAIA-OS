"""create_task tool implementation for GAIA OS."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from gaia.domain.entities import Task
from gaia.domain.events import EventType
from gaia.tools.base import BaseTool, ToolContext, ToolResult


class CreateTaskInput(BaseModel):
    """Input contract for create_task."""

    title: str = Field(
        ..., min_length=1, max_length=300, description="Title or summary of the task"
    )
    description: str = Field(
        default="", max_length=5000, description="Detailed instructions or context"
    )
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Task urgency/importance: low, medium, high, critical",
    )
    status: str = Field(
        default="todo",
        pattern="^(todo|in_progress|done|cancelled)$",
        description="Task state: todo, in_progress, done, cancelled",
    )
    project_id: str | None = Field(default=None, description="Optional associated project UUID")


class CreateTaskTool(BaseTool):
    """Tool to create a tangible task or action item."""

    @property
    def name(self) -> str:
        return "create_task"

    @property
    def description(self) -> str:
        return "Create a new actionable task with a priority and status."

    @property
    def input_model(self) -> type[BaseModel]:
        return CreateTaskInput

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            validated = CreateTaskInput.model_validate(arguments)
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

        task = Task(
            title=validated.title,
            description=validated.description,
            priority=validated.priority,
            status=validated.status,
            project_id=validated.project_id,
        )
        saved = await context.task_repo.create_task(task)

        return ToolResult(
            success=True,
            output={
                "id": saved.id,
                "title": saved.title,
                "priority": saved.priority,
                "status": saved.status,
                "project_id": saved.project_id,
                "message": f"Task '{saved.title}' created successfully.",
            },
            event_type=EventType.TASK_CREATED,
            event_payload={"task_id": saved.id, "title": saved.title, "priority": saved.priority},
        )
