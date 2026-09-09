"""Core GAIA OS runtime orchestrator implementing the end-to-end vertical slice."""

import time
import uuid
from dataclasses import dataclass
from typing import Any

from gaia.config.settings import GaiaSettings
from gaia.core.deterministic import RuleBasedInterpreter
from gaia.core.interpreter import IntentInterpreter
from gaia.core.service import GaiaAdminService
from gaia.core.types import ConversationalResponse, ToolCall
from gaia.domain.events import Actor, EventType
from gaia.events.recorder import EventRecorder
from gaia.logging.logger import correlation_id_var, get_logger
from gaia.models.fake_provider import FakeModelProvider
from gaia.models.openai_provider import OpenAICompatibleProvider
from gaia.storage.sqlite_repo import SqliteRepository
from gaia.tools.base import ToolContext
from gaia.tools.registry import ToolRegistry

logger = get_logger("gaia.runtime")


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeResult:
    """End-to-end execution outcome returned by GaiaRuntime."""

    response: str
    tool_called: str | None
    tool_result: Any | None
    success: bool
    correlation_id: str
    duration_ms: float
    error: str | None = None


class GaiaRuntime:
    """Core orchestrator executing user text through interpretation, tools, persistence, and events."""

    def __init__(
        self,
        repository: SqliteRepository,
        event_recorder: EventRecorder,
        tool_registry: ToolRegistry,
        interpreter: IntentInterpreter | RuleBasedInterpreter,
        admin_service: GaiaAdminService,
    ) -> None:
        self.repository = repository
        self.event_recorder = event_recorder
        self.tool_registry = tool_registry
        self.interpreter = interpreter
        self.admin_service = admin_service

    async def execute(
        self,
        user_text: str,
        correlation_id: str | None = None,
    ) -> RuntimeResult:
        """Executes the complete vertical slice for a user text input."""
        cid = correlation_id or str(uuid.uuid4())
        token = correlation_id_var.set(cid)
        start_time = time.perf_counter()

        logger.info("gaia_request_started", operation="execute", input_text=user_text)

        try:
            # Step 1: Append USER_MESSAGE event
            user_event = await self.event_recorder.record(
                event_type=EventType.USER_MESSAGE,
                correlation_id=cid,
                actor=Actor.USER,
                payload={"text": user_text},
            )

            # Step 2: Intent interpretation
            tools_schema = self.tool_registry.get_schemas()
            interpretation = await self.interpreter.interpret(user_text, tools_schema)

            # Step 3A: Conversational response (no tool invoked)
            if isinstance(interpretation, ConversationalResponse):
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                await self.event_recorder.record(
                    event_type=EventType.GAIA_RESPONSE,
                    correlation_id=cid,
                    causation_id=user_event.id,
                    actor=Actor.GAIA,
                    payload={"response": interpretation.message, "tool_called": None},
                )
                logger.info(
                    "gaia_request_completed",
                    operation="execute",
                    duration_ms=duration_ms,
                    tool_called=None,
                )
                return RuntimeResult(
                    response=interpretation.message,
                    tool_called=None,
                    tool_result=None,
                    success=True,
                    correlation_id=cid,
                    duration_ms=duration_ms,
                )

            # Step 3B: Tool proposed
            tool_call: ToolCall = interpretation
            tool_event = await self.event_recorder.record(
                event_type=EventType.TOOL_CALLED,
                correlation_id=cid,
                causation_id=user_event.id,
                actor=Actor.GAIA,
                payload={"tool": tool_call.name, "arguments": tool_call.arguments},
            )

            if not self.tool_registry.has_tool(tool_call.name):
                err_msg = f"Tool '{tool_call.name}' proposed by model is not registered."
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                await self.event_recorder.record(
                    event_type=EventType.ACTION_FAILED,
                    correlation_id=cid,
                    causation_id=tool_event.id,
                    actor=Actor.GAIA,
                    payload={"error": err_msg},
                )
                logger.error("gaia_request_failed", operation="execute", error=err_msg)
                return RuntimeResult(
                    response=err_msg,
                    tool_called=tool_call.name,
                    tool_result=None,
                    success=False,
                    correlation_id=cid,
                    duration_ms=duration_ms,
                    error=err_msg,
                )

            # Step 4: Execute tool with injected context
            tool = self.tool_registry.get_tool(tool_call.name)
            tool_context = ToolContext(
                correlation_id=cid,
                causation_id=tool_event.id,
                project_repo=self.repository,
                task_repo=self.repository,
                idea_repo=self.repository,
                note_repo=self.repository,
                state_repo=self.repository,
            )

            result = await tool.execute(tool_call.arguments, tool_context)

            # Step 5: Check tool execution outcome
            if not result.success:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                await self.event_recorder.record(
                    event_type=EventType.ACTION_FAILED,
                    correlation_id=cid,
                    causation_id=tool_event.id,
                    actor=Actor.GAIA,
                    payload={"tool": tool_call.name, "error": result.error},
                )
                logger.error(
                    "tool_execution_failed",
                    operation="execute",
                    tool=tool_call.name,
                    error=result.error,
                )
                return RuntimeResult(
                    response=f"Failed to execute '{tool_call.name}': {result.error}",
                    tool_called=tool_call.name,
                    tool_result=None,
                    success=False,
                    correlation_id=cid,
                    duration_ms=duration_ms,
                    error=result.error,
                )

            # Step 6: Record domain event if emitted by tool
            if result.event_type:
                await self.event_recorder.record(
                    event_type=result.event_type,
                    correlation_id=cid,
                    causation_id=tool_event.id,
                    actor=Actor.SYSTEM,
                    payload=result.event_payload or {},
                )

            # Step 7: Record final GAIA response
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            if isinstance(result.output, dict) and "message" in result.output:
                response_text = str(result.output["message"])
            else:
                response_text = str(result.output)

            await self.event_recorder.record(
                event_type=EventType.GAIA_RESPONSE,
                correlation_id=cid,
                causation_id=tool_event.id,
                actor=Actor.GAIA,
                payload={"response": response_text, "tool_called": tool_call.name},
            )

            logger.info(
                "gaia_request_completed",
                operation="execute",
                duration_ms=duration_ms,
                tool_called=tool_call.name,
            )

            return RuntimeResult(
                response=response_text,
                tool_called=tool_call.name,
                tool_result=result.output,
                success=True,
                correlation_id=cid,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("gaia_request_exception", operation="execute", error=str(e), exc_info=True)
            return RuntimeResult(
                response=f"An internal error occurred: {e}",
                tool_called=None,
                tool_result=None,
                success=False,
                correlation_id=cid,
                duration_ms=duration_ms,
                error=str(e),
            )
        finally:
            correlation_id_var.reset(token)

    @classmethod
    async def create(cls, settings: GaiaSettings | None = None) -> "GaiaRuntime":
        """Factory initializing storage, tools, interpreter, and admin service from settings."""
        cfg = settings or GaiaSettings()

        # Storage
        repo = SqliteRepository(cfg.database_path)
        await repo.initialize()

        # Events
        recorder = EventRecorder(repo)

        # Tools
        registry = ToolRegistry.with_default_tools()

        # Admin service
        admin = GaiaAdminService(
            project_repo=repo,
            task_repo=repo,
            state_repo=repo,
            event_recorder=recorder,
        )

        # Interpreter selection based on provider_type
        interpreter: IntentInterpreter | RuleBasedInterpreter
        if cfg.provider_type == "openai":
            provider = OpenAICompatibleProvider(
                base_url=cfg.openai_base_url,
                api_key=cfg.openai_api_key,
                model=cfg.openai_model,
                timeout_seconds=cfg.model_timeout_seconds,
            )
            interpreter = IntentInterpreter(model_provider=provider)
        elif cfg.provider_type == "fake":
            fake_provider = FakeModelProvider()
            interpreter = IntentInterpreter(model_provider=fake_provider)
        else:  # "rule_based" default offline
            interpreter = RuleBasedInterpreter()

        return cls(
            repository=repo,
            event_recorder=recorder,
            tool_registry=registry,
            interpreter=interpreter,
            admin_service=admin,
        )
