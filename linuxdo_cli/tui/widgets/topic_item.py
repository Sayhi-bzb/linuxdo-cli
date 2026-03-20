from textual.app import ComposeResult
from textual.widgets import ListItem, Label
from rich.text import Text
from ..theme import COLORS


class TopicItem(ListItem):
    """单个话题行"""

    def __init__(self, topic, is_transitioning: bool = False) -> None:
        super().__init__()
        self.topic = topic
        self.is_transitioning = is_transitioning

    def compose(self) -> ComposeResult:
        t = self.topic

        # 构造标题文本
        title_text = Text()
        if t.pinned or t.pinned_globally:
            title_text.append("📌 ", style=COLORS["title_pinned"])
        if t.closed:
            title_text.append(t.title, style=COLORS["title_closed"])
        else:
            style = "dim" if self.is_transitioning else ""
            title_text.append(t.title, style=style)

        # 构造元信息
        last_posted = t.last_posted_at.strftime("%m-%d %H:%M")
        meta_text = Text()
        meta_text.append(f"@{t.last_poster_username}", style=COLORS["meta_author"])
        meta_text.append("  ")
        meta_text.append(f"💬 {t.reply_count}", style=COLORS["meta_replies"])
        meta_text.append(f"  👁 {t.views}  ")
        meta_text.append(last_posted, style="dim")

        yield Label(title_text, classes="topic-title")
        yield Label(meta_text, classes="topic-meta")
