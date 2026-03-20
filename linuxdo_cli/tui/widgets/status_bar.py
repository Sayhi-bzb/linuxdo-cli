from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    StatusBar Label {
        width: 1fr;
    }
    """

    is_loading: reactive[bool] = reactive(False)
    status_message: reactive[str] = reactive("")

    _msg_generation: int = 0

    def compose(self) -> ComposeResult:
        yield Label("", id="status-label")

    def watch_is_loading(self, loading: bool) -> None:
        self._update_label()

    def watch_status_message(self, msg: str) -> None:
        self._update_label()

    def _update_label(self) -> None:
        label = self.query_one("#status-label", Label)
        if self.is_loading:
            label.update("[@click] 加载中...")
        elif self.status_message:
            label.update(self.status_message)
        else:
            label.update("")

    def show_message(self, msg: str, duration: float = 2.0) -> None:
        self._msg_generation += 1
        gen = self._msg_generation
        self.status_message = msg
        self.set_timer(duration, lambda: self._clear_if_same_gen(gen))

    def _clear_if_same_gen(self, gen: int) -> None:
        if gen == self._msg_generation:
            self.status_message = ""
