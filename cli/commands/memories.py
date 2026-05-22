import typer
from rich.table import Table
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command("add")
def add_memory(
    workspace: str = typer.Option(..., "--workspace", "-w", help="Workspace ID"),
    title: str = typer.Option(..., "--title", "-t"),
    content: str = typer.Argument(...),
    type: str = typer.Option("decision", "--type"),
    importance: float = typer.Option(0.9, "--importance"),
):
    result = MemClient().add_memory(workspace, title, content, type, importance)
    if "id" in result:
        console.print(f"[green]Saved memory:[/green] {result['title']} ({result['id'][:8]})")
    else:
        console.print(f"[red]Error:[/red] {result}")


@app.command("list")
def list_memories(workspace: str = typer.Option(None, "--workspace", "-w")):
    memories = MemClient().list_memories(workspace)
    if not memories:
        console.print("No memories found.")
        return
    table = Table("ID", "Type", "Title", "Importance", "Staleness")
    for m in memories:
        table.add_row(m["id"][:8], m["type"], m["title"][:50], str(m["importance_score"]), m["staleness_status"])
    console.print(table)


@app.command("delete")
def delete_memory(memory_id: str = typer.Argument(...)):
    ok = MemClient().delete_memory(memory_id)
    if ok:
        console.print(f"[green]Deleted[/green] {memory_id[:8]}")
    else:
        console.print(f"[red]Not found:[/red] {memory_id}")
