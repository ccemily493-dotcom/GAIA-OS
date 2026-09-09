"""get_current_context tool implementation for GAIA OS."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from gaia.tools.base import BaseTool, ToolContext, ToolResult


class GetCurrentContextInput(BaseModel):
    """Input contract for get_current_context."""

    include_recent_packets: bool = Field(
        default=True, description="Whether to include recent context packets"
    )
    packet_limit: int = Field(
        default=5, ge=1, le=50, description="Max number of context packets to include"
    )


class GetCurrentContextTool(BaseTool):
    """Tool to retrieve the user's active context and working state."""

    @property
    def name(self) -> str:
        return "get_current_context"

    @property
    def description(self) -> str:
        return "Retrieve the current active project, task, agent, and recent context history."

    @property
    def input_model(self) -> type[BaseModel]:
        return GetCurrentContextInput

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            validated = GetCurrentContextInput.model_validate(arguments)
        except ValidationError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid arguments for {self.name}: {e.errors()}",
            )

        state = await context.state_repo.get_current_state()

        active_project = None
        if state.current_project_id:
            proj = await context.project_repo.get_project(state.current_project_id)
            if proj:
                active_project = {"id": proj.id, "name": proj.name, "status": proj.status}

        active_task = None
        if state.current_task_id:
            task = await context.task_repo.get_task(state.current_task_id)
            if task:
                active_task = {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                }

        recent_packets = []
        if validated.include_recent_packets:
            packets = await context.state_repo.get_recent_context_packets(
                limit=validated.packet_limit
            )
            recent_packets = [
                {
                    "id": p.id,
                    "source": p.source,
                    "type": p.type,
                    "payload": p.payload,
                    "priority": p.priority,
                    "created_at": p.created_at,
                }
                for p in packets
            ]

        return ToolResult(
            success=True,
            output={
                "current_project": active_project,
                "current_task": active_task,
                "active_app": state.active_app,
                "active_agent": state.active_agent,
                "last_action_timestamp": state.last_action_timestamp,
                "recent_context_packets": recent_packets,
                "message": "Current context retrieved successfully.",
            },
        )
