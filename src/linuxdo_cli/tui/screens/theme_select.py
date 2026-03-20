from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label
from textual.containers import Vertical
from ..theme import THEMES


class ThemeSelectScreen(ModalScreen):
    """主题选择面板（带有实时预览）"""

    BINDINGS = [
        Binding("escape,q", "cancel", "取消", show=True),
        Binding("t", "cancel", "取消", show=False),
        Binding("enter", "select_theme", "确认", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.original_theme = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-select-container"):
            yield Label("选择主题 (Select Theme)", id="theme-select-title")
            yield OptionList(
                *[theme.name for theme in THEMES],
                id="theme-option-list"
            )
            yield Label("[dim]方向键预览，回车确认，Esc 取消[/dim]", id="theme-select-footer")

    def on_mount(self) -> None:
        self.original_theme = self.app.theme
        # 预选中当前主题
        option_list = self.query_one(OptionList)
        for i, theme in enumerate(THEMES):
            if theme.name == self.original_theme:
                option_list.highlighted = i
                break

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """实现实时预览：当光标移动时即时应用主题"""
        if event.option:
            theme_name = str(event.option.prompt)
            self.app.theme = theme_name

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_select_theme()

    def action_select_theme(self) -> None:
        """确认选择"""
        option_list = self.query_one(OptionList)
        if option_list.highlighted is not None:
            theme_name = str(option_list.get_option_at_index(option_list.highlighted).prompt)
            self.dismiss(theme_name)

    def action_cancel(self) -> None:
        """取消并恢复原始主题"""
        self.app.theme = self.original_theme
        self.dismiss(None)
