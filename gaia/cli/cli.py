"""Command-line interface dispatcher for GAIA OS."""

import asyncio
import sys

import click
from rich.console import Console
from rich.table import Table

from gaia.config.settings import GaiaSettings
from gaia.core.runtime import GaiaRuntime
from gaia.logging.logger import configure_logging

console = Console()


async def _get_runtime() -> GaiaRuntime:
    settings = GaiaSettings()
    configure_logging(settings.log_level)
    return await GaiaRuntime.create(settings)


class NaturalLanguageGroup(click.Group):
    """Custom Click Group that routes unparsed commands to the natural language runner."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        return None

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if not args:
            return None, None, []
        if args[0] in self.commands:
            return super().resolve_command(ctx, args)

        # Unrecognized first token: treat entire args sequence as a natural language query
        return "query", self.commands["query"], args


@click.group(cls=NaturalLanguageGroup, invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """GAIA OS — Voice-first personal assistant runtime."""
    if ctx.invoked_subcommand is None:
        # No command provided: launch interactive REPL
        runtime = asyncio.run(_get_runtime())
        from gaia.cli.repl import run_repl

        asyncio.run(run_repl(runtime))


@main.command("query", hidden=True)
@click.argument("words", nargs=-1, required=True)
def query_command(words: tuple[str, ...]) -> None:
    """Execute a single-shot natural language query."""
    runtime = asyncio.run(_get_runtime())
    query_text = " ".join(words).strip()
    result = asyncio.run(runtime.execute(query_text))

    if result.success:
        if result.tool_called:
            console.print(f"[bold green][OK] [{result.tool_called}][/bold green] {result.response}")
        else:
            console.print(f"[bold cyan]GAIA:[/bold cyan] {result.response}")
        sys.exit(0)
    else:
        console.print(f"[bold red][ERROR][/bold red] {result.response}")
        sys.exit(1)


@main.group("project")
def project() -> None:
    """Administrative commands for managing projects."""


@project.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Project description.")
def project_create(name: str, description: str) -> None:
    """Create a new project deterministically."""
    runtime = asyncio.run(_get_runtime())
    proj = asyncio.run(runtime.admin_service.create_project(name, description))
    console.print(
        f"[bold green][OK] Project created:[/bold green] {proj.name} [dim](ID: {proj.id})[/dim]"
    )


@project.command("list")
@click.option(
    "--status", "-s", default=None, help="Filter by status (active, archived, paused, completed)."
)
def project_list(status: str | None) -> None:
    """List all projects."""
    runtime = asyncio.run(_get_runtime())
    projects = asyncio.run(runtime.admin_service.list_projects(status=status))

    if not projects:
        console.print("[dim]No projects found.[/dim]")
        return

    table = Table(title="GAIA Projects", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold", no_wrap=True)
    table.add_column("Status")
    table.add_column("Description")

    for p in projects:
        table.add_row(p.id, p.name, p.status, p.description)

    console.print(table)


@main.group("context")
def context() -> None:
    """Administrative commands for managing current working context."""


@context.command("set-project")
@click.argument("project_id", required=False)
def context_set_project(project_id: str | None) -> None:
    """Set the active project ID (or pass empty to clear)."""
    runtime = asyncio.run(_get_runtime())
    try:
        state = asyncio.run(runtime.admin_service.set_current_project(project_id))
        console.print(
            f"[bold green][OK] Active project set to:[/bold green] {state.current_project_id}"
        )
    except Exception as e:
        console.print(f"[bold red][ERROR] Failed to set project:[/bold red] {e}")
        sys.exit(1)


@context.command("set-task")
@click.argument("task_id", required=False)
def context_set_task(task_id: str | None) -> None:
    """Set the active task ID (or pass empty to clear)."""
    runtime = asyncio.run(_get_runtime())
    try:
        state = asyncio.run(runtime.admin_service.set_current_task(task_id))
        console.print(f"[bold green][OK] Active task set to:[/bold green] {state.current_task_id}")
    except Exception as e:
        console.print(f"[bold red][ERROR] Failed to set task:[/bold red] {e}")
        sys.exit(1)


@context.command("show")
def context_show() -> None:
    """Show the current user context."""
    runtime = asyncio.run(_get_runtime())
    state = asyncio.run(runtime.admin_service.get_state())

    table = Table(title="Current GAIA State", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Current Project ID", str(state.current_project_id or "None"))
    table.add_row("Current Task ID", str(state.current_task_id or "None"))
    table.add_row("Active Application", str(state.active_app or "None"))
    table.add_row("Active Agent", str(state.active_agent or "None"))
    table.add_row("Last Action Timestamp", str(state.last_action_timestamp or "None"))

    console.print(table)


@main.command("repl")
def repl_command() -> None:
    """Start the interactive REPL shell."""
    runtime = asyncio.run(_get_runtime())
    from gaia.cli.repl import run_repl

    asyncio.run(run_repl(runtime))


if __name__ == "__main__":
    main()
