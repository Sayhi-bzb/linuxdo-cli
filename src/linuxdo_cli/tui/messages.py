from textual.message import Message

from ..services import FetchTopicsResult, TopicDetailResult, TopicPostsPageResult


class TopicsFetched(Message):
    def __init__(self, result: FetchTopicsResult, generation: int, is_append: bool = False) -> None:
        super().__init__()
        self.result = result
        self.generation = generation
        self.is_append = is_append


class FetchFailed(Message):
    def __init__(self, error: str, generation: int) -> None:
        super().__init__()
        self.error = error
        self.generation = generation


class DetailLoaded(Message):
    def __init__(self, result: TopicDetailResult, is_append: bool = False) -> None:
        super().__init__()
        self.result = result
        self.is_append = is_append


class DetailPostsAppended(Message):
    def __init__(self, result: TopicPostsPageResult) -> None:
        super().__init__()
        self.result = result


class DetailFailed(Message):
    def __init__(self, error: str, is_append: bool = False) -> None:
        super().__init__()
        self.error = error
        self.is_append = is_append
