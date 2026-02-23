import typer
import os
import subprocess
from pathlib import Path
from nuage import config, launcher, env, redmine

app = typer.Typer(help="Nuage: Your project context switcher.")

@app.command()
def setup(path: str = "."):
    """Initialize a project in the current directory."""
    p_path = Path(path).resolve()
    name = typer.prompt("Project name", default=p_path.name)
    editor = typer.prompt("Editor command (code, nvim, emacs)", default="code")
    
    typer.echo("\n--- Redmine (Optional - Press Enter to skip) ---")
    url = typer.prompt("Redmine URL", default="", show_default=False)
    key = typer.prompt("API Key", default="", hide_input=True, show_default=False) if url else None

    config.save_config(p_path, name, editor, url or None, key or None)
    typer.echo(f"Nuage setup complete for {name}!")

@app.command()
def go():
    """Launch editor and tmux session."""
    conf = config.load_config(Path.cwd())
    if not conf:
        typer.secho("No nuagedev.conf found. Run 'nuage setup' first.", fg=typer.colors.RED)
        raise typer.Exit(1)

    p_path = Path(conf["project"]["path"])
    launcher.start_editor(conf["environment"]["editor"], p_path)
    launcher.start_tmux(conf["project"]["name"], p_path)

@app.command()
def items():
    """List project tasks from Redmine."""
    cwd = Path.cwd()
    conf = config.load_config(cwd)
    env.ensure_env(cwd)

    if not conf or "redmine" not in conf:
        typer.echo("Redmine not configured for this project.")
        return

    url = conf["redmine"]["url"]
    api_key = conf["redmine"].get("api_key") or env.get_redmine_api_key()

    if not api_key:
        typer.secho("Redmine URL found but no API Key found in config or .env", fg=typer.colors.RED)
        return

    overdue = redmine.get_overdue_issues(url, api_key)
    today = redmine.get_today_issues(url, api_key)

    typer.secho(f"\n TASKS: {conf['project']['name']}", bold=True, underline=True)
    for issue in overdue:
        typer.echo(f"  [RED] #{issue['id']} {issue['subject']} (OVERDUE)")
    for issue in today:
        typer.echo(f"  [GRN] #{issue['id']} {issue['subject']} (TODAY)")

@app.command()
def review(target: str = typer.Argument(None), base: str = "main"):
    """The differences with my code."""
    
    result = subprocess.run(["git", "diff", "--name-only", base], capture_output=True, text=True)
    all_files = [f for f in result.stdout.strip().split('\n') if f]

    if not all_files:
        typer.secho("No changes")
        return

    files_to_review = all_files
    if target:
        files_to_review = [f for f in all_files if target in f]
        if not files_to_review:
            typer.echo(f"'{target}' no such file")
            return

    created_temp_files = []

    for file_path in files_to_review:
        file_obj = Path(file_path)
        temp_file = f".{file_obj.name}.HEAD" 
        created_temp_files.append(temp_file)

        with open(temp_file, "w") as f:
            subprocess.run(["git", "show", f"{base}:{file_path}"], stdout=f)

        subprocess.run(["code", "--diff", temp_file, file_path])

    for temp_file in created_temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@app.command()
def review_list(base: str = "main"):
    """Lists of files that are meant to be reviewed."""

    cmd = ["git", "log", f"{base}..HEAD", "--oneline"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if not result.stdout.strip():
        typer.secho("No patch as of nowwww")
        return

    typer.secho(f"Pending Patches (Commits) to Review:", fg="blue", bold=True)
    commits = result.stdout.strip().split('\n')
    for i, commit in enumerate(commits, 1):
        typer.echo(f" {i}. {commit}")

if __name__ == "__main__":
    app()