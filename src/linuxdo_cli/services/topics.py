from dataclasses import dataclass, field

from ..client import LinuxDoClient, LinuxDoClientError
from ..models import Topic


class TopicServiceError(Exception):
    """Raised when topic fetching cannot be completed."""


@dataclass(slots=True)
class TopicQuery:
    category_key: str = "latest"
    page: int = 0
    category_slug: str = ""
    category_id: int = 0
    category_name: str | None = None


@dataclass(slots=True)
class FetchTopicsResult:
    topics: list[Topic] = field(default_factory=list)
    page: int = 0
    category_key: str = "latest"
    category_name: str | None = None
    has_more: bool = True


class TopicService:
    def __init__(self, client: LinuxDoClient) -> None:
        self._client = client

    async def fetch_topics(self, query: TopicQuery) -> FetchTopicsResult:
        if query.page < 0:
            raise TopicServiceError("页码不能小于 0")

        try:
            if query.category_key == "latest":
                topics = await self._client.get_latest_topics(page=query.page)
                category_name = None
            elif query.category_key == "hot":
                topics = await self._client.get_hot_topics(page=query.page)
                category_name = None
            elif query.category_key == "category":
                if not query.category_slug or not query.category_id:
                    raise TopicServiceError("分类参数不完整，无法加载分类话题")
                topics = await self._client.get_category_topics(
                    query.category_slug,
                    query.category_id,
                    page=query.page,
                )
                category_name = query.category_name
            else:
                raise TopicServiceError(f"不支持的分类: {query.category_key}")
        except TopicServiceError:
            raise
        except LinuxDoClientError as exc:
            raise TopicServiceError(str(exc)) from exc
        except Exception as exc:
            raise TopicServiceError(f"加载话题失败: {exc}") from exc

        return FetchTopicsResult(
            topics=topics,
            page=query.page,
            category_key=query.category_key,
            category_name=category_name,
            has_more=bool(topics),
        )
