"""Unit tests for domain entities, state, context packets, and events."""

import pytest
from pydantic import ValidationError

from gaia.domain.context import ContextPacket
from gaia.domain.entities import Decision, Idea, Note, Project, Task
from gaia.domain.events import Actor, Event, EventType
from gaia.domain.state import CurrentState


def test_project_creation_and_validation() -> None:
    project = Project(name="GAIA Core", description="Primary assistant engine")
    assert project.name == "GAIA Core"
    assert project.status == "active"
    assert project.id is not None
    assert project.created_at is not None

    with pytest.raises(ValidationError):
        Project(name="")

    with pytest.raises(ValidationError):
        Project(name="   ")

    with pytest.raises(ValidationError):
        Project(name="Invalid Status", status="unknown_status")


def test_task_creation_and_validation() -> None:
    task = Task(title="Build SQLite persistence", priority="high", status="todo")
    assert task.title == "Build SQLite persistence"
    assert task.priority == "high"
    assert task.status == "todo"
    assert task.project_id is None

    with pytest.raises(ValidationError):
        Task(title="   ")

    with pytest.raises(ValidationError):
        Task(title="Invalid Priority", priority="urgent")


def test_idea_and_note_creation() -> None:
    idea = Idea(title="Voice interface via Piper", tags=["voice", "tts"])
    assert idea.title == "Voice interface via Piper"
    assert "tts" in idea.tags

    note = Note(title="Architecture Notes", content="I/O isolation is key", tags=["arch"])
    assert note.title == "Architecture Notes"
    assert note.content == "I/O isolation is key"

    with pytest.raises(ValidationError):
        Note(title="Empty Content", content="")


def test_decision_creation() -> None:
    decision = Decision(
        title="Use SQLite for v0.1",
        rationale="Simplicity, zero-infrastructure, testability",
        status="accepted",
    )
    assert decision.status == "accepted"
    assert "Simplicity" in decision.rationale


def test_context_packet_minimal_schema() -> None:
    packet = ContextPacket(
        source="ide",
        type="active_file",
        payload={"path": "gaia/core/runtime.py", "cursor_line": 42},
        priority=10,
    )
    assert packet.source == "ide"
    assert packet.priority == 10
    assert packet.payload["cursor_line"] == 42


def test_current_state_schema() -> None:
    state = CurrentState(
        current_project_id="proj-123",
        current_task_id="task-456",
        active_app="VSCode",
        active_agent="antigravity",
    )
    assert state.current_project_id == "proj-123"
    assert state.active_agent == "antigravity"


def test_event_causality_and_correlation() -> None:
    user_event = Event(
        event_type=EventType.USER_MESSAGE,
        correlation_id="corr-1",
        actor=Actor.USER,
        payload={"text": "create note test"},
    )
    tool_event = Event(
        event_type=EventType.TOOL_CALLED,
        correlation_id="corr-1",
        causation_id=user_event.id,
        actor=Actor.GAIA,
        payload={"tool": "create_note"},
    )
    note_event = Event(
        event_type=EventType.NOTE_CREATED,
        correlation_id="corr-1",
        causation_id=tool_event.id,
        actor=Actor.SYSTEM,
        payload={"note_id": "note-1"},
    )

    assert user_event.correlation_id == tool_event.correlation_id == note_event.correlation_id
    assert tool_event.causation_id == user_event.id
    assert note_event.causation_id == tool_event.id
    assert user_event.actor == Actor.USER
    assert tool_event.actor == Actor.GAIA
