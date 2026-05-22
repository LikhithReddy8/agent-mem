import typer
from rich.table import Table
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command()
def status(
    workspace: str = typer.Option(..., "--workspace", "-w"),
    stale_only: bool = typer.Option(False, "--stale"),
):
    data = MemClient().get_status(workspace)
    console.print(f"[bold]Workspace:[/bold] {workspace[:8]}")
    console.print(f"Total: {data['total']} | Fresh: {data['fresh']} | "
                  f"Potentially stale: {data['potentially_stale']} | "
                  f"Confirmed stale: {data['confirmed_stale']}")
    memories = data.get("memories", [])
    if stale_only:
        memories = [m for m in memories if m["staleness_status"] != "fresh"]
    table = Table("ID", "Type", "Title", "Staleness", "Last Indexed")
    for m in memories:
        table.add_row(
            m["id"][:8], m["type"], m["title"][:40],
            m["staleness_status"],
            (m.get("last_indexed_at") or "")[:10],
        )
    console.print(table)
