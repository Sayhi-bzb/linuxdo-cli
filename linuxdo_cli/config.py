import json
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

CONFIG_DIR = Path.home() / ".config" / "linuxdo-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Config(BaseSettings):
    client_id: str = "8yXy7fSJEAGEIGfuHUgRvr0upF6Do7ek"
    client_secret: str = "Unz0rqLG33yNNDTFAamETaneq4bU5L8c"
    access_token: Optional[str] = Field(None)
    refresh_token: Optional[str] = Field(None)
    base_url: str = "https://linux.do"
    connect_url: str = "https://connect.linux.do"

    class Config:
        env_prefix = "LINUXDO_"
        extra = "ignore"

def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return Config(**json.load(f))
    except Exception:
        return Config()

def save_config(config: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2, exclude_none=True))
