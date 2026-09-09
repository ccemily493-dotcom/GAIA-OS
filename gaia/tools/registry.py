"""Tool registry for registering and discovering GAIA OS typed tools."""

from typing import Any

from gaia.domain.exceptions import ToolExecutionError
from gaia.tools.base import BaseTool
from gaia.tools.builtin import (
    CreateIdeaTool,
    CreateNoteTool,
    CreateTaskTool,
    GetCurrentContextTool,
    ListProjectsTool,
)


class ToolRegistry:
    """Registry holding available typed tools in the GAIA system."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers a typed tool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Returns a registered tool by name."""
        if name not in self._tools:
            raise ToolExecutionError(name, f"Tool '{name}' is not registered in GAIA.")
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Checks if a tool exists."""
        return name in self._tools

    def list_tools(self) -> list[BaseTool]:
        """Returns all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Returns OpenAI/JSON-Schema compatible specifications for all registered tools."""
        schemas: list[dict[str, Any]] = []
        for tool in self._tools.values():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_model.model_json_schema(),
                    },
                }
            )
        return schemas

    @classmethod
    def with_default_tools(cls) -> "ToolRegistry":
        """Factory initializing a registry with the standard 5 v0.1 tools."""
        registry = cls()
        registry.register(CreateNoteTool())
        registry.register(CreateIdeaTool())
        registry.register(CreateTaskTool())
        registry.register(ListProjectsTool())
        registry.register(GetCurrentContextTool())
        return registry
