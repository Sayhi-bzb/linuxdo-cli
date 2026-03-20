from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import ListView
from .topic_item import TopicItem


class TopicList(ListView):
    """话题列表 Widget"""

    BINDINGS = [
        Binding("j,down", "cursor_down", "下移", show=False),
        Binding("k,up", "cursor_up", "上移", show=False),
        Binding("g", "scroll_home", "顶部", show=False),
        Binding("G", "scroll_end", "底部", show=False),
    ]

    DEFAULT_CSS = """
    TopicList {
        height: 1fr;
    }
    TopicList > ListItem {
        padding: 0 1;
        border-bottom: dashed $surface-lighten-1;
    }
    TopicList > ListItem:focus {
        background: $surface-lighten-1;
    }
    TopicList > ListItem.-highlight {
        background: $accent 20%;
    }
    .topic-title {
        text-style: bold;
    }
    .topic-meta {
        color: $text-disabled;
    }
    """

    topics: reactive[list] = reactive([], recompose=True)
    is_transitioning: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        for topic in self.topics:
            yield TopicItem(topic, is_transitioning=self.is_transitioning)

    def action_scroll_home(self) -> None:
        self.index = 0

    def action_scroll_end(self) -> None:
        if self.topics:
            self.index = len(self.topics) - 1
