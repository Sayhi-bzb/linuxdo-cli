from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Label, ScrollableContainer
from textual.work import work

from ..messages import DetailLoaded, DetailFailed
from ..widgets.post_view import PostView
from ..widgets.status_bar import StatusBar


class DetailScreen(Screen):
    """话题详情界面"""

    BINDINGS = [
        Binding("escape,q", "go_back", "返回", show=True),
        Binding("j,down", "scroll_down", "向下", show=False),
        Binding("k,up", "scroll_up", "向上", show=False),
        Binding("g", "scroll_top", "顶部", show=False),
        Binding("G", "scroll_bottom", "底部", show=False),
    ]

    def __init__(self, topic_id: int, title: str) -> None:
        super().__init__()
        self.topic_id = topic_id
        self.topic_title = title

    def compose(self) -> ComposeResult:
        yield Label(f" {self.topic_title}", id="detail-title")
        yield ScrollableContainer(id="posts-container")
        yield StatusBar()

    def on_mount(self) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = True
        self._load_detail(self.topic_id)

    @work(exclusive=True, thread=True)
    def _load_detail(self, topic_id: int) -> None:
        import asyncio
        try:
            client = self.app.client
            detail = asyncio.run(client.get_topic_detail(topic_id))
            self.app.call_from_thread(self.post_message, DetailLoaded(detail=detail))
        except Exception as e:
            self.app.call_from_thread(self.post_message, DetailFailed(error=str(e)))

    def on_detail_loaded(self, event: DetailLoaded) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False

        container = self.query_one("#posts-container", ScrollableContainer)
        posts = event.detail.post_stream.get("posts", [])
        for post in posts:
            container.mount(PostView(post))

        status_bar.show_message(
            f"{event.detail.title[:40]}  共 {event.detail.posts_count} 楼"
        )

    def on_detail_failed(self, event: DetailFailed) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        status_bar.show_message(f"[red]加载失败: {event.error}[/red]", duration=5.0)

    # ── Actions ──────────────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_scroll_down(self) -> None:
        container = self.query_one("#posts-container", ScrollableContainer)
        container.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        container = self.query_one("#posts-container", ScrollableContainer)
        container.scroll_up(animate=False)

    def action_scroll_top(self) -> None:
        container = self.query_one("#posts-container", ScrollableContainer)
        container.scroll_home(animate=False)

    def action_scroll_bottom(self) -> None:
        container = self.query_one("#posts-container", ScrollableContainer)
        container.scroll_end(animate=False)
