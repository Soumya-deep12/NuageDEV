from pathlib import Path
import typer

from nuage.config import save_config, load_config
from nuage.launcher import start_tmux, start_editor


app = typer.Typer()


@app.command()
def setup(path: str = ".") -> None:
    """
    Initialize a nuagedev project in the given directory.
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        print("Path does not exist")
        raise typer.Exit(1)

    project_name = typer.prompt(
        "Project name",
        default=project_path.name,
    )

    editor = typer.prompt(
        "Editor command (e.g. code, vim, nvim)"
    )

    save_config(project_path, project_name, editor)

    print("Project initialized")
    print(f"Config written to {project_path / 'nuagedev.conf'}")


@app.command()
def go(project_name: str) -> None:
    """
    Start the tmux session and editor for the project.
    """
    cwd = Path.cwd()
    config = load_config(cwd)

    if not config:
        print("nuagedev.conf not found or invalid. Run `nuagedev setup .` first.")
        raise typer.Exit(1)

    saved_name = config["project"]["name"]
    path = Path(config["project"]["path"])
    editor = config["environment"]["editor"]

    if project_name != saved_name:
        print(
            f"Project name does not match config "
            f"(expected '{saved_name}')"
        )
        raise typer.Exit(1)

    print("Starting tmux session...")
    start_tmux(saved_name, path)

    print("Opening editor...")
    start_editor(editor, path)


if __name__ == "__main__":
    app()
