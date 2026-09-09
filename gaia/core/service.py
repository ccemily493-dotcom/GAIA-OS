"""Application service for non-AI administrative operations in GAIA OS."""

import uuid
from datetime import UTC, datetime

from gaia.domain.entities import Project
from gaia.domain.events import Actor, EventType
from gaia.domain.exceptions import EntityNotFoundError
from gaia.domain.state import CurrentState
from gaia.events.recorder import EventRecorder
from gaia.storage.protocols import (
    ProjectRepository,
    StateRepository,
    TaskRepository,
)


class GaiaAdminService:
    """Provides deterministic administrative operations outside the model/tool pipeline."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        task_repo: TaskRepository,
        state_repo: StateRepository,
        event_recorder: EventRecorder,
    ) -> None:
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.state_repo = state_repo
        self.event_recorder = event_recorder

    async def create_project(self, name: str, description: str = "") -> Project:
        """Creates a new project deterministically."""
        correlation_id = str(uuid.uuid4())
        project = Project(name=name, description=description)
        created = await self.project_repo.create_project(project)

        await self.event_recorder.record(
            event_type=EventType.PROJECT_CREATED,
            correlation_id=correlation_id,
            actor=Actor.USER,
            payload={"project_id": created.id, "name": created.name},
        )
        return created

    async def list_projects(self, status: str | None = None) -> list[Project]:
        """Lists projects matching the optional status filter."""
        return await self.project_repo.list_projects(status=status)

    async def set_current_project(self, project_id: str | None) -> CurrentState:
        """Sets the active project in the user's current working state."""
        correlation_id = str(uuid.uuid4())
        if project_id is not None:
            proj = await self.project_repo.get_project(project_id)
            if not proj:
                raise EntityNotFoundError("Project", project_id)

        state = await self.state_repo.get_current_state()
        updated = CurrentState(
            current_project_id=project_id,
            current_task_id=state.current_task_id,
            active_app=state.active_app,
            active_agent=state.active_agent,
            last_action_timestamp=datetime.now(UTC).isoformat(),
        )
        saved_state = await self.state_repo.update_current_state(updated)

        await self.event_recorder.record(
            event_type=EventType.PROJECT_SELECTED,
            correlation_id=correlation_id,
            actor=Actor.USER,
            payload={"project_id": project_id},
        )
        return saved_state

    async def set_current_task(self, task_id: str | None) -> CurrentState:
        """Sets the active task in the user's current working state."""
        correlation_id = str(uuid.uuid4())
        if task_id is not None:
            task = await self.task_repo.get_task(task_id)
            if not task:
                raise EntityNotFoundError("Task", task_id)

        state = await self.state_repo.get_current_state()
        updated = CurrentState(
            current_project_id=state.current_project_id,
            current_task_id=task_id,
            active_app=state.active_app,
            active_agent=state.active_agent,
            last_action_timestamp=datetime.now(UTC).isoformat(),
        )
        saved_state = await self.state_repo.update_current_state(updated)

        await self.event_recorder.record(
            event_type=EventType.STATE_UPDATED,
            correlation_id=correlation_id,
            actor=Actor.USER,
            payload={"current_task_id": task_id},
        )
        return saved_state

    async def get_state(self) -> CurrentState:
        """Retrieves the active user state."""
        return await self.state_repo.get_current_state()
