"""End-to-end vertical slice integration tests for GAIA OS runtime."""

import pytest

from gaia.core.deterministic import RuleBasedInterpreter
from gaia.core.interpreter import IntentInterpreter
from gaia.core.runtime import GaiaRuntime
from gaia.core.service import GaiaAdminService
from gaia.core.types import ToolCall
from gaia.domain.events import EventType
from gaia.events.recorder import EventRecorder
from gaia.models.fake_provider import FakeModelProvider
from gaia.storage.sqlite_repo import SqliteRepository
from gaia.tools.registry import ToolRegistry


@pytest.fixture
async def memory_runtime() -> tuple[
    GaiaRuntime, SqliteRepository, EventRecorder, FakeModelProvider
]:
    repo = SqliteRepository(":memory:")
    await repo.initialize()
    recorder = EventRecorder(repo)
    registry = ToolRegistry.with_default_tools()
    fake_provider = FakeModelProvider()
    interpreter = IntentInterpreter(model_provider=fake_provider)
    admin = GaiaAdminService(repo, repo, repo, recorder)

    runtime = GaiaRuntime(
        repository=repo,
        event_recorder=recorder,
        tool_registry=registry,
        interpreter=interpreter,
        admin_service=admin,
    )
    return runtime, repo, recorder, fake_provider


@pytest.mark.asyncio
async def test_vertical_slice_create_note_end_to_end(
    memory_runtime: tuple[GaiaRuntime, SqliteRepository, EventRecorder, FakeModelProvider],
) -> None:
    runtime, repo, recorder, fake_provider = memory_runtime

    # 1. Script fake model to propose a create_note tool call
    fake_provider.enqueue_response(
        ToolCall(
            name="create_note",
            arguments={
                "title": "Test-Driven Architecture",
                "content": "I/O isolation is non-negotiable",
            },
        )
    )

    # 2. Execute user text through the runtime
    user_input = "Please take a note on test-driven architecture"
    result = await runtime.execute(user_input)

    # 3. Verify runtime output
    assert result.success is True
    assert result.tool_called == "create_note"
    assert "created successfully" in result.response
    assert result.duration_ms > 0
    cid = result.correlation_id

    # 4. Verify SQLite persistence
    notes = await repo.list_notes()
    assert len(notes) == 1
    assert notes[0].title == "Test-Driven Architecture"
    assert notes[0].content == "I/O isolation is non-negotiable"

    # 5. Verify Event Log with causality links
    events = await recorder.get_events(correlation_id=cid)
    assert len(events) == 4

    # Chain: USER_MESSAGE -> TOOL_CALLED -> NOTE_CREATED -> GAIA_RESPONSE
    e_user, e_tool, e_note, e_resp = events[0], events[1], events[2], events[3]

    assert e_user.event_type == EventType.USER_MESSAGE
    assert e_user.causation_id is None

    assert e_tool.event_type == EventType.TOOL_CALLED
    assert e_tool.causation_id == e_user.id
    assert e_tool.payload["tool"] == "create_note"

    assert e_note.event_type == EventType.NOTE_CREATED
    assert e_note.causation_id == e_tool.id
    assert e_note.payload["title"] == "Test-Driven Architecture"

    assert e_resp.event_type == EventType.GAIA_RESPONSE
    assert e_resp.causation_id == e_tool.id


@pytest.mark.asyncio
async def test_vertical_slice_conversational_response(
    memory_runtime: tuple[GaiaRuntime, SqliteRepository, EventRecorder, FakeModelProvider],
) -> None:
    runtime, repo, recorder, fake_provider = memory_runtime

    # Script fake model with conversational text (no tool calls)
    fake_provider.enqueue_response("Hello! I am GAIA. How can I support your work today?")

    result = await runtime.execute("Hello GAIA")

    assert result.success is True
    assert result.tool_called is None
    assert "Hello! I am GAIA" in result.response

    # Verify events
    events = await recorder.get_events(correlation_id=result.correlation_id)
    assert len(events) == 2
    assert events[0].event_type == EventType.USER_MESSAGE
    assert events[1].event_type == EventType.GAIA_RESPONSE
    assert events[1].causation_id == events[0].id


@pytest.mark.asyncio
async def test_vertical_slice_invalid_arguments_rejection(
    memory_runtime: tuple[GaiaRuntime, SqliteRepository, EventRecorder, FakeModelProvider],
) -> None:
    runtime, repo, recorder, fake_provider = memory_runtime

    # Script fake model to propose invalid arguments (missing required 'content' field)
    fake_provider.enqueue_response(
        ToolCall(
            name="create_note",
            arguments={"title": "Note Without Content"},
        )
    )

    result = await runtime.execute("save note")

    assert result.success is False
    assert result.tool_called == "create_note"
    assert "Invalid arguments" in result.response

    # Verify nothing was persisted to database
    notes = await repo.list_notes()
    assert len(notes) == 0

    # Verify failure event recorded
    events = await recorder.get_events(correlation_id=result.correlation_id)
    assert any(e.event_type == EventType.ACTION_FAILED for e in events)


@pytest.mark.asyncio
async def test_vertical_slice_with_rule_based_interpreter() -> None:
    repo = SqliteRepository(":memory:")
    await repo.initialize()
    recorder = EventRecorder(repo)
    registry = ToolRegistry.with_default_tools()
    interpreter = RuleBasedInterpreter()
    admin = GaiaAdminService(repo, repo, repo, recorder)

    runtime = GaiaRuntime(
        repository=repo,
        event_recorder=recorder,
        tool_registry=registry,
        interpreter=interpreter,
        admin_service=admin,
    )

    # Deterministic create_task
    res = await runtime.execute("create task Implement whisper.cpp audio layer [high]")
    assert res.success is True
    assert res.tool_called == "create_task"

    tasks = await repo.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Implement whisper.cpp audio layer"
    assert tasks[0].priority == "high"
