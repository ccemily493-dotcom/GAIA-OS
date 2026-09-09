"""Unit tests for SQLite persistence and migration runner."""

import pytest

from gaia.domain.context import ContextPacket
from gaia.domain.entities import Decision, Idea, Note, Project, Task
from gaia.domain.events import Actor, Event, EventType
from gaia.domain.state import CurrentState
from gaia.storage.sqlite_repo import SqliteRepository


@pytest.fixture
async def repo() -> SqliteRepository:
    repository = SqliteRepository(":memory:")
    await repository.initialize()
    yield repository
    await repository.close()


@pytest.mark.asyncio
async def test_migration_and_project_crud(repo: SqliteRepository) -> None:
    # Verify migration applied
    async with repo.connect() as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM schema_migrations;")
        count = (await cursor.fetchone())[0]
        assert count > 0

    project = Project(name="Project Prometheus", description="Core AI research")
    created = await repo.create_project(project)
    assert created.id == project.id

    fetched = await repo.get_project(project.id)
    assert fetched is not None
    assert fetched.name == "Project Prometheus"
    assert fetched.description == "Core AI research"

    projects = await repo.list_projects()
    assert len(projects) == 1
    assert projects[0].id == project.id


@pytest.mark.asyncio
async def test_task_crud_with_project(repo: SqliteRepository) -> None:
    proj = await repo.create_project(Project(name="Test Project"))
    task = Task(project_id=proj.id, title="Refactor SQLite Repo", priority="high")
    await repo.create_task(task)

    fetched = await repo.get_task(task.id)
    assert fetched is not None
    assert fetched.project_id == proj.id
    assert fetched.title == "Refactor SQLite Repo"

    tasks = await repo.list_tasks(project_id=proj.id)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_notes_and_ideas_crud(repo: SqliteRepository) -> None:
    note = Note(
        title="Design Patterns", content="Use Protocols for repositories", tags=["arch", "python"]
    )
    await repo.create_note(note)
    fetched_note = await repo.get_note(note.id)
    assert fetched_note is not None
    assert fetched_note.tags == ["arch", "python"]

    idea = Idea(title="Add whisper.cpp in v0.2", description="Local speech-to-text", tags=["voice"])
    await repo.create_idea(idea)
    fetched_idea = await repo.get_idea(idea.id)
    assert fetched_idea is not None
    assert fetched_idea.tags == ["voice"]


@pytest.mark.asyncio
async def test_decisions_crud(repo: SqliteRepository) -> None:
    decision = Decision(title="Use uv", rationale="Speed and PEP 621 compliance", status="accepted")
    await repo.create_decision(decision)
    fetched = await repo.get_decision(decision.id)
    assert fetched is not None
    assert fetched.status == "accepted"


@pytest.mark.asyncio
async def test_current_state_and_context_packets(repo: SqliteRepository) -> None:
    initial_state = await repo.get_current_state()
    assert initial_state.current_project_id is None

    proj = await repo.create_project(Project(name="State Test Project"))
    task = await repo.create_task(Task(project_id=proj.id, title="State Test Task"))

    updated_state = CurrentState(
        current_project_id=proj.id,
        current_task_id=task.id,
        active_app="Terminal",
        active_agent="gaia",
        last_action_timestamp="2026-09-09T20:00:00Z",
    )
    await repo.update_current_state(updated_state)

    retrieved = await repo.get_current_state()
    assert retrieved.current_project_id == proj.id
    assert retrieved.current_task_id == task.id
    assert retrieved.active_app == "Terminal"

    packet = ContextPacket(source="cli", type="user_intent", payload={"action": "test"})
    await repo.append_context_packet(packet)

    packets = await repo.get_recent_context_packets(limit=5)
    assert len(packets) == 1
    assert packets[0].payload["action"] == "test"


@pytest.mark.asyncio
async def test_event_append_and_retrieval(repo: SqliteRepository) -> None:
    e1 = Event(
        event_type=EventType.USER_MESSAGE,
        correlation_id="corr-123",
        actor=Actor.USER,
        payload={"query": "hello"},
    )
    e2 = Event(
        event_type=EventType.GAIA_RESPONSE,
        correlation_id="corr-123",
        causation_id=e1.id,
        actor=Actor.GAIA,
        payload={"response": "hi"},
    )
    await repo.append_event(e1)
    await repo.append_event(e2)

    events = await repo.get_events(correlation_id="corr-123")
    assert len(events) == 2
    assert events[0].id == e1.id
    assert events[1].causation_id == e1.id
