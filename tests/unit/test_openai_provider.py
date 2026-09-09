"""Unit tests for OpenAICompatibleProvider using httpx.MockTransport."""

import json

import httpx
import pytest

from gaia.domain.exceptions import ModelProviderError
from gaia.models.base import ChatMessage
from gaia.models.openai_provider import OpenAICompatibleProvider


@pytest.mark.asyncio
async def test_openai_provider_tool_call_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "create_note",
                                    "arguments": json.dumps(
                                        {"title": "Mock Note", "content": "From mock HTTP"}
                                    ),
                                }
                            }
                        ],
                    }
                }
            ]
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatibleProvider(base_url="http://mock-llm/v1")

    # Patch AsyncClient to use mock transport
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):
        kwargs["transport"] = transport
        return original_client(**kwargs)

    import gaia.models.openai_provider as op_module

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(op_module.httpx, "AsyncClient", mock_client)

    try:
        messages = [ChatMessage(role="user", content="Take note")]
        tools = [{"type": "function", "function": {"name": "create_note"}}]
        completion = await provider.complete(messages, tools)

        assert len(completion.tool_calls) == 1
        assert completion.tool_calls[0].name == "create_note"
        assert completion.tool_calls[0].arguments["title"] == "Mock Note"
    finally:
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_openai_provider_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Internal Server Error"})

    transport = httpx.MockTransport(handler)
    provider = OpenAICompatibleProvider(base_url="http://mock-llm/v1")

    original_client = httpx.AsyncClient

    def mock_client(**kwargs):
        kwargs["transport"] = transport
        return original_client(**kwargs)

    import gaia.models.openai_provider as op_module

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(op_module.httpx, "AsyncClient", mock_client)

    try:
        messages = [ChatMessage(role="user", content="Hello")]
        with pytest.raises(ModelProviderError):
            await provider.complete(messages)
    finally:
        monkeypatch.undo()
