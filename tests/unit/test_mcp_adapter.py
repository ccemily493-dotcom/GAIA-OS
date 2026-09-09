"""Unit tests for McpToolAdapter."""

import json

import pytest

from gaia.mcp.adapter import McpToolAdapter
from gaia.storage.sqlite_repo import SqliteRepository
from gaia.tools.base import ToolContext
from gaia.tools.registry import ToolRegistry


@pytest.fixture
async def tool_context() -> ToolContext:
    repo = SqliteRepository(":memory:")
    await repo.initialize()
    return ToolContext(
        correlation_id="mcp-corr",
        causation_id=None,
        project_repo=repo,
        task_repo=repo,
        idea_repo=repo,
        note_repo=repo,
        state_repo=repo,
    )


def test_mcp_tool_schema_export() -> None:
    registry = ToolRegistry.with_default_tools()
    mcp_tools = McpToolAdapter.list_mcp_tools(registry)
    assert len(mcp_tools) == 5

    note_tool = next(t for t in mcp_tools if t["name"] == "create_note")
    assert "inputSchema" in note_tool
    assert note_tool["inputSchema"]["type"] == "object"
    assert "properties" in note_tool["inputSchema"]
    assert "title" in note_tool["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_mcp_tool_execution(tool_context: ToolContext) -> None:
    registry = ToolRegistry.with_default_tools()

    # Successful MCP call
    res = await McpToolAdapter.handle_mcp_call(
        registry=registry,
        context=tool_context,
        name="create_note",
        arguments={"title": "MCP Note", "content": "Created via MCP protocol"},
    )
    assert res["isError"] is False
    assert len(res["content"]) == 1
    output = json.loads(res["content"][0]["text"])
    assert output["title"] == "MCP Note"

    # Unknown tool call
    res_unknown = await McpToolAdapter.handle_mcp_call(
        registry=registry,
        context=tool_context,
        name="unknown_tool",
    )
    assert res_unknown["isError"] is True
    assert "not registered" in res_unknown["content"][0]["text"]
