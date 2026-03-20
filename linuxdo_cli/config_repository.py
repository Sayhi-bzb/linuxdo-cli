import json
from pathlib import Path

from .settings import Config, apply_builtin_credentials


CONFIG_DIR = Path.home() / ".config" / "linuxdo-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigRepository:
    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        self.config_file = config_file

    def load(self) -> Config:
        if not self.config_file.exists():
            return apply_builtin_credentials(Config())

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = Config(**json.load(f))
        except Exception:
            config = Config()

        return apply_builtin_credentials(config)

    def save(self, config: Config) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2, exclude_none=True))
