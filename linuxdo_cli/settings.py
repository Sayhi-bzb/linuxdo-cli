from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    client_id: str = Field(default="")
    client_secret: str = Field(default="")
    access_token: Optional[str] = Field(None)
    refresh_token: Optional[str] = Field(None)
    base_url: str = "https://linux.do"
    connect_url: str = "https://connect.linux.do"
    theme: Optional[str] = Field(None)
    layout_density: str = Field(default="standard")

    model_config = SettingsConfigDict(
        env_prefix="LINUXDO_",
        extra="ignore",
    )


def apply_builtin_credentials(config: Config) -> Config:
    """若 client_id 为空，尝试从内置 _credentials.py 读取。"""
    if config.client_id:
        return config
    try:
        from ._credentials import CLIENT_ID, CLIENT_SECRET

        return config.model_copy(
            update={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
        )
    except ImportError:
        return config
