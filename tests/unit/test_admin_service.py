"""Unit tests for GaiaAdminService deterministic operations."""

import pytest

from gaia.core.service import GaiaAdminService
from gaia.domain.events import EventType
from gaia.domain.exceptions import EntityNotFoundError
from gaia.events.recorder import EventRecorder
from gaia.storage.sqlite_repo import SqliteRepository


@pytest.fixture
async def admin_setup() -> tuple[GaiaAdminService, SqliteRepository, EventRecorder]:
    repo = SqliteRepository(":memory:")
    await repo.initialize()
    recorder = EventRecorder(repo)
    service = GaiaAdminService(
        project_repo=repo,
        task_repo=repo,
        state_repo=repo,
        event_recorder=recorder,
    )
    return service, repo, recorder


@pytest.mark.asyncio
async def test_admin_create_and_list_projects(
    admin_setup: tuple[GaiaAdminService, SqliteRepository, EventRecorder],
) -> None:
    service, repo, recorder = admin_setup

    proj = await service.create_project(name="Project Alpha", description="Alpha test")
    assert proj.name == "Project Alpha"

    projects = await service.list_projects()
    assert len(projects) == 1
    assert projects[0].id == proj.id

    events = await recorder.get_events()
    assert any(e.event_type == EventType.PROJECT_CREATED for e in events)


@pytest.mark.asyncio
async def test_admin_set_project_and_task(
    admin_setup: tuple[GaiaAdminService, SqliteRepository, EventRecorder],
) -> None:
    service, repo, recorder = admin_setup

    proj = await service.create_project(name="Gloomy")
    state = await service.set_current_project(proj.id)
    assert state.current_project_id == proj.id

    # Non-existent project
    with pytest.raises(EntityNotFoundError):
        await service.set_current_project("fake-id")
