import re
from markdownify import markdownify as md, MarkdownConverter

# alt 无实际描述的模式：纯空白、"image"、纯数字、文件名形式（word.ext）
_MEANINGLESS_ALT = re.compile(
    r'^(image[\d×x]*|img[\d×x]*|\d+|[^. ]+\.(png|jpe?g|gif|webp|svg|bmp))$',
    re.IGNORECASE,
)


class _DiscourseConverter(MarkdownConverter):
    """处理 Discourse cooked HTML 的特殊元素。"""

    def convert_img(self, el, text, convert_as_inline=False, **kwargs):
        alt = el.get("alt", "").strip()
        classes = el.get("class", "")

        # emoji：Discourse 把 emoji 渲染成 <img class="emoji" alt=":smile:">
        if "emoji" in classes:
            return alt if alt else ""

        # 无意义 alt → [图片]，有意义 alt → [图片: 描述]
        if alt and not _MEANINGLESS_ALT.match(alt):
            return f"[图片: {alt}]"
        return "[图片]"

    def convert_a(self, el, text, **kwargs):
        # Discourse lightbox 链接只包一个图片，text 已被 convert_img 处理成 [图片]
        # 直接返回内部文本，丢弃 URL
        if "lightbox" in el.get("class", ""):
            return text
        return super().convert_a(el, text, **kwargs)


def html_to_md(html: str) -> str:
    """将 Discourse 的 cooked HTML 转换为 Markdown。"""
    if not html:
        return ""

    markdown = _DiscourseConverter(
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    ).convert(html)

    # 清理多余的换行符
    lines = [line.strip() for line in markdown.split("\n")]
    cleaned = "\n".join(
        line for i, line in enumerate(lines)
        if line or (i > 0 and lines[i - 1])
    )

    return cleaned
