"""CLI-facing auth entrypoint; the OAuth flow lives in AuthService."""

import webbrowser
from typing import Optional
from .config import Config, ConfigRepository
from .connect_client import ConnectClient
from .services import AuthService, AuthServiceError
from rich import print


def login(config: Config, repository: ConfigRepository | None = None) -> Optional[Config]:
    """Run the CLI login flow and persist tokens on success."""
    config_repository = repository or ConfigRepository()
    connect_client = ConnectClient()
    auth_service = AuthService(
        connect_client,
        config_repository,
        browser_opener=webbrowser.open,
    )

    try:
        session = auth_service.prepare_login(config)
        print(f"\n[bold cyan]正在启动 OAuth2 授权流程...[/bold cyan]")
        print(
            "请在浏览器中完成授权。如果浏览器未自动打开，请手动访问：\n"
            f"[link={session.auth_url}]{session.auth_url}[/link]\n"
        )
        result = auth_service.login(config, session=session)
        print(f"\n[bold green]登录成功！[/bold green]")
        print(f"欢迎回来, [bold yellow]{result.user.username}[/bold yellow]!")
        return result.config
    except AuthServiceError as e:
        print(f"\n[red]登录过程中发生错误:[/red] {e}")
        return None
