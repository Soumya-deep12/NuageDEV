import configparser
from pathlib import Path

CONFIG_FILE = "nuagedev.conf"

def save_config(path: Path, project_name: str, editor: str, redmine_url: str = None, redmine_api_key: str = None):
    config = configparser.ConfigParser()
    config["project"] = {"name": project_name, "path": str(path.resolve())}
    config["environment"] = {"editor": editor}

    if redmine_url:
        config["redmine"] = {"url": redmine_url}
        if redmine_api_key:
            config["redmine"]["api_key"] = redmine_api_key

    with open(path / CONFIG_FILE, "w") as f:
        config.write(f)

def load_config(path: Path) -> configparser.ConfigParser | None:
    config_path = path / CONFIG_FILE
    if not config_path.exists():
        return None
    config = configparser.ConfigParser()
    config.read(config_path)
    return config if "project" in config else None