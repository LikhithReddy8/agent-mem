import typer
from cli.commands import workspaces, memories, review, status, sessions, reindex
from cli.commands.search import search

app = typer.Typer(name="mem", help="Agent memory CLI — manage Claude Code session and code knowledge.")

app.add_typer(workspaces.app, name="workspace")
app.add_typer(memories.app, name="memory")

app.command("search")(search)
app.command("review")(review.review)
app.command("status")(status.status)
app.command("sessions")(sessions.sessions)
app.command("reindex")(reindex.reindex)

if __name__ == "__main__":
    app()
