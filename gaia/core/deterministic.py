"""Optional deterministic, rule-based intent interpreter for offline GAIA operations."""

import re
from typing import Any

from gaia.core.types import ConversationalResponse, InterpretationResult, ToolCall


class RuleBasedInterpreter:
    """Deterministic intent parser for offline demonstrations without an LLM."""

    async def interpret(
        self,
        user_text: str,
        _tools_schema: list[dict[str, Any]],
    ) -> InterpretationResult:
        text = user_text.strip()
        lower = text.lower()

        # 1. list_projects
        if lower in ("list projects", "projects", "show projects", "list project"):
            return ToolCall(name="list_projects", arguments={})

        # 2. get_current_context
        if lower in (
            "get current context",
            "get context",
            "current context",
            "context",
            "status",
            "show status",
        ):
            return ToolCall(name="get_current_context", arguments={})

        # 3. create_note: patterns like "create note <title>: <content>" or "create note <title> with content <content>"
        note_match = re.search(
            r"^create note (.*?)(?:\s+(?:with content|content|:)\s+(.*))?$",
            text,
            re.IGNORECASE,
        )
        if note_match:
            title = note_match.group(1).strip()
            content = note_match.group(2).strip() if note_match.group(2) else "No content provided."
            return ToolCall(name="create_note", arguments={"title": title, "content": content})

        # 4. create_idea: pattern like "create idea <title>"
        idea_match = re.search(r"^create idea (.*)$", text, re.IGNORECASE)
        if idea_match:
            rest = idea_match.group(1).strip()
            return ToolCall(name="create_idea", arguments={"title": rest, "description": ""})

        # 5. create_task: pattern like "create task <title>"
        task_match = re.search(r"^create task (.*)$", text, re.IGNORECASE)
        if task_match:
            rest = task_match.group(1).strip()
            priority = "medium"
            if "[high]" in lower:
                priority = "high"
                rest = re.sub(r"\[high\]", "", rest, flags=re.IGNORECASE).strip()
            elif "[low]" in lower:
                priority = "low"
                rest = re.sub(r"\[low\]", "", rest, flags=re.IGNORECASE).strip()
            return ToolCall(
                name="create_task",
                arguments={"title": rest, "priority": priority, "status": "todo"},
            )

        # Conversational fallback
        return ConversationalResponse(
            message=f"I heard: '{text}'. In offline rule-based mode, try 'create note <title> with content <content>', 'create idea <title>', 'create task <title>', 'list projects', or 'get current context'."
        )
