import os
import typer
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command()
def reindex(
    file_path: str = typer.Argument(..., help="Path to file to re-index"),
    workspace: str = typer.Option(..., "--workspace", "-w", help="Workspace ID"),
):
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        console.print(f"[red]File not found:[/red] {file_path}")
        raise typer.Exit(1)

    language = "go" if file_path.endswith(".go") else "python" if file_path.endswith(".py") else None
    with MemClient()._c() as c:
        result = c.post("/reindex", json={
            "workspace_id": workspace,
            "file_path": os.path.abspath(file_path),
            "content": content,
            "language": language,
        }).json()
    console.print(f"[green]Re-indexed:[/green] {result.get('file_path')} (hash: {result.get('hash', '')[:8]})")
