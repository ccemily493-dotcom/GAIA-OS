"""Unit tests for EventRecorder and event causality."""

import pytest

from gaia.domain.events import Actor, EventType
from gaia.events.recorder import EventRecorder
from gaia.storage.sqlite_repo import SqliteRepository


@pytest.fixture
async def repo() -> SqliteRepository:
    repository = SqliteRepository(":memory:")
    await repository.initialize()
    yield repository
    await repository.close()


@pytest.mark.asyncio
async def test_event_recorder_causation_chain(repo: SqliteRepository) -> None:
    recorder = EventRecorder(repo)
    corr_id = "txn-99"

    # Step 1: User message event
    e_user = await recorder.record(
        event_type=EventType.USER_MESSAGE,
        correlation_id=corr_id,
        actor=Actor.USER,
        payload={"query": "Make a note of the design"},
    )
    assert e_user.correlation_id == corr_id
    assert e_user.causation_id is None
    assert e_user.actor == Actor.USER

    # Step 2: Tool call event caused by user message
    e_tool = await recorder.record(
        event_type=EventType.TOOL_CALLED,
        correlation_id=corr_id,
        causation_id=e_user.id,
        actor=Actor.GAIA,
        payload={"tool": "create_note", "arguments": {"title": "Design"}},
    )
    assert e_tool.correlation_id == corr_id
    assert e_tool.causation_id == e_user.id
    assert e_tool.actor == Actor.GAIA

    # Step 3: Domain note created caused by tool call
    e_note = await recorder.record(
        event_type=EventType.NOTE_CREATED,
        correlation_id=corr_id,
        causation_id=e_tool.id,
        actor=Actor.SYSTEM,
        payload={"note_id": "note-123"},
    )
    assert e_note.correlation_id == corr_id
    assert e_note.causation_id == e_tool.id

    # Retrieve and verify chain
    chain = await recorder.get_events(correlation_id=corr_id)
    assert len(chain) == 3
    assert chain[0].id == e_user.id
    assert chain[1].causation_id == e_user.id
    assert chain[2].causation_id == e_tool.id
