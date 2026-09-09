"""Evaluation runner for GAIA OS intent interpretation baseline."""

import asyncio
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from gaia.core.deterministic import RuleBasedInterpreter
from gaia.core.types import ConversationalResponse, ToolCall
from gaia.tools.registry import ToolRegistry

console = Console()
EVALS_FILE = Path(__file__).parent / "v001_intent_cases.json"


async def evaluate_dataset(interpreter: Any | None = None) -> dict[str, Any]:
    """Runs evaluation on v001_intent_cases.json and calculates accuracy."""
    if interpreter is None:
        interpreter = RuleBasedInterpreter()

    registry = ToolRegistry.with_default_tools()
    schemas = registry.get_schemas()

    cases = json.loads(EVALS_FILE.read_text(encoding="utf-8"))
    total = len(cases)
    tool_matches = 0
    arg_matches = 0
    eval_results = []

    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        expected_tool = case["expected_tool"]
        expected_args = case["expected_args"]

        result = await interpreter.interpret(user_input, schemas)

        actual_tool: str | None = None
        actual_args: dict[str, Any] = {}

        if isinstance(result, ToolCall):
            actual_tool = result.name
            actual_args = result.arguments
        elif isinstance(result, ConversationalResponse):
            actual_tool = None

        tool_correct = actual_tool == expected_tool
        if tool_correct:
            tool_matches += 1

        args_correct = True
        if expected_args is not None and tool_correct:
            for k, v in expected_args.items():
                if actual_args.get(k) != v:
                    args_correct = False
                    break
        elif expected_args is None and not tool_correct:
            args_correct = False

        if args_correct:
            arg_matches += 1

        eval_results.append(
            {
                "id": case_id,
                "input": user_input,
                "expected_tool": expected_tool,
                "actual_tool": actual_tool,
                "tool_correct": tool_correct,
                "args_correct": args_correct,
            }
        )

    tool_accuracy = (tool_matches / total) * 100.0
    arg_accuracy = (arg_matches / total) * 100.0

    return {
        "total": total,
        "tool_matches": tool_matches,
        "tool_accuracy_pct": tool_accuracy,
        "arg_matches": arg_matches,
        "arg_accuracy_pct": arg_accuracy,
        "details": eval_results,
    }


def main() -> None:
    results = asyncio.run(evaluate_dataset())

    table = Table(
        title="GAIA v0.1 Intent Evaluation Baseline", show_header=True, header_style="bold cyan"
    )
    table.add_column("Case ID", style="dim", no_wrap=True)
    table.add_column("Input Query")
    table.add_column("Expected Tool")
    table.add_column("Actual Tool")
    table.add_column("Status")

    for d in results["details"]:
        status = (
            "[bold green]PASS[/bold green]"
            if d["tool_correct"] and d["args_correct"]
            else "[bold red]FAIL[/bold red]"
        )
        table.add_row(
            d["id"],
            d["input"],
            str(d["expected_tool"]),
            str(d["actual_tool"]),
            status,
        )

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] Total Cases: {results['total']}")
    console.print(
        f"Tool Routing Accuracy: [bold green]{results['tool_accuracy_pct']:.1f}%[/bold green]"
    )
    console.print(
        f"Argument Precision: [bold green]{results['arg_accuracy_pct']:.1f}%[/bold green]"
    )


if __name__ == "__main__":
    main()
