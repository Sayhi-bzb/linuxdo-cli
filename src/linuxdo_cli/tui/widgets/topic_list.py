from textual.message import Message
from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import ListView
from .topic_item import TopicItem


class TopicList(ListView):
    """话题列表 Widget"""

    class ReachedBottom(Message):
        """Posted when the scroll viewport reaches the bottom."""

        def __init__(self, topic_list: "TopicList") -> None:
            super().__init__()
            self.topic_list = topic_list

    BINDINGS = [
        Binding("j,down", "cursor_down", "下移", show=False),
        Binding("k,up", "cursor_up", "上移", show=False),
        Binding("g,home", "scroll_home", "顶部", show=False),
        Binding("G,end", "scroll_end", "底部", show=False),
    ]

    topics: reactive[list] = reactive([], recompose=True)
    is_transitioning: reactive[bool] = reactive(False)
    _bottom_reported: bool = False

    def compose(self) -> ComposeResult:
        category_map: dict = getattr(self.app, "category_map", {})  # id → Category
        for topic in self.topics:
            yield TopicItem(topic, is_transitioning=self.is_transitioning, category_map=category_map)

    def watch_topics(self, topics: list) -> None:
        self._bottom_reported = False

    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        super().watch_scroll_y(old_value, new_value)
        self._notify_reached_bottom()

    def _notify_reached_bottom(self) -> None:
        if self.max_scroll_y <= 0:
            self._bottom_reported = False
            return

        if self.scroll_y >= self.max_scroll_y:
            if not self._bottom_reported:
                self._bottom_reported = True
                self.post_message(self.ReachedBottom(self))
        else:
            self._bottom_reported = False

    def action_scroll_home(self) -> None:
        self.index = 0

    def action_scroll_end(self) -> None:
        if self.topics:
            self.index = len(self.topics) - 1
