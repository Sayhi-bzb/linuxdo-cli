from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import Horizontal


class StatusBar(Widget):
    """底部状态栏，增强信息密度"""

    is_loading: reactive[bool] = reactive(False)
    status_message: reactive[str] = reactive("")
    
    # Unicode 动画帧
    SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    _frame_index: int = 0
    _msg_generation: int = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("⠋", id="spinner", classes="status-item")
            yield Label("", id="status-label", classes="status-item main-msg")
            yield Label("", id="theme-label", classes="status-item")
            yield Label("", id="density-label", classes="status-item")

    def on_mount(self) -> None:
        self.set_interval(0.1, self.update_spinner)
        self.set_interval(0.5, self.update_stats)

    def update_spinner(self) -> None:
        sp = self.query_one("#spinner", Label)
        if self.is_loading:
            sp.update(self.SPINNER_FRAMES[self._frame_index])
            self._frame_index = (self._frame_index + 1) % len(self.SPINNER_FRAMES)
        else:
            sp.update(" ")

    def update_stats(self) -> None:
        """更新辅助状态信息"""
        try:
            # 更新主题显示
            theme_label = self.query_one("#theme-label", Label)
            theme_label.update(f" MODE: {self.app.theme.upper()} ")
            
            # 更新密度显示
            density_label = self.query_one("#density-label", Label)
            density = getattr(self.app.config, "layout_density", "standard")
            density_label.update(f" DENSITY: {density.upper()} ")
        except Exception:
            pass

    def watch_status_message(self, msg: str) -> None:
        label = self.query_one("#status-label", Label)
        label.update(f" {msg} ")

    def show_message(self, msg: str, duration: float = 3.0) -> None:
        self._msg_generation += 1
        gen = self._msg_generation
        self.status_message = msg
        
        def clear():
            if gen == self._msg_generation:
                self.status_message = ""
        
        self.set_timer(duration, clear)
