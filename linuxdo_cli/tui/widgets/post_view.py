from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Markdown, Label
from rich.text import Text
from ..theme import COLORS
from ...utils.converter import html_to_md


class PostView(Widget):
    """单篇帖子渲染"""

    DEFAULT_CSS = """
    PostView {
        border-bottom: dashed $surface-lighten-1;
        padding: 1 2;
    }
    PostView .post-meta {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self, post: dict) -> None:
        super().__init__()
        self.post = post

    def compose(self) -> ComposeResult:
        post = self.post
        author = post.get("display_username") or post.get("username", "?")
        created_at = post.get("created_at", "")
        cooked = post.get("cooked", "")
        md_content = html_to_md(cooked)

        meta = Text()
        meta.append(f"@{author}", style=COLORS["post_author"])
        meta.append(f"  {created_at}", style="dim")

        yield Label(meta, classes="post-meta")
        if md_content:
            yield Markdown(md_content)
        else:
            yield Label("[dim](空内容)[/dim]")
