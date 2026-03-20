from textual.message import Message
from typing import List, Any


class TopicsFetched(Message):
    """话题列表加载完成"""
    def __init__(self, topics: list, generation: int) -> None:
        super().__init__()
        self.topics = topics
        self.generation = generation


class FetchFailed(Message):
    """话题列表加载失败"""
    def __init__(self, error: str, generation: int) -> None:
        super().__init__()
        self.error = error
        self.generation = generation


class DetailLoaded(Message):
    """话题详情加载完成"""
    def __init__(self, detail: Any) -> None:
        super().__init__()
        self.detail = detail


class DetailFailed(Message):
    """话题详情加载失败"""
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error
