import configparser
from pathlib import Path


CONFIG_FILE = "nuagedev.conf"


def save_config(path: Path, project_name: str, editor: str):
    config = configparser.ConfigParser()

    config["project"] = {
        "name": project_name,
        "path": str(path.resolve()),
    }

    config["environment"] = {
        "editor": editor,
    }

    with open(path / CONFIG_FILE, "w") as f:
        config.write(f)


def load_config(path: Path):
    config_path = path / CONFIG_FILE
    if not config_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(config_path)
    return config
