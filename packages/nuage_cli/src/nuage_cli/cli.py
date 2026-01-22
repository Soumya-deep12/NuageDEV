import typer

app = typer.Typer()

@app.command()
def hello():
    """Simple test command"""
    print("Nuage CLI is working")

if __name__ == "__main__":
    app()
