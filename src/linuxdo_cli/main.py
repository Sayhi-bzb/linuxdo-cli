import typer
from rich import print
from rich.console import Console
from rich.table import Table
from .auth import login as do_login
from .config import ConfigRepository
from .connect_client import (
    ConnectAuthenticationError,
    ConnectClient,
    ConnectClientError,
)

app = typer.Typer(
    help="LINUX DO 社区命令行工具",
    invoke_without_command=True,
)
console = Console()


def version_callback(value: bool):
    if value:
        from . import __version__
        print(f"linuxdo-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-V",
        callback=version_callback,
        is_eager=True,
        help="显示版本号",
    ),
):
    """直接运行 linuxdo 启动 TUI 浏览器"""
    if ctx.invoked_subcommand is None:
        from .tui import run_tui
        run_tui()


@app.command("login")
def login():
    """使用 Linux Do Connect 登录"""
    repo = ConfigRepository()
    c = repo.load()
    do_login(c, repository=repo)


@app.command("me")
def show_me():
    """查看我的用户信息"""
    repo = ConfigRepository()
    c = repo.load()

    if not c.access_token:
        print("[red]未登录，请先执行 [bold]linuxdo login[/bold][/red]")
        raise typer.Exit(1)

    try:
        user = ConnectClient().get_current_user(c)

        table = Table(title="我的用户信息", show_header=False, box=None)
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="white")

        trust_colors = {0: "red", 1: "yellow", 2: "green", 3: "blue", 4: "magenta"}
        tl = user.trust_level
        tl_str = f"[{trust_colors.get(tl, 'white')}]TL{tl}[/{trust_colors.get(tl, 'white')}]"

        table.add_row("用户 ID", str(user.id))
        table.add_row("用户名", f"[bold yellow]{user.username}[/bold yellow]")
        table.add_row("昵称", user.name or "-")
        table.add_row("信任等级", tl_str)
        table.add_row("账号活跃", "[green]是[/green]" if user.active else "[red]否[/red]")
        table.add_row("禁言状态", "[red]是[/red]" if user.silenced else "[green]否[/green]")

        console.print(table)
    except ConnectAuthenticationError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except ConnectClientError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[red]出错: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
