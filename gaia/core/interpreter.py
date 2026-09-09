"""Intent interpreter for mapping natural language user input to tool calls or conversational responses."""

from typing import Any

from gaia.core.types import ConversationalResponse, InterpretationResult
from gaia.models.base import ChatMessage, ModelProvider

DEFAULT_SYSTEM_PROMPT = """You are GAIA (General Autonomous Intelligent Assistant), a modular personal assistant.
Your responsibility is to interpret user input and invoke the appropriate tool with clean, validated arguments when an action is requested.
Available actions include:
- create_note: Save knowledge, thoughts, or documentation.
- create_idea: Record unrefined thoughts, suggestions, or potential future items.
- create_task: Add an actionable item with priority and status.
- list_projects: View existing projects.
- get_current_context: Check active project, task, and recent context.

If the user request does not require any tool, respond helpfully and concisely as a conversational response.
"""


class IntentInterpreter:
    """Interprets user intent using a ModelProvider and registered tool schemas."""

    def __init__(
        self,
        model_provider: ModelProvider,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.model_provider = model_provider
        self.system_prompt = system_prompt

    async def interpret(
        self,
        user_text: str,
        tools_schema: list[dict[str, Any]],
    ) -> InterpretationResult:
        """Interprets user text and returns either a ToolCall or a ConversationalResponse."""
        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(role="user", content=user_text),
        ]

        completion = await self.model_provider.complete(messages, tools=tools_schema)

        if completion.tool_calls:
            # Model proposed one or more tool calls; take primary tool call
            return completion.tool_calls[0]

        message = completion.raw_content or "I processed your request, but no action was needed."
        return ConversationalResponse(message=message)
