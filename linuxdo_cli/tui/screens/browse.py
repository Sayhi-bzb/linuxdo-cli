import webbrowser
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.work import work

from ..state import BrowseState, ViewState
from ..messages import TopicsFetched, FetchFailed
from ..widgets.category_tabs import CategoryTabs
from ..widgets.topic_list import TopicList
from ..widgets.status_bar import StatusBar


class BrowseScreen(Screen):
    """话题列表主界面"""

    BINDINGS = [
        Binding("tab", "next_category", "下一分类", show=False),
        Binding("shift+tab", "prev_category", "上一分类", show=False),
        Binding("enter", "open_topic", "打开话题", show=True),
        Binding("r", "refresh", "刷新", show=True),
        Binding("o", "open_browser", "浏览器打开", show=True),
        Binding("n", "next_page", "下一页", show=True),
        Binding("p", "prev_page", "上一页", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._state = BrowseState()

    def compose(self) -> ComposeResult:
        yield CategoryTabs()
        yield TopicList()
        yield StatusBar()

    def on_mount(self) -> None:
        self._start_fetch()

    # ── Category tab switching ──────────────────────────────────────────

    def on_category_tabs_tab_changed(self, event: CategoryTabs.TabChanged) -> None:
        if event.category == self._state.current_category:
            return
        self._state.current_category = event.category
        self._state.current_page = 0
        self._state.cursor_index = 0
        self._start_fetch(transitioning=True)

    def action_next_category(self) -> None:
        self.query_one(CategoryTabs).next_category()

    def action_prev_category(self) -> None:
        self.query_one(CategoryTabs).prev_category()

    # ── Fetch topics ────────────────────────────────────────────────────

    def _start_fetch(self, transitioning: bool = False) -> None:
        self._state.fetch_generation += 1
        self._state.view_state = ViewState.FETCHING
        self._state.is_transitioning = transitioning

        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = True

        topic_list = self.query_one(TopicList)
        topic_list.is_transitioning = transitioning

        self._fetch_topics(
            self._state.current_category,
            self._state.current_page,
            self._state.fetch_generation,
        )

    @work(exclusive=True, group="topic_fetch", thread=True)
    def _fetch_topics(self, category: str, page: int, generation: int) -> None:
        import asyncio
        try:
            client = self.app.client
            # 热门使用 /top.json，最新使用 /latest.json
            if category == "latest":
                topics = asyncio.run(client.get_latest_topics(page=page))
            else:
                # hot: 复用 get_latest_topics 逻辑但走 /top.json
                params = {"page": page} if page > 0 else None
                data = asyncio.run(client._get("/top.json", params=params))
                from ...models import LatestTopicsResponse
                topics = LatestTopicsResponse(**data).topic_list.topics
            self.app.call_from_thread(
                self.post_message, TopicsFetched(topics=topics, generation=generation)
            )
        except Exception as e:
            self.app.call_from_thread(
                self.post_message, FetchFailed(error=str(e), generation=generation)
            )

    def on_topics_fetched(self, event: TopicsFetched) -> None:
        if event.generation != self._state.fetch_generation:
            return  # 过时结果，丢弃
        self._state.topics = event.topics
        self._state.view_state = ViewState.BROWSING
        self._state.is_transitioning = False

        topic_list = self.query_one(TopicList)
        topic_list.topics = event.topics
        topic_list.is_transitioning = False

        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        status_bar.show_message(
            f"已加载 {len(event.topics)} 个话题  第 {self._state.current_page + 1} 页"
        )

        # 焦点移到列表
        topic_list.focus()
        # 如果有话题，高亮第一个
        if event.topics:
            topic_list.index = 0

    def on_fetch_failed(self, event: FetchFailed) -> None:
        if event.generation != self._state.fetch_generation:
            return
        self._state.view_state = ViewState.ERROR
        self._state.is_transitioning = False

        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        status_bar.show_message(f"[red]加载失败: {event.error}[/red]", duration=5.0)

        topic_list = self.query_one(TopicList)
        topic_list.is_transitioning = False

    # ── Actions ─────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        self._start_fetch(transitioning=True)

    def action_next_page(self) -> None:
        self._state.current_page += 1
        self._start_fetch(transitioning=True)

    def action_prev_page(self) -> None:
        if self._state.current_page > 0:
            self._state.current_page -= 1
            self._start_fetch(transitioning=True)

    def action_open_topic(self) -> None:
        topic_list = self.query_one(TopicList)
        idx = topic_list.index
        if idx is None or not self._state.topics:
            return
        if idx >= len(self._state.topics):
            return
        topic = self._state.topics[idx]
        from .detail import DetailScreen
        self.app.push_screen(DetailScreen(topic.id, topic.title))

    def action_open_browser(self) -> None:
        topic_list = self.query_one(TopicList)
        idx = topic_list.index
        if idx is None or not self._state.topics:
            return
        if idx >= len(self._state.topics):
            return
        topic = self._state.topics[idx]
        url = f"{self.app.client.base_url}/t/{topic.slug}/{topic.id}"
        webbrowser.open(url)
        self.query_one(StatusBar).show_message(f"已在浏览器打开: {topic.title[:40]}")
