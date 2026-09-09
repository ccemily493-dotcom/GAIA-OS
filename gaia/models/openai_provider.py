"""OpenAI-compatible HTTP model provider for Ollama, vLLM, and cloud APIs."""

import json
from typing import Any

import httpx

from gaia.domain.exceptions import ModelProviderError
from gaia.models.base import ChatMessage, ModelCompletion, ModelProvider, ToolCall


class OpenAICompatibleProvider(ModelProvider):
    """Interacts with OpenAI-compatible chat completion APIs (Ollama, OpenAI, Groq, etc.)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        model: str = "llama3.2",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> ModelCompletion:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            raise ModelProviderError(f"HTTP error communicating with model provider: {e}") from e
        except Exception as e:
            raise ModelProviderError(
                f"Unexpected error communicating with model provider: {e}"
            ) from e

        choices = data.get("choices", [])
        if not choices:
            return ModelCompletion(raw_content=None, tool_calls=[])

        message_data = choices[0].get("message", {})
        raw_content = message_data.get("content")
        raw_tool_calls = message_data.get("tool_calls") or []

        parsed_tool_calls: list[ToolCall] = []
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            args_raw = func.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except json.JSONDecodeError:
                args = {}
            parsed_tool_calls.append(ToolCall(name=name, arguments=args))

        return ModelCompletion(
            raw_content=raw_content,
            tool_calls=parsed_tool_calls,
        )
