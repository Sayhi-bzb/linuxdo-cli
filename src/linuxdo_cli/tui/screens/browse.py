import webbrowser
from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import ListView

from ...services import TopicQuery
from ..state import BrowseState, ViewState
from ..messages import TopicsFetched, FetchFailed
from ..widgets.category_tabs import CategoryTabs
from ..widgets.topic_list import TopicList
from ..widgets.status_bar import StatusBar


class BrowseScreen(Screen):
    """话题列表主界面"""

    BINDINGS = [
        Binding("tab", "next_category", "下一分类", show=True),
        Binding("shift+tab", "prev_category", "上一分类", show=False),
        Binding("r", "refresh", "刷新", show=True),
        Binding("o", "open_browser", "浏览器打开", show=True),
        Binding("n", "load_more", "下一页", show=True),
        Binding("ctrl+q", "quit", "退出", show=True),
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

    def refresh_responsive_layout(self) -> None:
        try:
            self.query_one(CategoryTabs).refresh_responsive_layout()
        except Exception:
            pass

    # ── Category tab switching ──────────────────────────────────────────

    def on_category_tabs_tab_changed(self, event: CategoryTabs.TabChanged) -> None:
        if event.category == "category":
            from .category_select import CategorySelectScreen
            self.app.push_screen(CategorySelectScreen(), self._on_category_picked)
            return
        if event.category == self._state.current_category:
            return
        self._state.current_category = event.category
        self._state.category_slug = ""
        self._state.category_id = 0
        self._state.category_name = ""
        self._start_fetch(transitioning=True)

    def _on_category_picked(self, cat) -> None:
        """CategorySelectScreen dismiss 回调，cat 为选中的 Category 对象，None 表示取消。"""
        if cat is None:
            return
        self._state.current_category = "category"
        self._state.category_slug = cat.slug
        self._state.category_id = cat.id
        self._state.category_name = cat.name
        self.query_one(CategoryTabs).set_active("category", cat.name)
        self._start_fetch(transitioning=True)

    def action_next_category(self) -> None:
        self.query_one(CategoryTabs).next_category()

    def action_prev_category(self) -> None:
        self.query_one(CategoryTabs).prev_category()

    # ── Fetch topics ────────────────────────────────────────────────────

    def _start_fetch(self, transitioning: bool = False) -> None:
        """Reset mode: clear list and load page 0."""
        self._state.fetch_generation += 1
        self._state.current_page = 0
        self._state.has_more = True
        self._state.is_appending = False
        self._state.view_state = ViewState.FETCHING

        self.query_one(StatusBar).is_loading = True

        topic_list = self.query_one(TopicList)
        topic_list.is_transitioning = transitioning

        self._fetch_topics(self._build_query(), self._state.fetch_generation, is_append=False)

    def _start_append(self) -> None:
        """Append mode: load next page and merge into existing list."""
        if self._state.is_appending or not self._state.has_more:
            return
        if self._state.view_state != ViewState.BROWSING:
            return
        self._state.is_appending = True
        self._state.current_page += 1
        self.query_one(StatusBar).is_loading = True
        self._fetch_topics(self._build_query(), self._state.fetch_generation, is_append=True)

    def _build_query(self) -> TopicQuery:
        return TopicQuery(
            category_key=self._state.current_category,
            page=self._state.current_page,
            category_slug=self._state.category_slug,
            category_id=self._state.category_id,
            category_name=self._state.category_name or None,
        )

    def _fetch_topics(self, query: TopicQuery, generation: int, is_append: bool = False) -> None:
        def _run() -> None:
            import asyncio
            try:
                result = asyncio.run(self.app.topic_service.fetch_topics(query))
                self.app.call_from_thread(
                    self.post_message,
                    TopicsFetched(result=result, generation=generation, is_append=is_append),
                )
            except Exception as e:
                self.app.call_from_thread(
                    self.post_message, FetchFailed(error=str(e), generation=generation)
                )

        self.run_worker(_run, exclusive=not is_append, group="topic_fetch", thread=True)

    def on_topics_fetched(self, event: TopicsFetched) -> None:
        if event.generation != self._state.fetch_generation:
            return  # 过时结果，丢弃

        topic_list = self.query_one(TopicList)
        status_bar = self.query_one(StatusBar)
        result = event.result

        if not event.is_append:
            # Reset mode
            self._state.topics = result.topics
            self._state.current_page = result.page
            self._state.current_category = result.category_key
            if result.category_name is not None:
                self._state.category_name = result.category_name
            self._state.has_more = result.has_more
            self._state.view_state = ViewState.BROWSING

            topic_list.topics = result.topics
            topic_list.is_transitioning = False

            status_bar.is_loading = False
            status_bar.show_message(
                f"已加载 {len(result.topics)} 个话题  第 {result.page + 1} 页"
            )

            topic_list.focus()
            if result.topics:
                topic_list.call_after_refresh(lambda: setattr(topic_list, "index", 0))
        else:
            # Append mode
            self._state.is_appending = False
            status_bar.is_loading = False

            if not result.topics:
                self._state.has_more = False
                status_bar.show_message("已加载全部话题")
                return

            prev_index = topic_list.index
            merged = self._state.topics + result.topics
            self._state.topics = merged
            self._state.current_page = result.page
            self._state.has_more = result.has_more
            topic_list.topics = merged

            if prev_index is not None:
                topic_list.call_after_refresh(
                    lambda: setattr(topic_list, "index", prev_index)
                )
            status_bar.show_message(
                f"已追加 {len(result.topics)} 个话题  当前共 {len(merged)} 个"
            )

    def on_fetch_failed(self, event: FetchFailed) -> None:
        if event.generation != self._state.fetch_generation:
            return
        self._state.view_state = ViewState.ERROR
        self._state.is_appending = False

        status_bar = self.query_one(StatusBar)
        status_bar.is_loading = False
        status_bar.show_message(f"[red]加载失败: {event.error}[/red]", duration=5.0)
        self.query_one(TopicList).is_transitioning = False

    # ── Infinite scroll trigger ─────────────────────────────────────────

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        total = len(self._state.topics)
        if total == 0 or not self._state.has_more or self._state.is_appending:
            return
        current_index = self.query_one(TopicList).index
        threshold = total - 1 if total <= 3 else total - 2
        if current_index is not None and current_index >= threshold:
            self._start_append()

    def on_topic_list_reached_bottom(self, event: TopicList.ReachedBottom) -> None:
        self._start_append()

    # ── Actions ─────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        self._start_fetch(transitioning=True)

    def action_load_more(self) -> None:
        self._start_append()

    def _selected_topic(self):
        idx = self.query_one(TopicList).index
        if idx is None or not self._state.topics or idx >= len(self._state.topics):
            return None
        return self._state.topics[idx]

    def on_list_view_selected(self, event: TopicList.Selected) -> None:
        topic = self._selected_topic()
        if topic is None:
            return
        from .detail import DetailScreen
        self.app.push_screen(DetailScreen(topic.id, topic.title))

    def action_open_browser(self) -> None:
        topic = self._selected_topic()
        if topic is None:
            return
        url = f"{self.app.client.base_url}/t/{topic.slug}/{topic.id}"
        webbrowser.open(url)
        self.query_one(StatusBar).show_message(f"已在浏览器打开: {topic.title[:40]}")
