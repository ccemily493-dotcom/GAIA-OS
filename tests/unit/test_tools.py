"""Unit tests for GAIA OS typed tools."""

import pytest

from gaia.domain.context import ContextPacket
from gaia.domain.entities import Project, Task
from gaia.domain.state import CurrentState
from gaia.storage.sqlite_repo import SqliteRepository
from gaia.tools.base import ToolContext
from gaia.tools.builtin import (
    CreateIdeaTool,
    CreateNoteTool,
    CreateTaskTool,
    GetCurrentContextTool,
    ListProjectsTool,
)
from gaia.tools.registry import ToolRegistry


@pytest.fixture
async def tool_context() -> ToolContext:
    repo = SqliteRepository(":memory:")
    await repo.initialize()
    return ToolContext(
        correlation_id="test-corr",
        causation_id=None,
        project_repo=repo,
        task_repo=repo,
        idea_repo=repo,
        note_repo=repo,
        state_repo=repo,
    )


@pytest.mark.asyncio
async def test_create_note_tool_success_and_invalid(tool_context: ToolContext) -> None:
    tool = CreateNoteTool()

    # Success
    res = await tool.execute(
        {"title": "Meeting Notes", "content": "Discussed roadmap", "tags": ["meeting"]},
        tool_context,
    )
    assert res.success is True
    assert res.output["title"] == "Meeting Notes"
    assert res.event_type is not None

    # Invalid arguments (missing required content)
    res_err = await tool.execute({"title": "No Content"}, tool_context)
    assert res_err.success is False
    assert "Invalid arguments" in res_err.error

    # Non-existent project
    res_proj_err = await tool.execute(
        {"title": "Note", "content": "Text", "project_id": "non-existent-id"},
        tool_context,
    )
    assert res_proj_err.success is False
    assert "does not exist" in res_proj_err.error


@pytest.mark.asyncio
async def test_create_idea_tool(tool_context: ToolContext) -> None:
    tool = CreateIdeaTool()
    res = await tool.execute(
        {"title": "Agent Bridge concept", "description": "Connect to Codex", "tags": ["agents"]},
        tool_context,
    )
    assert res.success is True
    assert res.output["title"] == "Agent Bridge concept"
    assert "Idea 'Agent Bridge concept' recorded successfully." in res.output["message"]


@pytest.mark.asyncio
async def test_create_task_tool(tool_context: ToolContext) -> None:
    tool = CreateTaskTool()
    res = await tool.execute(
        {"title": "Build REPL", "priority": "high", "status": "todo"},
        tool_context,
    )
    assert res.success is True
    assert res.output["priority"] == "high"

    # Invalid priority
    res_err = await tool.execute({"title": "Invalid", "priority": "blazing"}, tool_context)
    assert res_err.success is False


@pytest.mark.asyncio
async def test_list_projects_tool(tool_context: ToolContext) -> None:
    p1 = Project(name="Project 1", status="active")
    p2 = Project(name="Project 2", status="archived")
    await tool_context.project_repo.create_project(p1)
    await tool_context.project_repo.create_project(p2)

    tool = ListProjectsTool()
    res_all = await tool.execute({}, tool_context)
    assert res_all.success is True
    assert res_all.output["count"] == 2

    res_active = await tool.execute({"status": "active"}, tool_context)
    assert res_active.success is True
    assert res_active.output["count"] == 1
    assert res_active.output["projects"][0]["name"] == "Project 1"


@pytest.mark.asyncio
async def test_get_current_context_tool(tool_context: ToolContext) -> None:
    proj = await tool_context.project_repo.create_project(Project(name="Active Proj"))
    task = await tool_context.task_repo.create_task(Task(project_id=proj.id, title="Active Task"))
    await tool_context.state_repo.update_current_state(
        CurrentState(
            current_project_id=proj.id,
            current_task_id=task.id,
            active_app="Terminal",
            active_agent="gaia",
        )
    )
    await tool_context.state_repo.append_context_packet(
        ContextPacket(source="test", type="info", payload={"status": "running"})
    )

    tool = GetCurrentContextTool()
    res = await tool.execute({}, tool_context)
    assert res.success is True
    assert res.output["current_project"]["name"] == "Active Proj"
    assert res.output["current_task"]["title"] == "Active Task"
    assert len(res.output["recent_context_packets"]) == 1


def test_tool_registry() -> None:
    registry = ToolRegistry.with_default_tools()
    assert len(registry.list_tools()) == 5
    assert registry.has_tool("create_note")
    assert registry.has_tool("create_idea")
    assert registry.has_tool("create_task")
    assert registry.has_tool("list_projects")
    assert registry.has_tool("get_current_context")

    schemas = registry.get_schemas()
    assert len(schemas) == 5
    names = [s["function"]["name"] for s in schemas]
    assert "create_note" in names
