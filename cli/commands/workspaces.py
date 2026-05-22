import typer
from rich.table import Table
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command("add")
def add_workspace(
    name: str = typer.Argument(..., help="Workspace name, e.g. auth-service"),
    path: str = typer.Argument(..., help="Absolute path to the workspace"),
    language: str = typer.Option(None, "--language", "-l"),
):
    result = MemClient().add_workspace(name, path, language)
    if "id" in result:
        console.print(f"[green]Registered workspace:[/green] {result['name']} ({result['id']})")
    else:
        console.print(f"[red]Error:[/red] {result}")


@app.command("list")
def list_workspaces():
    workspaces = MemClient().list_workspaces()
    if not workspaces:
        console.print("No workspaces registered.")
        return
    table = Table("ID", "Name", "Path", "Language", "Created")
    for w in workspaces:
        table.add_row(w["id"][:8], w["name"], w["path"], w.get("language") or "", w["created_at"][:10])
    console.print(table)
