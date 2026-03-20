import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Resize

from ..config import ConfigRepository
from ..client import LinuxDoClient
from ..services import TopicDetailService, TopicService
from .screens.browse import BrowseScreen
from .screens.help import HelpScreen
from .screens.theme_select import ThemeSelectScreen
from .theme import THEMES
from .widgets.status_bar import StatusBar
from .widgets.topic_list import TopicList

logger = logging.getLogger(__name__)


class LinuxDoApp(App):
    """LINUX DO TUI 应用"""

    CSS_PATH = "app.tcss"
    MEDIUM_VIEWPORT_WIDTH = 100
    NARROW_VIEWPORT_WIDTH = 72

    BINDINGS = [
        Binding("ctrl+q", "quit", "退出", show=True, priority=True),
        Binding("question_mark", "push_help", "帮助", show=True),
        Binding("t", "open_theme_select", "切换主题", show=True),
        Binding("d", "toggle_density", "切换密度", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config_repository = ConfigRepository()
        self.config = self.config_repository.load()
        self.client = LinuxDoClient(self.config)
        self.topic_service = TopicService(self.client)
        self.topic_detail_service = TopicDetailService(self.client)
        self.category_map: dict = {}  # category_id → Category
        self.viewport_name = "wide"

    def on_mount(self) -> None:
        for theme in THEMES:
            self.register_theme(theme)
            
        self.theme = self.config.theme or "linuxdo"
        self.refresh_density_class()
        self.refresh_viewport_class()
        
        self.push_screen(BrowseScreen())
        self.run_worker(self._load_category_map, thread=True)
        self.run_worker(self._check_update, thread=True)

    def refresh_density_class(self) -> None:
        """根据配置为 App 添加或移除紧凑模式类名"""
        if self.config.layout_density == "compact":
            self.add_class("-compact")
        else:
            self.remove_class("-compact")

    def _resolve_viewport_name(self, width: int) -> str:
        if width < self.NARROW_VIEWPORT_WIDTH:
            return "narrow"
        if width < self.MEDIUM_VIEWPORT_WIDTH:
            return "medium"
        return "wide"

    def refresh_viewport_class(self, width: int | None = None) -> None:
        width = width if width is not None else self.size.width
        viewport_name = self._resolve_viewport_name(width)
        self.viewport_name = viewport_name

        self.set_class(viewport_name == "wide", "-viewport-wide")
        self.set_class(viewport_name == "medium", "-viewport-medium")
        self.set_class(viewport_name == "narrow", "-viewport-narrow")

        for screen in self.screen_stack:
            refresh = getattr(screen, "refresh_responsive_layout", None)
            if callable(refresh):
                refresh()

    def on_resize(self, event: Resize) -> None:
        self.refresh_viewport_class(event.size.width)

    def action_toggle_density(self) -> None:
        new_density = "compact" if self.config.layout_density == "standard" else "standard"
        self.config.layout_density = new_density
        self.config_repository.save(self.config)
        self.refresh_density_class()
        try:
            msg = "紧凑模式" if new_density == "compact" else "标准模式"
            self.screen.query_one(StatusBar).show_message(f"布局已切换为: {msg}")
        except Exception:
            pass

    def _load_category_map(self) -> None:
        import asyncio
        try:
            cats = asyncio.run(self.client.get_categories())
            self.category_map = {c.id: c for c in cats}
            self.call_from_thread(self._refresh_topic_list)
        except Exception as exc:
            logger.warning("Failed to load category map: %s", exc)
            self.call_from_thread(self._notify_category_map_error, str(exc))

    def _refresh_topic_list(self) -> None:
        try:
            tl = self.screen.query_one(TopicList)
            tl.topics = list(tl.topics)
        except Exception:
            pass

    def _notify_category_map_error(self, error: str) -> None:
        try:
            self.screen.query_one(StatusBar).show_message(
                f"[yellow]分类加载失败: {error}[/yellow]",
                duration=5.0,
            )
        except Exception:
            logger.warning("Category map error could not be shown in status bar: %s", error)

    def _check_update(self) -> None:
        try:
            import urllib.request, json
            from .. import __version__
            url = "https://pypi.org/pypi/linuxdo-cli/json"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
            latest = data["info"]["version"]
            if latest != __version__:
                self.call_from_thread(self._notify_update, latest)
        except Exception:
            pass

    def _notify_update(self, latest: str) -> None:
        from .. import __version__
        try:
            self.screen.query_one(StatusBar).show_message(
                f"[yellow]新版本可用: {latest}（当前 {__version__}）  pip install -U linuxdo-cli[/yellow]",
                duration=10.0,
            )
        except Exception:
            pass

    def action_push_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_open_theme_select(self) -> None:
        def on_theme_selected(theme_name: str | None) -> None:
            if theme_name:
                self.theme = theme_name
                self.config.theme = theme_name
                self.config_repository.save(self.config)
                try:
                    self.screen.query_one(StatusBar).show_message(f"已应用并保存主题: {theme_name}")
                except Exception:
                    pass

        self.push_screen(ThemeSelectScreen(), callback=on_theme_selected)
