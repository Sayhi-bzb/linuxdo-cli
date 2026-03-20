from enum import Enum, auto
from dataclasses import dataclass, field


class ViewState(Enum):
    STARTUP = auto()   # 等待首次加载
    FETCHING = auto()  # 网络请求中
    BROWSING = auto()  # 空闲，正常交互
    ERROR = auto()     # 加载失败


@dataclass
class BrowseState:
    view_state: ViewState = ViewState.STARTUP
    topics: list = field(default_factory=list)
    current_page: int = 0
    cursor_index: int = 0
    current_category: str = "latest"
    is_transitioning: bool = False  # 切换时保留旧数据（防闪烁）
    fetch_generation: int = 0       # 防竞态计数器
