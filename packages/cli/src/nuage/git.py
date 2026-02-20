import subprocess

def get_git_diff():
    """Checks if we are in a git repo and returns status."""
    try:
        # Check if it's a git repo
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                       check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False