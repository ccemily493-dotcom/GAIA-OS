"""Interactive REPL shell for GAIA OS."""

import asyncio

from rich.console import Console
from rich.panel import Panel

from gaia.core.runtime import GaiaRuntime

console = Console()


async def run_repl(runtime: GaiaRuntime) -> None:
    """Runs the interactive GAIA OS REPL loop."""
    console.print(
        Panel.fit(
            "[bold cyan]GAIA OS v0.1[/bold cyan] — Personal Assistant Shell\n"
            "[dim]Type your command or request. Type [bold]exit[/bold] or [bold]quit[/bold] to leave.[/dim]",
            border_style="cyan",
        )
    )

    while True:
        try:
            # Check current state for prompt
            state = await runtime.admin_service.get_state()
            active_proj_name = "None"
            if state.current_project_id:
                proj = await runtime.repository.get_project(state.current_project_id)
                if proj:
                    active_proj_name = proj.name

            prompt_text = f"[bold green]gaia[/bold green] [dim]({active_proj_name})[/dim]> "
            user_input = console.input(prompt_text).strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", ":q"):
                console.print("[dim]Exiting GAIA OS. Goodbye![/dim]")
                break

            result = await runtime.execute(user_input)

            if result.success:
                if result.tool_called:
                    console.print(
                        f"[bold green][OK] [{result.tool_called}][/bold green] {result.response}"
                    )
                else:
                    console.print(f"[bold cyan]GAIA:[/bold cyan] {result.response}")
            else:
                console.print(f"[bold red][ERROR][/bold red] {result.response}")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session terminated. Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected REPL error:[/bold red] {e}")


def start_repl(runtime: GaiaRuntime) -> None:
    """Synchronous launcher for REPL."""
    asyncio.run(run_repl(runtime))
