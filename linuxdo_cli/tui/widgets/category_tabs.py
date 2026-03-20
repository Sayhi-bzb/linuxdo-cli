from textual.app import ComposeResult
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.message import Message
from textual.containers import Horizontal


CATEGORIES = [
    ("latest", "● 最新"),
    ("hot", "★ 热门"),
    ("category", "◈ 分类"),
]


class CategoryTabs(Widget):
    """顶部分类 Tab 栏"""

    class TabChanged(Message):
        def __init__(self, category: str) -> None:
            super().__init__()
            self.category = category

    active_category: reactive[str] = reactive("latest")
    # 当前选中的分类名（active_category == "category" 时展示）
    category_label: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label(" LINUX DO ", id="brand-logo")
        with Horizontal(id="tabs-container"):
            for key, label in CATEGORIES:
                classes = "tab-item -active" if key == self.active_category else "tab-item"
                yield Label(self._label_for(key), id=f"tab-{key}", classes=classes)

    def on_mount(self) -> None:
        self.refresh_responsive_layout()

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
        self._refresh_tab_labels()

    def watch_category_label(self, label: str) -> None:
        """当分类名称更新时，刷新 Tab 显示文字。"""
        self._refresh_tab_labels()

    def refresh_responsive_layout(self) -> None:
        self._refresh_tab_labels()

    def _refresh_tab_labels(self) -> None:
        for key, _ in CATEGORIES:
            try:
                tab = self.query_one(f"#tab-{key}", Label)
                tab.update(self._label_for(key))
            except Exception:
                pass

    def _label_for(self, key: str) -> str:
        compact = self.app.has_class("-viewport-medium") or self.app.has_class("-viewport-narrow")
        if key == "category" and self.category_label:
            if compact:
                limit = 4 if self.app.has_class("-viewport-narrow") else 6
                label = self.category_label[:limit]
                if len(self.category_label) > limit:
                    label += "…"
                return label
            return f"◈ {self.category_label}"

        if compact:
            return {
                "latest": "最新",
                "hot": "热门",
                "category": "分类",
            }[key]
        return dict(CATEGORIES)[key]

    def refresh_category_label(self) -> None:
        """兼容旧逻辑的显式刷新入口。"""
        try:
            tab = self.query_one("#tab-category", Label)
            tab.update(self._label_for("category"))
        except Exception:
            pass

    def set_active(self, key: str, category_name: str = "") -> None:
        """外部调用：切换激活 Tab，并可选更新分类名标签。"""
        self.active_category = key
        if key == "category" and category_name:
            self.category_label = category_name
        elif key != "category":
            # 回到非分类 Tab 时重置分类标签文字
            self.category_label = ""

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

    def on_click(self, event: Click) -> None:
        widget_id = getattr(event.widget, "id", "") or ""
        if not widget_id.startswith("tab-"):
            return
        key = widget_id[4:]
        if key == self.active_category and key != "category":
            return
        self.active_category = key
        self.post_message(self.TabChanged(key))
