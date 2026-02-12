import os
from pathlib import Path
from dotenv import load_dotenv as _load_dotenv

def ensure_env(project_root: Path):
    env_path = project_root / ".env"
    if env_path.exists():
        _load_dotenv(dotenv_path=env_path)

def get_redmine_api_key() -> str | None:
    return os.getenv("REDMINE_API_KEY")