"""Unit tests for IntentInterpreter, FakeModelProvider, and RuleBasedInterpreter."""

import pytest

from gaia.core.deterministic import RuleBasedInterpreter
from gaia.core.interpreter import IntentInterpreter
from gaia.core.types import ConversationalResponse, ToolCall
from gaia.models.fake_provider import FakeModelProvider
from gaia.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_intent_interpreter_with_fake_provider() -> None:
    registry = ToolRegistry.with_default_tools()
    schemas = registry.get_schemas()

    # Scripted ToolCall
    scripted_call = ToolCall(
        name="create_note",
        arguments={"title": "Scripted Note", "content": "Deterministic text"},
    )
    fake_provider = FakeModelProvider(responses=[scripted_call])
    interpreter = IntentInterpreter(model_provider=fake_provider)

    result = await interpreter.interpret("Please save a note", schemas)
    assert isinstance(result, ToolCall)
    assert result.name == "create_note"
    assert result.arguments["title"] == "Scripted Note"

    # Scripted conversational message
    fake_provider.enqueue_response("Hello there! How can I help?")
    result_conv = await interpreter.interpret("Hi GAIA", schemas)
    assert isinstance(result_conv, ConversationalResponse)
    assert result_conv.message == "Hello there! How can I help?"


@pytest.mark.asyncio
async def test_rule_based_interpreter() -> None:
    interpreter = RuleBasedInterpreter()
    schemas = []

    # Note
    res_note = await interpreter.interpret("create note Arch with content Simple design", schemas)
    assert isinstance(res_note, ToolCall)
    assert res_note.name == "create_note"
    assert res_note.arguments["title"] == "Arch"
    assert res_note.arguments["content"] == "Simple design"

    # Idea
    res_idea = await interpreter.interpret("create idea Voice wake-up", schemas)
    assert isinstance(res_idea, ToolCall)
    assert res_idea.name == "create_idea"
    assert res_idea.arguments["title"] == "Voice wake-up"

    # Task with priority
    res_task = await interpreter.interpret("create task Fix sqlite foreign key [high]", schemas)
    assert isinstance(res_task, ToolCall)
    assert res_task.name == "create_task"
    assert res_task.arguments["title"] == "Fix sqlite foreign key"
    assert res_task.arguments["priority"] == "high"

    # List projects
    res_proj = await interpreter.interpret("list projects", schemas)
    assert isinstance(res_proj, ToolCall)
    assert res_proj.name == "list_projects"

    # Get context
    res_ctx = await interpreter.interpret("get context", schemas)
    assert isinstance(res_ctx, ToolCall)
    assert res_ctx.name == "get_current_context"

    # Fallback
    res_other = await interpreter.interpret("what is the weather?", schemas)
    assert isinstance(res_other, ConversationalResponse)
