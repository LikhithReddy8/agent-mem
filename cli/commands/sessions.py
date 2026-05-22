import typer
from rich.table import Table
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command()
def sessions(workspace: str = typer.Option(None, "--workspace", "-w")):
    items = MemClient().list_sessions(workspace)
    if not items:
        console.print("No sessions found. (Tip: sessions are stored per workspace via the hooks.)")
        return
    table = Table("ID", "Status", "Started", "Ended", "Summary")
    for s in items:
        table.add_row(
            s["id"][:8], s["status"],
            s["started_at"][:16], (s.get("ended_at") or "")[:16],
            (s.get("summary") or "")[:60],
        )
    console.print(table)
