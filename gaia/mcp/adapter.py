"""MCP (Model Context Protocol) adapter boundary.

Translates GAIA internal typed tools to and from standard Model Context Protocol
tool descriptors and execution schemas without coupling GAIA Core to external MCP libraries.
"""

import json
from typing import Any

from gaia.tools.base import BaseTool, ToolContext
from gaia.tools.registry import ToolRegistry


class McpToolAdapter:
    """Protocol adapter translating GAIA tools to/from MCP format."""

    @staticmethod
    def to_mcp_tool_definition(tool: BaseTool) -> dict[str, Any]:
        """Converts a GAIA BaseTool into an MCP Tool specification.

        Standard MCP Tool schema:
        {
            "name": str,
            "description": str,
            "inputSchema": dict (JSON Schema)
        }
        """
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_model.model_json_schema(),
        }

    @classmethod
    def list_mcp_tools(cls, registry: ToolRegistry) -> list[dict[str, Any]]:
        """Exports all registered GAIA tools as a list of MCP tool definitions."""
        return [cls.to_mcp_tool_definition(t) for t in registry.list_tools()]

    @staticmethod
    async def handle_mcp_call(
        registry: ToolRegistry,
        context: ToolContext,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes a tool call requested in MCP format and returns an MCP-compliant response.

        Standard MCP CallToolResult schema:
        {
            "content": [{"type": "text", "text": str}],
            "isError": bool
        }
        """
        if not registry.has_tool(name):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Tool '{name}' is not registered in GAIA.",
                    }
                ],
                "isError": True,
            }

        tool = registry.get_tool(name)
        result = await tool.execute(arguments or {}, context)

        if not result.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool '{name}': {result.error}",
                    }
                ],
                "isError": True,
            }

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result.output, indent=2),
                }
            ],
            "isError": False,
        }
