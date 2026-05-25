import os
import typer
from pathlib import Path
from rich.table import Table
from rich.console import Console
from cli.client import MemClient

app = typer.Typer()
console = Console()


def _detect_language(path: Path) -> str | None:
    files = {f.name for f in path.iterdir() if f.is_file()}
    dirs  = {d.name for d in path.iterdir() if d.is_dir()}
    if "go.mod" in files or any(f.endswith(".go") for f in files):
        return "go"
    if "requirements.txt" in files or "pyproject.toml" in files or "setup.py" in files:
        return "python"
    if "package.json" in files:
        return "javascript"
    if "Cargo.toml" in files:
        return "rust"
    # check one level deeper for go files (monorepo layout)
    for d in dirs:
        sub = path / d
        if any(f.suffix == ".go" for f in sub.iterdir() if f.is_file()):
            return "go"
    return None


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


@app.command("init")
def init_workspaces(
    root: str = typer.Argument(None, help="Parent folder containing repo subdirectories (default: current directory)"),
    git_only: bool = typer.Option(True, "--git-only/--all", help="Only register dirs with a .git folder"),
):
    """Scan a folder and register every subdirectory as a workspace."""
    root_path = Path(root).expanduser().resolve() if root else Path.cwd()
    if not root_path.is_dir():
        console.print(f"[red]Not a directory:[/red] {root_path}")
        raise typer.Exit(1)

    client = MemClient()
    existing = {w["path"] for w in client.list_workspaces()}

    candidates = sorted(
        d for d in root_path.iterdir()
        if d.is_dir()
        and not d.name.startswith(".")
        and (not git_only or (d / ".git").exists())
    )

    if not candidates:
        hint = "" if not git_only else " (no .git found — try --all to include non-git dirs)"
        console.print(f"[yellow]No subdirectories found{hint}[/yellow]")
        return

    registered = skipped = failed = 0
    table = Table("Name", "Language", "Status")

    for d in candidates:
        if str(d) in existing:
            table.add_row(d.name, "", "[dim]already registered[/dim]")
            skipped += 1
            continue

        lang = _detect_language(d)
        result = client.add_workspace(d.name, str(d), lang)

        if "id" in result:
            table.add_row(d.name, lang or "—", f"[green]registered[/green] {result['id'][:8]}")
            registered += 1
        else:
            detail = result.get("detail", str(result))
            table.add_row(d.name, lang or "—", f"[red]failed:[/red] {detail}")
            failed += 1

    console.print(table)
    console.print(f"\n{registered} registered  {skipped} skipped  {failed} failed")


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


@app.command("delete")
def delete_workspace(
    workspace_id: str = typer.Argument(..., help="Workspace ID (or first 8 chars)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a workspace and all its memories."""
    client = MemClient()

    # resolve short ID to full ID
    workspaces = client.list_workspaces()
    match = next((w for w in workspaces if w["id"].startswith(workspace_id)), None)
    if not match:
        console.print(f"[red]Not found:[/red] {workspace_id}")
        raise typer.Exit(1)

    if not yes:
        console.print(f"[bold]{match['name']}[/bold]  {match['path']}")
        typer.confirm("Delete this workspace and all its memories?", abort=True)

    ok = client.delete_workspace(match["id"])
    if ok:
        console.print(f"[green]Deleted[/green] {match['name']} ({match['id'][:8]})")
    else:
        console.print(f"[red]Failed to delete[/red] {match['id'][:8]}")
