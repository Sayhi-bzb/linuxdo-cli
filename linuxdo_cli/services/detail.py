from dataclasses import dataclass, field

from ..client import LinuxDoClient, LinuxDoClientError
from ..models import TopicDetail


class TopicDetailServiceError(Exception):
    """Raised when topic detail loading fails."""


@dataclass(slots=True)
class TopicDetailResult:
    detail: TopicDetail
    posts: list[dict] = field(default_factory=list)
    post_count: int = 0
    total_post_count: int = 0
    loaded_post_ids: list[int] = field(default_factory=list)
    remaining_post_ids: list[int] = field(default_factory=list)
    has_more: bool = False


@dataclass(slots=True)
class TopicPostsPageResult:
    posts: list[dict] = field(default_factory=list)
    loaded_post_ids: list[int] = field(default_factory=list)
    remaining_post_ids: list[int] = field(default_factory=list)
    has_more: bool = False


class TopicDetailService:
    def __init__(self, client: LinuxDoClient) -> None:
        self._client = client

    async def load_detail(self, topic_id: int) -> TopicDetailResult:
        if topic_id <= 0:
            raise TopicDetailServiceError("话题 ID 无效")

        try:
            detail = await self._client.get_topic_detail(topic_id)
        except LinuxDoClientError as exc:
            raise TopicDetailServiceError(str(exc)) from exc
        except Exception as exc:
            raise TopicDetailServiceError(f"加载详情失败: {exc}") from exc

        posts, loaded_post_ids, remaining_post_ids = self._extract_post_stream(detail)

        return TopicDetailResult(
            detail=detail,
            posts=posts,
            post_count=len(posts),
            total_post_count=detail.posts_count,
            loaded_post_ids=loaded_post_ids,
            remaining_post_ids=remaining_post_ids,
            has_more=bool(remaining_post_ids),
        )

    async def load_more_posts(
        self,
        topic_id: int,
        remaining_post_ids: list[int],
        loaded_post_ids: list[int] | None = None,
        batch_size: int = 20,
    ) -> TopicPostsPageResult:
        if topic_id <= 0:
            raise TopicDetailServiceError("话题 ID 无效")

        if batch_size <= 0:
            raise TopicDetailServiceError("batch_size 必须大于 0")

        if not remaining_post_ids:
            return TopicPostsPageResult(
                posts=[],
                loaded_post_ids=list(loaded_post_ids or []),
                remaining_post_ids=[],
                has_more=False,
            )

        next_post_ids = remaining_post_ids[:batch_size]
        try:
            posts = await self._client.get_topic_posts(topic_id, next_post_ids)
        except LinuxDoClientError as exc:
            raise TopicDetailServiceError(str(exc)) from exc
        except Exception as exc:
            raise TopicDetailServiceError(f"加载更多回复失败: {exc}") from exc

        fetched_ids = [
            int(post["id"])
            for post in posts
            if isinstance(post, dict) and post.get("id") is not None
        ]
        merged_loaded_ids = list(loaded_post_ids or []) + fetched_ids
        new_remaining_post_ids = remaining_post_ids[len(next_post_ids):]

        return TopicPostsPageResult(
            posts=posts,
            loaded_post_ids=merged_loaded_ids,
            remaining_post_ids=new_remaining_post_ids,
            has_more=bool(new_remaining_post_ids),
        )

    @staticmethod
    def _extract_post_stream(detail: TopicDetail) -> tuple[list[dict], list[int], list[int]]:
        posts: list[dict] = []
        stream_ids: list[int] = []
        if isinstance(detail.post_stream, dict):
            raw_posts = detail.post_stream.get("posts", [])
            if isinstance(raw_posts, list):
                posts = raw_posts

            raw_stream = detail.post_stream.get("stream", [])
            if isinstance(raw_stream, list):
                stream_ids = [int(post_id) for post_id in raw_stream]

        loaded_post_ids = [
            int(post["id"])
            for post in posts
            if isinstance(post, dict) and post.get("id") is not None
        ]
        loaded_post_id_set = set(loaded_post_ids)
        remaining_post_ids = [post_id for post_id in stream_ids if post_id not in loaded_post_id_set]
        return posts, loaded_post_ids, remaining_post_ids
