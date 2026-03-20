from datetime import datetime
import pytest
from unittest.mock import AsyncMock, patch

from linuxdo_cli.models import Topic, TopicDetail
from linuxdo_cli.config import Config
from linuxdo_cli.services import FetchTopicsResult, TopicDetailResult, TopicPostsPageResult


def make_topic(id: int, title: str = None, slug: str = None) -> Topic:
    return Topic(
        id=id,
        title=title or f"Topic {id}",
        slug=slug or f"topic-{id}",
        posts_count=3,
        reply_count=2,
        highest_post_number=3,
        created_at=datetime(2024, 1, 1),
        last_posted_at=datetime(2024, 1, 2),
        bumped=False,
        bumped_at=datetime(2024, 1, 2),
        archetype="regular",
        unseen=False,
        pinned=False,
        visible=True,
        closed=False,
        archived=False,
        views=100,
        like_count=5,
        has_summary=False,
        last_poster_username="testuser",
        category_id=1,
        pinned_globally=False,
    )


FAKE_TOPICS = [
    make_topic(1, "Hello World", "hello-world"),
    make_topic(2, "Second Post", "second-post"),
]

FAKE_DETAIL = TopicDetail(
    id=1,
    title="Hello World",
    posts_count=1,
    created_at=datetime(2024, 1, 1),
    views=100,
    like_count=5,
    last_posted_at=datetime(2024, 1, 2),
    category_id=1,
    post_stream={"posts": [
        {
            "id": 1,
            "username": "testuser",
            "created_at": "2024-01-01T00:00:00Z",
            "cooked": "<p>Hello world content</p>",
        },
    ]},
)

FAKE_DETAIL_WITH_STREAM = TopicDetail(
    id=1,
    title="Hello World",
    posts_count=3,
    created_at=datetime(2024, 1, 1),
    views=100,
    like_count=5,
    last_posted_at=datetime(2024, 1, 2),
    category_id=1,
    post_stream={
        "stream": [1, 2, 3],
        "posts": [
            {
                "id": 1,
                "username": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
                "cooked": "<p>Hello world content</p>",
            },
        ],
    },
)

FAKE_TOP_JSON = {
    "topic_list": {
        "topics": [t.model_dump(mode="json") for t in FAKE_TOPICS]
    }
}


async def fake_fetch_topics(query):
    topics = FAKE_TOPICS if query.page == 0 else []
    return FetchTopicsResult(
        topics=topics,
        page=query.page,
        category_key=query.category_key,
        category_name=query.category_name,
        has_more=bool(topics),
    )


FAKE_DETAIL_RESULT = TopicDetailResult(
    detail=FAKE_DETAIL,
    posts=FAKE_DETAIL.post_stream["posts"],
    post_count=1,
    total_post_count=1,
    loaded_post_ids=[1],
    remaining_post_ids=[],
    has_more=False,
)

EMPTY_POSTS_PAGE_RESULT = TopicPostsPageResult(
    posts=[],
    loaded_post_ids=[1],
    remaining_post_ids=[],
    has_more=False,
)


@pytest.fixture
def mock_client():
    """Patch service methods and config repository for TUI tests."""
    fake_config = Config(
        client_id="test",
        client_secret="test",
        base_url="https://linux.do",
        connect_url="https://connect.linux.do",
    )
    with patch("linuxdo_cli.tui.app.ConfigRepository.load", return_value=fake_config):
        with patch(
            "linuxdo_cli.client.LinuxDoClient.get_categories",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "linuxdo_cli.services.topics.TopicService.fetch_topics",
                new_callable=AsyncMock,
                side_effect=fake_fetch_topics,
            ):
                with patch(
                    "linuxdo_cli.services.detail.TopicDetailService.load_detail",
                    new_callable=AsyncMock,
                    return_value=FAKE_DETAIL_RESULT,
                ):
                    with patch(
                        "linuxdo_cli.services.detail.TopicDetailService.load_more_posts",
                        new_callable=AsyncMock,
                        return_value=EMPTY_POSTS_PAGE_RESULT,
                    ):
                        yield
