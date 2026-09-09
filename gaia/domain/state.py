"""Current state abstraction for GAIA OS v0.1 World State preparation."""

from pydantic import BaseModel, ConfigDict, Field


class CurrentState(BaseModel):
    """Represents the immediate focal state of the user in GAIA OS."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    current_project_id: str | None = Field(default=None, description="Active Project UUID")
    current_task_id: str | None = Field(default=None, description="Active Task UUID")
    active_app: str | None = Field(default=None, description="Current foreground application")
    active_agent: str | None = Field(default=None, description="Active delegated agent")
    last_action_timestamp: str | None = Field(default=None, description="Timestamp of last action")
