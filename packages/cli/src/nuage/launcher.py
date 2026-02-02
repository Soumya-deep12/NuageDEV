import subprocess
from pathlib import Path


def start_tmux(session_name: str, path: Path):
    subprocess.run(
        ["tmux", "new-session", "-A", "-s", session_name, "-c", str(path)],
        check=False,
    )


def start_editor(editor: str, path: Path):
    subprocess.Popen([editor, str(path)])
