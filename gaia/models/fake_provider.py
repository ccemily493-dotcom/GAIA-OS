"""Scripted fake model provider for deterministic unit and integration testing."""

from typing import Any

from gaia.models.base import ChatMessage, ModelCompletion, ModelProvider, ToolCall


class FakeModelProvider(ModelProvider):
    """Explicitly scripted fake model provider for deterministic testing."""

    def __init__(
        self,
        responses: list[ModelCompletion | ToolCall | str] | None = None,
    ) -> None:
        self._queue: list[ModelCompletion] = []
        self.recorded_calls: list[tuple[list[ChatMessage], list[dict[str, Any]] | None]] = []

        if responses:
            for item in responses:
                self.enqueue_response(item)

    def enqueue_response(self, response: ModelCompletion | ToolCall | str) -> None:
        """Queues a scripted response for subsequent completion calls."""
        if isinstance(response, ModelCompletion):
            self._queue.append(response)
        elif isinstance(response, ToolCall):
            self._queue.append(ModelCompletion(raw_content=None, tool_calls=[response]))
        elif isinstance(response, str):
            self._queue.append(ModelCompletion(raw_content=response, tool_calls=[]))
        else:
            raise TypeError(f"Unsupported fake response type: {type(response)}")

    async def complete(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelCompletion:
        """Returns the next scripted response from the queue."""
        self.recorded_calls.append((messages, tools))

        if not self._queue:
            # Default fallback if queue exhausted
            return ModelCompletion(
                raw_content="I am ready to assist you.",
                tool_calls=[],
            )

        return self._queue.pop(0)
