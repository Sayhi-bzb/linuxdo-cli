from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Markdown, Label
from ...utils.converter import html_to_md


class PostView(Widget):
    """单篇帖子渲染"""

    def __init__(self, post: dict) -> None:
        super().__init__()
        self.post = post

        author = post.get("display_username") or post.get("username", "?")
        created_at = post.get("created_at", "")
        if created_at and "T" in created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        cooked = post.get("cooked", "")
        body = html_to_md(cooked)
        # 把 meta 行作为 markdown 的第一行（用 blockquote 样式区分）
        meta_line = f"**@{author}**  *{created_at}*"
        self._md_content = f"{meta_line}\n\n{body}" if body else meta_line

    def compose(self) -> ComposeResult:
        yield Markdown(self._md_content)
