import asyncio
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from . import config as cfg
from .client import LinuxDoClient
from .utils.converter import html_to_md

app = typer.Typer(help="LINUX DO 社区命令行工具")
console = Console()

@app.command("login")
def login():
    """使用 Linux Do Connect 登录"""
    from .auth import login as do_login
    c = cfg.load_config()
    do_login(c)

@app.command("me")
def show_me():
    """查看我的用户信息"""
    import httpx
    c = cfg.load_config()

    if not c.access_token:
        print("[red]未登录，请先执行 [bold]linuxdo login[/bold][/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            res = client.get(
                f"{c.connect_url}/api/user",
                headers={"Authorization": f"Bearer {c.access_token}"}
            )
            res.raise_for_status()
            user = res.json()

        table = Table(title="我的用户信息", show_header=False, box=None)
        table.add_column("字段", style="cyan", no_wrap=True)
        table.add_column("值", style="white")

        trust_colors = {0: "red", 1: "yellow", 2: "green", 3: "blue", 4: "magenta"}
        tl = user.get("trust_level", 0)
        tl_str = f"[{trust_colors.get(tl, 'white')}]TL{tl}[/{trust_colors.get(tl, 'white')}]"

        table.add_row("用户 ID", str(user.get("id", "")))
        table.add_row("用户名", f"[bold yellow]{user.get('username', '')}[/bold yellow]")
        table.add_row("昵称", user.get("name") or "-")
        table.add_row("信任等级", tl_str)
        table.add_row("账号活跃", "[green]是[/green]" if user.get("active") else "[red]否[/red]")
        table.add_row("禁言状态", "[red]是[/red]" if user.get("silenced") else "[green]否[/green]")

        console.print(table)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("[red]登录已过期，请重新执行 [bold]linuxdo login[/bold][/red]")
        else:
            print(f"[red]请求失败: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[red]出错: {e}[/red]")
        raise typer.Exit(1)

@app.command("topics")
def list_topics(page: int = 0):
    """查看最新话题"""
    c = cfg.load_config()
    client = LinuxDoClient(c)

    async def _fetch():
        with console.status("[bold green]正在拉取最新话题...[/bold green]"):
            topics = await client.get_latest_topics(page=page)

        table = Table(title="LINUX DO 最新话题")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("标题", style="white")
        table.add_column("作者", style="yellow")
        table.add_column("回复", justify="right", style="green")
        table.add_column("最后回复", style="magenta")

        for t in topics:
            table.add_row(
                str(t.id),
                t.title,
                t.last_poster_username,
                str(t.posts_count),
                t.last_posted_at.strftime("%m-%d %H:%M")
            )
        console.print(table)

    asyncio.run(_fetch())

@app.command("view")
def view_topic(topic_id: int):
    """查看话题详情"""
    c = cfg.load_config()
    client = LinuxDoClient(c)

    async def _fetch():
        with console.status(f"[bold green]正在拉取话题 {topic_id} 详情...[/bold green]"):
            detail = await client.get_topic_detail(topic_id)

        console.print(f"\n[bold cyan]话题: {detail.title}[/bold cyan]")
        console.print(f"[dim]ID: {detail.id} | 回复: {detail.posts_count} | 浏览: {detail.views}[/dim]\n")
        console.print("-" * console.width)

        for post in detail.post_stream.get("posts", []):
            author = post.get("display_username") or post.get("username")
            created_at = post.get("created_at")
            md_content = html_to_md(post.get("cooked", ""))
            console.print(f"[bold yellow]@{author}[/bold yellow] [dim]{created_at}[/dim]")
            console.print(Markdown(md_content))
            console.print("-" * (console.width // 2))

    asyncio.run(_fetch())

@app.command("browse")
def browse():
    """启动交互式 TUI 浏览器"""
    from .tui import run_tui
    run_tui()


if __name__ == "__main__":
    app()
