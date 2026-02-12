import subprocess
from pathlib import Path

def start_tmux(session_name: str, path: Path):
    # -A attaches if session exists, -s creates it
    subprocess.run(["tmux", "new-session", "-A", "-s", session_name, "-c", str(path)])

def start_editor(editor: str, path: Path):
    try:
        # Non-blocking: starts the editor and lets the script continue to tmux
        subprocess.Popen([editor, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"❌ Error: Editor '{editor}' not found in your $PATH.")