from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.message import Message
from rich.text import Text
from ..theme import COLORS


CATEGORIES = [
    ("latest", "最新"),
    ("hot", "热门"),
]


class CategoryTabs(Widget):
    """顶部分类 Tab 栏"""

    DEFAULT_CSS = """
    CategoryTabs {
        dock: top;
        height: 2;
        background: $surface;
        layout: horizontal;
        padding: 0 1;
        align: left middle;
    }
    CategoryTabs .tab-item {
        padding: 0 2;
        height: 2;
        content-align: center middle;
    }
    CategoryTabs .tab-item.-active {
        color: $primary;
        text-style: bold;
        border-bottom: heavy $primary;
    }
    """

    class TabChanged(Message):
        def __init__(self, category: str) -> None:
            super().__init__()
            self.category = category

    active_category: reactive[str] = reactive("latest")

    def compose(self) -> ComposeResult:
        for key, label in CATEGORIES:
            classes = "tab-item -active" if key == self.active_category else "tab-item"
            yield Label(label, id=f"tab-{key}", classes=classes)

    def watch_active_category(self, cat: str) -> None:
        for key, _ in CATEGORIES:
            try:
                tab = self.query_one(f"#tab-{key}", Label)
                if key == cat:
                    tab.add_class("-active")
                else:
                    tab.remove_class("-active")
            except Exception:
                pass

    def next_category(self) -> None:
        keys = [k for k, _ in CATEGORIES]
        idx = keys.index(self.active_category)
        new_key = keys[(idx + 1) % len(keys)]
        self.active_category = new_key
        self.post_message(self.TabChanged(new_key))

    def prev_category(self) -> None:
        keys = [k for k, _ in CATEGORIES]
        idx = keys.index(self.active_category)
        new_key = keys[(idx - 1) % len(keys)]
        self.active_category = new_key
        self.post_message(self.TabChanged(new_key))
