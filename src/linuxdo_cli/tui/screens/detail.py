from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Label, Button
from textual.containers import Horizontal

from ..messages import DetailLoaded, DetailFailed, DetailPostsAppended
from ..widgets.post_view import PostView
from ..widgets.posts_container import PostsContainer
from ..widgets.status_bar import StatusBar


class DetailScreen(Screen):
    """话题详情界面"""

    BINDINGS = [
        Binding("escape", "go_back", "返回", show=True),
        Binding("j,down", "scroll_down", "向下", show=False),
        Binding("k,up", "scroll_up", "向上", show=False),
        Binding("pageup", "scroll_page_up", show=False),
        Binding("pagedown", "scroll_page_down", show=False),
        Binding("g", "scroll_top", "顶部", show=False),
        Binding("G", "scroll_bottom", "底部", show=False),
    ]

    def __init__(self, topic_id: int, title: str) -> None:
        super().__init__()
        self.topic_id = topic_id
        self.topic_title = title
        self._loaded_post_ids: list[int] = []
        self._remaining_post_ids: list[int] = []
        self._total_post_count: int = 0
        self._is_appending: bool = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="detail-header"):
            yield Button("← 返回", id="detail-back-btn")
            yield Label(f"§ {self.topic_title}", id="detail-title")
        yield PostsContainer(id="posts-container")
        yield StatusBar()

    def on_mount(self) -> None:
        self.refresh_responsive_layout()
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = True
        self._load_detail(self.topic_id)

    def refresh_responsive_layout(self) -> None:
        try:
            back_button = self.query_one("#detail-back-btn", Button)
            back_button.label = "←" if self.app.has_class("-viewport-narrow") else "← 返回"
        except Exception:
            pass

    def _load_detail(self, topic_id: int) -> None:
        def _run() -> None:
            import asyncio
            try:
                result = asyncio.run(self.app.topic_detail_service.load_detail(topic_id))
                self.app.call_from_thread(self.post_message, DetailLoaded(result=result, is_append=False))
            except Exception as e:
                self.app.call_from_thread(self.post_message, DetailFailed(error=str(e), is_append=False))

        self.run_worker(_run, exclusive=True, thread=True)

    def _load_more_posts(self) -> None:
        if self._is_appending or not self._remaining_post_ids:
            return

        self._is_appending = True
        self.query_one(StatusBar).is_loading = True

        def _run() -> None:
            import asyncio
            try:
                result = asyncio.run(
                    self.app.topic_detail_service.load_more_posts(
                        self.topic_id,
                        self._remaining_post_ids,
                        loaded_post_ids=self._loaded_post_ids,
                    )
                )
                self.app.call_from_thread(self.post_message, DetailPostsAppended(result=result))
            except Exception as e:
                self.app.call_from_thread(self.post_message, DetailFailed(error=str(e), is_append=True))

        self.run_worker(_run, exclusive=False, group="detail_post_fetch", thread=True)

    def on_detail_loaded(self, event: DetailLoaded) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        self._is_appending = False
        self._loaded_post_ids = list(event.result.loaded_post_ids)
        self._remaining_post_ids = list(event.result.remaining_post_ids)
        self._total_post_count = event.result.total_post_count

        for post in event.result.posts:
            self._container.mount(PostView(post))
        self._container.content_generation += 1

        status_bar.show_message(
            f"已加载 {event.result.post_count}/{event.result.total_post_count} 个回复"
        )

    def on_detail_posts_appended(self, event: DetailPostsAppended) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        self._is_appending = False
        self._loaded_post_ids = list(event.result.loaded_post_ids)
        self._remaining_post_ids = list(event.result.remaining_post_ids)

        for post in event.result.posts:
            self._container.mount(PostView(post))
        self._container.content_generation += 1

        if not event.result.posts:
            status_bar.show_message("已加载全部回复")
            return

        status_bar.show_message(
            f"已追加 {len(event.result.posts)} 个回复  当前已加载 {len(self._loaded_post_ids)}/{self._total_post_count}"
        )

    def on_detail_failed(self, event: DetailFailed) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        self._is_appending = False
        status_bar.show_message(f"[red]加载失败: {event.error}[/red]", duration=5.0)

    @property
    def _container(self) -> PostsContainer:
        return self.query_one("#posts-container", PostsContainer)

    def on_posts_container_reached_bottom(self, event: PostsContainer.ReachedBottom) -> None:
        self._load_more_posts()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "detail-back-btn":
            self.action_go_back()

    # ── Actions ──────────────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_scroll_down(self) -> None:
        self._container.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        self._container.scroll_up(animate=False)

    def action_scroll_page_up(self) -> None:
        self._container.scroll_page_up(animate=False)

    def action_scroll_page_down(self) -> None:
        self._container.scroll_page_down(animate=False)

    def action_scroll_top(self) -> None:
        self._container.scroll_home(animate=False)

    def action_scroll_bottom(self) -> None:
        self._container.scroll_end(animate=False)
