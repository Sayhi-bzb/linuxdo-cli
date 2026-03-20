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
    current_category: str = "latest"
    fetch_generation: int = 0  # 防竞态计数器
    has_more: bool = True       # False = 已到最后一页，停止追加
    is_appending: bool = False  # True = 追加请求进行中（防重入）
    # 分类 Tab 专用字段（current_category == "category" 时生效）
    category_slug: str = ""
    category_id: int = 0
    category_name: str = ""
