"""Main CLI."""

import typer
from rich.console import Console

app = typer.Typer(help="Nuage CLI - Your Cloud Development Tool")
console = Console()


@app.command()
def hello(name: str = "World"):
    """Say hello to someone."""
    console.print(f"[bold green]Hello, {name}![/bold green]")
    console.print("[cyan]Welcome to Nuage![/cyan]")


@app.command()
def info():
    """Show information about Nuage."""
    console.print("[bold blue]Nuage CLI v0.1.0[/bold blue]")
    console.print("A professional cloud development tool")


if __name__ == "__main__":
    app()