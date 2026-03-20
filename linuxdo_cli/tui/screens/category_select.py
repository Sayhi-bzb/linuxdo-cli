from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList, Input
from textual.widgets.option_list import Option
from textual.containers import Vertical
from rich.text import Text


class CategorySelectScreen(ModalScreen):
    """重写的分类选择面板 - 采用卡片式布局，修复边框和空行问题"""

    BINDINGS = [
        Binding("escape", "dismiss", "关闭", show=True),
        Binding("j,down", "cursor_down", show=False),
        Binding("k,up", "cursor_up", show=False),
        Binding("slash", "focus_input", "搜索", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._all_cats = []
        self._filtered_cats = []

    def compose(self) -> ComposeResult:
        with Vertical(id="cat-card-panel"):
            yield Label("选择分类", id="cat-card-title")
            yield Input(placeholder="   搜索分类...", id="cat-card-search")
            yield OptionList(id="cat-card-list")
            yield Label("↑↓ 移动  Enter 确认  / 搜索  Esc 关闭", id="cat-card-footer")

    def on_mount(self) -> None:
        category_map: dict = getattr(self.app, "category_map", {})
        
        if not category_map:
            ol = self.query_one("#cat-card-list", OptionList)
            ol.add_option(Option("[dim]正在加载分类数据...[/dim]", disabled=True))
            return

        # 整理分类数据：一级分类，按话题数排序
        self._all_cats = sorted(
            [c for c in category_map.values() if c.parent_category_id is None],
            key=lambda c: c.topic_count,
            reverse=True,
        )
        self._filtered_cats = list(self._all_cats)
        self._refresh_list()
        self.query_one("#cat-card-list", OptionList).focus()

    def _refresh_list(self) -> None:
        ol = self.query_one("#cat-card-list", OptionList)
        ol.clear_options()
        for cat in self._filtered_cats:
            # 构造更丰富的选项内容
            label = Text()
            label.append(f" {cat.name} ", style="bold")
            label.append(f"({cat.topic_count})", style="dim italic")
            ol.add_option(Option(label, id=str(cat.id)))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "cat-card-search":
            return
        
        search_text = event.value.lower()
        if not search_text:
            self._filtered_cats = list(self._all_cats)
        else:
            self._filtered_cats = [
                c for c in self._all_cats 
                if search_text in c.name.lower() or search_text in c.slug.lower()
            ]
        self._refresh_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._filtered_cats:
            self.dismiss(self._filtered_cats[0])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(self._filtered_cats[event.option_index])

    def action_focus_input(self) -> None:
        self.query_one("#cat-card-search", Input).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#cat-card-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#cat-card-list", OptionList).action_cursor_up()
