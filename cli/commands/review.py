import typer
from rich.console import Console
from rich.panel import Panel
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command()
def review(workspace: str = typer.Option(None, "--workspace", "-w")):
    client = MemClient()
    workspaces = [{"id": workspace}] if workspace else client.list_workspaces()

    for ws in workspaces:
        status = client.get_status(ws["id"])
        stale = [m for m in status.get("memories", []) if m["staleness_status"] != "fresh"]
        if not stale:
            console.print(f"[green]No stale memories for workspace {ws['id'][:8]}[/green]")
            continue

        for m in stale:
            console.print(Panel(
                f"[bold]{m['title']}[/bold]\n{m['content']}\n\n[dim]Staleness: {m['staleness_status']}[/dim]",
                title=f"[yellow]{m['id'][:8]}[/yellow]",
            ))
            action = typer.prompt("Action: [r]e-index, [v]alid, [i]gnore", default="i")
            if action == "v":
                client.validate_memory(m["id"])
                console.print("[green]Marked as valid.[/green]")
            elif action == "i":
                console.print("[dim]Skipped.[/dim]")
            else:
                console.print("[dim]Re-index not yet implemented in CLI — use `mem reindex <file>`[/dim]")
