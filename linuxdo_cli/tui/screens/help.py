from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label, Static


HELP_TEXT = """
[bold cyan]LINUX DO CLI  快捷键帮助[/bold cyan]

[bold]全局[/bold]
  [yellow]q[/yellow]          退出程序
  [yellow]?[/yellow]          打开/关闭此帮助

[bold]话题列表[/bold]
  [yellow]Tab[/yellow]        切换分类（最新/热门）
  [yellow]Shift+Tab[/yellow]  切换分类（反向）
  [yellow]j / ↓[/yellow]     光标下移
  [yellow]k / ↑[/yellow]     光标上移
  [yellow]g[/yellow]          跳到顶部
  [yellow]G[/yellow]          跳到底部
  [yellow]Enter[/yellow]      进入话题详情
  [yellow]o[/yellow]          浏览器打开话题
  [yellow]n[/yellow]          下一页
  [yellow]p[/yellow]          上一页
  [yellow]r[/yellow]          刷新

[bold]话题详情[/bold]
  [yellow]Esc / q[/yellow]   返回列表
  [yellow]j / k[/yellow]     上下滚动
  [yellow]g / G[/yellow]     滚动到顶/底

[dim]按 Esc 或 ? 关闭[/dim]
"""


class HelpScreen(ModalScreen):
    """快捷键帮助（模态框）"""

    BINDINGS = [
        Binding("escape,question_mark", "dismiss", "关闭", show=True),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Static {
        background: $surface;
        border: heavy $primary;
        padding: 1 3;
        width: 60;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT, markup=True)
