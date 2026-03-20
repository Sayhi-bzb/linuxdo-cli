from markdownify import markdownify as md

def html_to_md(html: str) -> str:
    """
    将 Discourse 的 cooked HTML 转换为 Markdown。
    针对终端显示进行了一些简单的清理和转换。
    """
    if not html:
        return ""
    
    # 使用 markdownify 进行基础转换
    # strip: 移除不需要的标签，heading_style: 使用 # 风格的标题
    markdown = md(
        html,
        heading_style="ATX",
        bullets="-",
        strip=['script', 'style']
    )
    
    # 清理多余的换行符
    lines = [line.strip() for line in markdown.split('\n')]
    cleaned_markdown = '\n'.join([line for i, line in enumerate(lines) if line or (i > 0 and lines[i-1])])
    
    return cleaned_markdown
