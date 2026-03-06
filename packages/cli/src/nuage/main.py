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

    config.save_config(p_path, name, editor, url or None)

    if url and key:
        env_path = p_path / ".env"
        with open(env_path, "a") as f:
            f.write(f"\nREDMINE_API_KEY={key}\n")
        typer.secho(f"  [✓] Saved API key securely to {env_path.name}", fg=typer.colors.GREEN)

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
def redmine_items():
    """List project tasks from Redmine."""
    cwd = Path.cwd()
    conf = config.load_config(cwd)

    if not conf or "redmine" not in conf:
        typer.echo("Redmine not configured for this project.")
        return

    # Load .env from the project root, not from wherever the user runs nuage
    project_root = Path(conf["project"]["path"])
    env.ensure_env(project_root)

    url = conf["redmine"]["url"]
    api_key = env.get_redmine_api_key()

    if not api_key:
        typer.secho("Redmine URL found but no API Key found in .env", fg=typer.colors.RED)
        return

    overdue = redmine.get_overdue_issues(url, api_key)
    today = redmine.get_today_issues(url, api_key)

    if overdue is None or today is None:
        typer.secho("\n  [!] Could not connect to Redmine server.", fg=typer.colors.RED, bold=True)
        return

    typer.secho(f"\n TASKS: {conf['project']['name']}", bold=True, underline=True)
    for issue in overdue:
        typer.echo(f"  [RED] #{issue['id']} {issue['subject']} (OVERDUE)")
    for issue in today:
        typer.echo(f"  [GRN] #{issue['id']} {issue['subject']} (TODAY)")

@app.command()
def redmine_list():
    """List all project tasks for all team members."""
    cwd = Path.cwd()
    conf = config.load_config(cwd)

    if not conf or "redmine" not in conf:
        typer.echo("Redmine not configured for this project.")
        return

    # Load .env from the project root, not from wherever the user runs nuage
    project_root = Path(conf["project"]["path"])
    env.ensure_env(project_root)

    url = conf["redmine"]["url"]
    api_key = env.get_redmine_api_key()

    if not api_key:
        typer.secho("Redmine URL found but no API Key found in .env", fg=typer.colors.RED)
        return

    all_issues = redmine.get_all_issues(url, api_key)

    # Always print the header table regardless of whether tasks exist
    typer.secho(f"\n ALL TEAM TASKS: {conf['project']['name']}", bold=True, underline=True)
    header = f"  {'ID':<8} | {'Assignee':<20} | {'Status':<15} | {'Subject'}"
    typer.echo("  " + "-" * (len(header) - 2))
    typer.echo(header)
    typer.echo("  " + "-" * (len(header) - 2))

    if all_issues is None:
        typer.secho("  [!] Connection failed. Data could not be retrieved.", fg=typer.colors.RED)
        return

    if not all_issues:
        typer.secho("  (no open tasks found)", fg=typer.colors.GREEN)
        return

    for issue in all_issues:
        assignee_data = issue.get("assigned_to")
        assignee_name = assignee_data.get("name") if assignee_data else "Unassigned"
        status = issue.get('status', {}).get('name', 'Unknown')
        issue_id = f"#{issue['id']}"

        color = "white"
        if "In Progress" in status: color = "green"
        if "Feedback" in status: color = "yellow"
        if "Closed" in status or "Rejected" in status: color = "red"

        row = f"  {issue_id:<8} | {assignee_name:<20} | {typer.style(f'{status:<15}', fg=color)} | {issue['subject']}"
        typer.echo(row)

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


@app.command()
def update(issue_id: int = typer.Argument(None)):
    """Update the status of a Redmine issue"""
    cwd = Path.cwd()
    env.ensure_env(cwd)
    conf = config.load_config(cwd)

    if not conf or "redmine" not in conf:
        typer.secho("Redmine not configured for this project.", fg=typer.colors.RED)
        raise typer.Exit(1)

    url = conf["redmine"]["url"]

    # Load .env from the project root, not from wherever the user runs nuage
    project_root = Path(conf["project"]["path"])
    env.ensure_env(project_root)
    api_key = env.get_redmine_api_key()

    if not api_key:
        typer.secho("No API Key found in .env", fg=typer.colors.RED)
        raise typer.Exit(1)

    # --- Discovery Mode: no ID given ---
    if issue_id is None:
        my_issues = redmine.get_my_open_issues(url, api_key)

        if my_issues is None:
            typer.echo("Could not connect to Redmine.")
            raise typer.Exit(1)

        if not my_issues:
            typer.echo("No open tasks assigned to you.")
            return

        typer.secho(f"\n YOUR OPEN TASKS:", bold=True, underline=True)
        for i, issue in enumerate(my_issues, 1):
            status = issue.get("status", {}).get("name", "?")
            typer.echo(f"  {i}. #{issue['id']} [{status}] {issue['subject']}")

        choice = typer.prompt("\nEnter issue number to update (or 0 to cancel)", default="0")
        try:
            idx = int(choice)
        except ValueError:
            typer.secho("Invalid input.", fg="red")
            raise typer.Exit(1)

        if idx == 0:
            return
        if idx < 1 or idx > len(my_issues):
            typer.secho("Out of range.", fg="red")
            raise typer.Exit(1)

        issue_id = my_issues[idx - 1]["id"]

    # --- Status Transition ---
    typer.echo(f"\n Fetching issue #{issue_id}...")
    issue = redmine.get_issue(url, api_key, issue_id)
    if issue is None:
        typer.secho(f"[!] Could not fetch issue #{issue_id}.", fg=typer.colors.RED)
        raise typer.Exit(1)

    current_status = issue.get("status", {}).get("name", "Unknown")
    typer.secho(f"\n Issue #{issue_id}: {issue['subject']}", bold=True)
    typer.echo(f"  Current Status: {current_status}")

    typer.secho("\n Fetching available statuses...", fg="blue")
    statuses = redmine.get_allowed_statuses(url, api_key, issue_id)
    if statuses is None:
        typer.secho("[!] Could not fetch available statuses.", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not statuses:
        typer.secho("\n [!] No status transitions available for you on this issue.", fg=typer.colors.YELLOW)
        typer.echo("     (You may lack permissions, or the Redmine workflow restricts it)")
        raise typer.Exit(1)

    typer.secho("\n Available Statuses:", bold=True)
    for i, s in enumerate(statuses, 1):
        typer.echo(f"  {i}. {s['name']}")

    choice = typer.prompt("\nSelect new status number (or 0 to cancel)", default="0")
    try:
        idx = int(choice)
    except ValueError:
        typer.secho("Invalid input.", fg="red")
        raise typer.Exit(1)

    if idx == 0:
        typer.echo("Cancelled.")
        return
    if idx < 1 or idx > len(statuses):
        typer.secho("Out of range.", fg="red")
        raise typer.Exit(1)

    chosen = statuses[idx - 1]
    typer.echo(f"\n Updating #{issue_id} to: {chosen['name']}...")
    success = redmine.update_issue_status(url, api_key, issue_id, chosen["id"])

    if success:
        typer.secho(f"  ✓ Issue #{issue_id} updated to '{chosen['name']}'.", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho(f"  [!] Failed to update issue #{issue_id}. Check your permissions.", fg=typer.colors.RED)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()