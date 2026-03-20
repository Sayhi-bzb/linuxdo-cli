from textual.app import App, ComposeResult
from textual.binding import Binding

from ..config import load_config
from ..client import LinuxDoClient
from .screens.browse import BrowseScreen
from .screens.help import HelpScreen


class LinuxDoApp(App):
    """LINUX DO TUI 应用"""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "退出", show=True, priority=True),
        Binding("question_mark", "push_help", "帮助", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        config = load_config()
        self.client = LinuxDoClient(config)

    def on_mount(self) -> None:
        self.push_screen(BrowseScreen())

    def action_push_help(self) -> None:
        self.push_screen(HelpScreen())
