from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static


HELP_TEXT = """
[bold #0088cc]LINUX DO CLI  快捷键帮助[/bold #0088cc]

[bold #ffba00]全局[/bold #ffba00]
  [#3498db]?[/#3498db]              打开/关闭此帮助

[bold #ffba00]话题列表[/bold #ffba00]
  [#3498db]Tab / Shift+Tab[/#3498db]  切换分类（最新/热门/分类）
  [#3498db]j / ↓[/#3498db]           光标下移
  [#3498db]k / ↑[/#3498db]           光标上移
  [#3498db]g / Home[/#3498db]        跳到顶部
  [#3498db]G / End[/#3498db]         跳到底部
  [#3498db]Enter[/#3498db]           进入话题详情
  [#3498db]o[/#3498db]               浏览器打开话题
  [#3498db]n[/#3498db]               立即加载下一页
  [#3498db]r[/#3498db]               刷新
  [#3498db]Ctrl+Q[/#3498db]          退出程序

[bold #ffba00]鼠标操作[/bold #ffba00]
  点击分类 Tab         切换分类（最新/热门/分类）
  点击话题行           进入话题详情
  点击 ← 返回          从详情返回列表
  接近列表底部         自动追加下一页（无限滚动）

[bold #ffba00]话题详情[/bold #ffba00]
  [#3498db]Esc[/#3498db]              返回列表（或点击 ← 返回）
  [#3498db]j / ↓[/#3498db]           向下滚动
  [#3498db]k / ↑[/#3498db]           向上滚动
  [#3498db]PageUp / PageDown[/#3498db]  翻页滚动
  [#3498db]g / Home[/#3498db]        滚动到顶部
  [#3498db]G / End[/#3498db]         滚动到底部
  接近底部或滚动到底部    自动追加更多回复

[dim]按 Esc 或 ? 关闭[/dim]
"""


class HelpScreen(ModalScreen):
    """快捷键帮助（模态框）"""

    BINDINGS = [
        Binding("escape,question_mark", "dismiss", "关闭", show=True),
    ]

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="help-container"):
            yield Static(HELP_TEXT, id="help-content", markup=True)
