import typer
from rich.console import Console
from rich.panel import Panel
from cli.client import MemClient

app = typer.Typer()
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace ID"),
    limit: int = typer.Option(10, "--limit", "-n"),
):
    results = MemClient().search(query, workspace, limit).get("results", [])
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    for r in results:
        m = r["memory"]
        score = r["score"]
        console.print(Panel(
            f"[bold]{m['title']}[/bold]\n{m['content']}\n\n"
            f"[dim]Type: {m['type']} | Score: {score:.3f} | Staleness: {m['staleness_status']}[/dim]",
            title=f"[cyan]{m['id'][:8]}[/cyan]",
        ))
