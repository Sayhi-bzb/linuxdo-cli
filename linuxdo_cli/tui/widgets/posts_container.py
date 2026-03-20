from textual.message import Message
from textual.reactive import reactive
from textual.containers import ScrollableContainer


class PostsContainer(ScrollableContainer):
    """Scrollable posts viewport that reports when it reaches the bottom."""

    class ReachedBottom(Message):
        def __init__(self, posts_container: "PostsContainer") -> None:
            super().__init__()
            self.posts_container = posts_container

    content_generation: reactive[int] = reactive(0)
    _bottom_reported: bool = False

    def watch_content_generation(self, generation: int) -> None:
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
