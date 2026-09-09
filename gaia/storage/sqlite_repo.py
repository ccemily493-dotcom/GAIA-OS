"""SQLite implementation of GAIA persistence protocols using aiosqlite."""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite

from gaia.domain.context import ContextPacket
from gaia.domain.entities import Decision, Idea, Note, Project, Task
from gaia.domain.events import Actor, Event, EventType
from gaia.domain.state import CurrentState
from gaia.storage.runner import run_migrations


class SqliteRepository:
    """Async SQLite persistence adapter for GAIA OS."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._shared_conn: aiosqlite.Connection | None = None

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[aiosqlite.Connection]:
        """Provides a managed connection to SQLite."""
        if self.db_path == ":memory:":
            if self._shared_conn is None:
                self._shared_conn = await aiosqlite.connect(self.db_path)
                self._shared_conn.row_factory = aiosqlite.Row
                await self._shared_conn.execute("PRAGMA foreign_keys = ON;")
            yield self._shared_conn
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                await conn.execute("PRAGMA foreign_keys = ON;")
                yield conn

    async def initialize(self) -> None:
        """Applies database migrations."""
        async with self.connect() as conn:
            await run_migrations(conn)

    async def close(self) -> None:
        """Closes memory connection if open."""
        if self._shared_conn is not None:
            await self._shared_conn.close()
            self._shared_conn = None

    # --- ProjectRepository ---

    async def create_project(self, project: Project) -> Project:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO projects (id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    project.id,
                    project.name,
                    project.description,
                    project.status,
                    project.created_at,
                    project.updated_at,
                ),
            )
            await conn.commit()
        return project

    async def get_project(self, project_id: str) -> Project | None:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_projects(self, status: str | None = None) -> list[Project]:
        async with self.connect() as conn:
            if status:
                cursor = await conn.execute(
                    "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC;",
                    (status,),
                )
            else:
                cursor = await conn.execute("SELECT * FROM projects ORDER BY created_at DESC;")
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                Project(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- TaskRepository ---

    async def create_task(self, task: Task) -> Task:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO tasks (id, project_id, title, description, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    task.id,
                    task.project_id,
                    task.title,
                    task.description,
                    task.status,
                    task.priority,
                    task.created_at,
                    task.updated_at,
                ),
            )
            await conn.commit()
        return task

    async def get_task(self, task_id: str) -> Task | None:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            return Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_tasks(
        self, project_id: str | None = None, status: str | None = None
    ) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC;"

        async with self.connect() as conn, conn.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
            return [
                Task(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    description=r["description"],
                    status=r["status"],
                    priority=r["priority"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- IdeaRepository ---

    async def create_idea(self, idea: Idea) -> Idea:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO ideas (id, project_id, title, description, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    idea.id,
                    idea.project_id,
                    idea.title,
                    idea.description,
                    json.dumps(idea.tags),
                    idea.created_at,
                    idea.updated_at,
                ),
            )
            await conn.commit()
        return idea

    async def get_idea(self, idea_id: str) -> Idea | None:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM ideas WHERE id = ?;", (idea_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            return Idea(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_ideas(self, project_id: str | None = None) -> list[Idea]:
        async with self.connect() as conn:
            if project_id:
                cursor = await conn.execute(
                    "SELECT * FROM ideas WHERE project_id = ? ORDER BY created_at DESC;",
                    (project_id,),
                )
            else:
                cursor = await conn.execute("SELECT * FROM ideas ORDER BY created_at DESC;")
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                Idea(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    description=r["description"],
                    tags=json.loads(r["tags"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- NoteRepository ---

    async def create_note(self, note: Note) -> Note:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO notes (id, project_id, title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    note.id,
                    note.project_id,
                    note.title,
                    note.content,
                    json.dumps(note.tags),
                    note.created_at,
                    note.updated_at,
                ),
            )
            await conn.commit()
        return note

    async def get_note(self, note_id: str) -> Note | None:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM notes WHERE id = ?;", (note_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            return Note(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                content=row["content"],
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_notes(self, project_id: str | None = None) -> list[Note]:
        async with self.connect() as conn:
            if project_id:
                cursor = await conn.execute(
                    "SELECT * FROM notes WHERE project_id = ? ORDER BY created_at DESC;",
                    (project_id,),
                )
            else:
                cursor = await conn.execute("SELECT * FROM notes ORDER BY created_at DESC;")
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                Note(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    content=r["content"],
                    tags=json.loads(r["tags"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- DecisionRepository ---

    async def create_decision(self, decision: Decision) -> Decision:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO decisions (id, project_id, title, rationale, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    decision.id,
                    decision.project_id,
                    decision.title,
                    decision.rationale,
                    decision.status,
                    decision.created_at,
                    decision.updated_at,
                ),
            )
            await conn.commit()
        return decision

    async def get_decision(self, decision_id: str) -> Decision | None:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM decisions WHERE id = ?;", (decision_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return None
            return Decision(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                rationale=row["rationale"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list_decisions(self, project_id: str | None = None) -> list[Decision]:
        async with self.connect() as conn:
            if project_id:
                cursor = await conn.execute(
                    "SELECT * FROM decisions WHERE project_id = ? ORDER BY created_at DESC;",
                    (project_id,),
                )
            else:
                cursor = await conn.execute("SELECT * FROM decisions ORDER BY created_at DESC;")
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                Decision(
                    id=r["id"],
                    project_id=r["project_id"],
                    title=r["title"],
                    rationale=r["rationale"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- StateRepository ---

    async def get_current_state(self) -> CurrentState:
        async with (
            self.connect() as conn,
            conn.execute("SELECT * FROM current_state WHERE singleton_id = 1;") as cursor,
        ):
            row = await cursor.fetchone()
            if not row:
                return CurrentState()
            return CurrentState(
                current_project_id=row["current_project_id"],
                current_task_id=row["current_task_id"],
                active_app=row["active_app"],
                active_agent=row["active_agent"],
                last_action_timestamp=row["last_action_timestamp"],
            )

    async def update_current_state(self, state: CurrentState) -> CurrentState:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO current_state (singleton_id, current_project_id, current_task_id, active_app, active_agent, last_action_timestamp)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    current_project_id = excluded.current_project_id,
                    current_task_id = excluded.current_task_id,
                    active_app = excluded.active_app,
                    active_agent = excluded.active_agent,
                    last_action_timestamp = excluded.last_action_timestamp;
                """,
                (
                    state.current_project_id,
                    state.current_task_id,
                    state.active_app,
                    state.active_agent,
                    state.last_action_timestamp,
                ),
            )
            await conn.commit()
        return state

    async def append_context_packet(self, packet: ContextPacket) -> ContextPacket:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO context_packets (id, source, type, payload, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    packet.id,
                    packet.source,
                    packet.type,
                    json.dumps(packet.payload),
                    packet.priority,
                    packet.created_at,
                ),
            )
            await conn.commit()
        return packet

    async def get_recent_context_packets(self, limit: int = 10) -> list[ContextPacket]:
        async with (
            self.connect() as conn,
            conn.execute(
                "SELECT * FROM context_packets ORDER BY created_at DESC LIMIT ?;",
                (limit,),
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            return [
                ContextPacket(
                    id=r["id"],
                    source=r["source"],
                    type=r["type"],
                    payload=json.loads(r["payload"]),
                    priority=r["priority"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- EventRepository ---

    async def append_event(self, event: Event) -> Event:
        async with self.connect() as conn:
            await conn.execute(
                """
                INSERT INTO events (id, event_type, correlation_id, causation_id, actor, payload, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event.id,
                    str(event.event_type),
                    event.correlation_id,
                    event.causation_id,
                    str(event.actor),
                    json.dumps(event.payload),
                    event.timestamp,
                ),
            )
            await conn.commit()
        return event

    async def get_events(self, correlation_id: str | None = None, limit: int = 100) -> list[Event]:
        async with self.connect() as conn:
            if correlation_id:
                cursor = await conn.execute(
                    "SELECT * FROM events WHERE correlation_id = ? ORDER BY timestamp ASC LIMIT ?;",
                    (correlation_id, limit),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM events ORDER BY timestamp ASC LIMIT ?;",
                    (limit,),
                )
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                Event(
                    id=r["id"],
                    event_type=EventType(r["event_type"])
                    if r["event_type"] in EventType.__members__
                    else r["event_type"],
                    correlation_id=r["correlation_id"],
                    causation_id=r["causation_id"],
                    actor=Actor(r["actor"]) if r["actor"] in Actor.__members__ else r["actor"],
                    payload=json.loads(r["payload"]),
                    timestamp=r["timestamp"],
                )
                for r in rows
            ]
