import configparser
from pathlib import Path

CONFIG_FILE = "nuagedev.conf"

def save_config(path: Path, project_name: str, editor: str, redmine_url: str = None):
    config = configparser.ConfigParser()
    config["project"] = {"name": project_name, "path": str(path.resolve())}
    config["environment"] = {"editor": editor}

    if redmine_url:
        config["redmine"] = {"url": redmine_url}

    with open(path / CONFIG_FILE, "w") as f:
        config.write(f)

def load_config(path: Path) -> configparser.ConfigParser | None:
    current_dir = path.resolve()
    
    # Traverse up the directory tree looking for the config file
    while current_dir != current_dir.parent:
        config_path = current_dir / CONFIG_FILE
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            return config if "project" in config else None
        current_dir = current_dir.parent
        
    return None