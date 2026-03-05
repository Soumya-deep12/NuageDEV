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

@app.command()
def review_prior():
    """Lists uncommitted changes prior to commit."""

    cmd = ["git", "status", "--short"]
    try:
        # Avoid shell=True for security. capture_output=True is safe here.
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
    except subprocess.CalledProcessError as e:
        typer.secho(f"Failed to run git command: {e}", fg="red")
        return
    except FileNotFoundError:
        typer.secho("Git executable not found. Please install git.", fg="red")
        return
    
    if not result.stdout.strip():
        typer.secho("No uncommitted changes as of now")
        return

    typer.secho("Pending Changes to Review (Pre-commit):", fg="yellow", bold=True)
    changes = result.stdout.strip().split('\n')
    for i, change in enumerate(changes, 1):
        # Additional safety/formatting check to prevent completely malformed output
        if change:
            typer.echo(f" {i}. {change}")

@app.command()
def land(target: str = typer.Argument("master")):
    """Squash local commits and safely push to the target branch."""
    
    # Step 1: Strict Check for uncommitted changes
    status_cmd = ["git", "status", "--porcelain"]
    status_result = subprocess.run(status_cmd, capture_output=True, text=True)
    if status_result.stdout.strip():
        typer.secho("Working directory is not clean. Commit or stash changes before landing.", fg="red")
        raise typer.Exit(1)

    # Get current branch
    branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    branch_result = subprocess.run(branch_cmd, capture_output=True, text=True, check=True)
    current_branch = branch_result.stdout.strip()
    
    if current_branch == target:
        typer.secho(f"You cannot land the {target} branch onto itself.", fg="red")
        raise typer.Exit(1)

    # Fetch latest target
    typer.echo(f"Fetching latest origin/{target}...")
    subprocess.run(["git", "fetch", "origin", target], check=True)

    # Step 2: Create a backup branch
    backup_branch = f"{current_branch}-backup"
    typer.echo(f"Creating safety backup branch: {backup_branch}")
    subprocess.run(["git", "branch", "-f", backup_branch], check=True)

    try:
        # Step 3 & 4: Get commit messages for context
        log_cmd = ["git", "log", f"origin/{target}..HEAD", "--format=* %s%n%b"]
        log_result = subprocess.run(log_cmd, capture_output=True, text=True, check=True)
        commit_messages = log_result.stdout.strip()

        # Step 3: Soft Reset
        typer.echo(f"Soft resetting to origin/{target} (squashing commits)...")
        subprocess.run(["git", "reset", "--soft", f"origin/{target}"], check=True)

        # Step 4: Commit
        # We write the commit messages to a temporary file to use as a template
        temp_msg_file = f".nuage_commit_template"
        with open(temp_msg_file, "w") as f:
            f.write("\n\n# --- Nuage Auto-Squash ---\n")
            f.write("# Provide a summary for this landed feature.\n")
            f.write("# The individual commit messages are below for reference:\n#\n")
            for line in commit_messages.split('\n'):
                f.write(f"# {line}\n")
        
        typer.secho("Opening editor for the final commit message...", fg="blue")
        commit_cmd = ["git", "commit", "-t", temp_msg_file]
        commit_run = subprocess.run(commit_cmd)
        
        if os.path.exists(temp_msg_file):
            os.remove(temp_msg_file)
            
        if commit_run.returncode != 0:
            typer.secho("Commit aborted. Restoring from backup...", fg="red")
            subprocess.run(["git", "reset", "--hard", backup_branch], check=True)
            raise typer.Exit(1)

        # Step 5: Push
        typer.echo(f"Pushing to origin/{target}...")
        push_cmd = ["git", "push", "origin", f"HEAD:{target}"]
        subprocess.run(push_cmd, check=True)
        
        typer.secho(f"Successfully landed {current_branch} onto {target}!", fg="green", bold=True)

        # Checkout target and pull
        subprocess.run(["git", "checkout", target], check=True)
        subprocess.run(["git", "pull", "--rebase", "origin", target], check=True)

        # Step 6: Post-Land Cleanup
        typer.echo(f"Cleaning up local branch {current_branch}...")
        subprocess.run(["git", "branch", "-D", current_branch], check=True)
        
        # We can also clean up the backup branch since we succeeded
        typer.echo(f"Cleaning up backup branch {backup_branch}...")
        subprocess.run(["git", "branch", "-D", backup_branch], check=True)

    except subprocess.CalledProcessError as e:
        typer.secho(f"\nError during land process: {e}", fg="red")
        typer.secho(f"Your original state is safely preserved in branch: {backup_branch}", fg="yellow")
        typer.secho(f"To restore: git reset --hard {backup_branch}", fg="yellow")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()