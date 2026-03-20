from textual.app import ComposeResult
from textual.widgets import ListItem, Label
from textual.containers import Horizontal
from rich.text import Text


class TopicItem(ListItem):
    """单个话题行"""

    def __init__(self, topic, is_transitioning: bool = False, category_map: dict | None = None) -> None:
        super().__init__()
        self.topic = topic
        self.is_transitioning = is_transitioning
        self._category_map: dict = category_map or {}

    def compose(self) -> ComposeResult:
        t = self.topic

        # 标题行
        title_text = Text()
        if t.pinned or t.pinned_globally:
            title_text.append("◆ ", style="bold #ffba00")
        title_text.append(t.title, style="dim" if (self.is_transitioning or t.closed) else "")
        yield Label(title_text, classes="topic-title")

        # 元信息行
        with Horizontal(classes="topic-meta-row"):
            cat = self._category_map.get(t.category_id)
            if cat:
                yield Label(f"[{cat.name}]", classes="meta-category")
            yield Label(f"@{t.last_poster_username}", classes="meta-author")
            yield Label(f" » {t.reply_count}", classes="meta-replies")
            yield Label(f" ○ {t.views}", classes="meta-views")
            yield Label(f" τ {t.last_posted_at.strftime('%m-%d %H:%M')}", classes="meta-time")
