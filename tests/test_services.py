from unittest.mock import AsyncMock, Mock

import pytest

from linuxdo_cli.services import (
    TopicDetailService,
    TopicDetailServiceError,
    TopicPostsPageResult,
    TopicQuery,
    TopicService,
    TopicServiceError,
)
from tests.conftest import FAKE_DETAIL, FAKE_DETAIL_WITH_STREAM, FAKE_TOPICS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("category_key", "method_name"),
    [
        ("latest", "get_latest_topics"),
        ("hot", "get_hot_topics"),
    ],
)
async def test_topic_service_dispatches_builtin_categories(category_key, method_name):
    client = Mock()
    client.get_latest_topics = AsyncMock()
    client.get_hot_topics = AsyncMock()
    client.get_category_topics = AsyncMock()
    getattr(client, method_name).return_value = FAKE_TOPICS

    result = await TopicService(client).fetch_topics(TopicQuery(category_key=category_key, page=1))

    getattr(client, method_name).assert_awaited_once_with(page=1)
    assert result.topics == FAKE_TOPICS
    assert result.page == 1
    assert result.category_key == category_key
    assert result.has_more is True


@pytest.mark.asyncio
async def test_topic_service_dispatches_category_query():
    client = Mock()
    client.get_latest_topics = AsyncMock()
    client.get_hot_topics = AsyncMock()
    client.get_category_topics = AsyncMock(return_value=FAKE_TOPICS)

    result = await TopicService(client).fetch_topics(
        TopicQuery(
            category_key="category",
            page=2,
            category_slug="dev",
            category_id=42,
            category_name="开发",
        )
    )

    client.get_category_topics.assert_awaited_once_with("dev", 42, page=2)
    assert result.category_name == "开发"
    assert result.has_more is True


@pytest.mark.asyncio
async def test_topic_service_marks_no_more_when_page_is_empty():
    client = Mock()
    client.get_latest_topics = AsyncMock(return_value=[])
    client.get_hot_topics = AsyncMock()
    client.get_category_topics = AsyncMock()

    result = await TopicService(client).fetch_topics(TopicQuery(category_key="latest", page=3))

    assert result.topics == []
    assert result.has_more is False


@pytest.mark.asyncio
async def test_topic_service_requires_complete_category_query():
    client = Mock()
    client.get_latest_topics = AsyncMock()
    client.get_hot_topics = AsyncMock()
    client.get_category_topics = AsyncMock()

    with pytest.raises(TopicServiceError, match="分类参数不完整"):
        await TopicService(client).fetch_topics(TopicQuery(category_key="category"))


@pytest.mark.asyncio
async def test_detail_service_extracts_posts():
    client = Mock()
    client.get_topic_detail = AsyncMock(return_value=FAKE_DETAIL)

    result = await TopicDetailService(client).load_detail(1)

    client.get_topic_detail.assert_awaited_once_with(1)
    assert result.detail == FAKE_DETAIL
    assert result.post_count == 1
    assert result.posts == FAKE_DETAIL.post_stream["posts"]
    assert result.loaded_post_ids == [1]
    assert result.remaining_post_ids == []
    assert result.has_more is False


@pytest.mark.asyncio
async def test_detail_service_extracts_remaining_post_ids_from_stream():
    client = Mock()
    client.get_topic_detail = AsyncMock(return_value=FAKE_DETAIL_WITH_STREAM)

    result = await TopicDetailService(client).load_detail(1)

    assert result.loaded_post_ids == [1]
    assert result.remaining_post_ids == [2, 3]
    assert result.has_more is True


@pytest.mark.asyncio
async def test_detail_service_loads_more_posts_in_batches():
    client = Mock()
    client.get_topic_posts = AsyncMock(
        return_value=[
            {"id": 2, "username": "alice", "created_at": "2024-01-01T00:00:00Z", "cooked": "<p>A</p>"},
            {"id": 3, "username": "bob", "created_at": "2024-01-01T00:00:00Z", "cooked": "<p>B</p>"},
        ]
    )

    result = await TopicDetailService(client).load_more_posts(
        1,
        [2, 3, 4],
        loaded_post_ids=[1],
        batch_size=2,
    )

    client.get_topic_posts.assert_awaited_once_with(1, [2, 3])
    assert result.posts[0]["id"] == 2
    assert result.loaded_post_ids == [1, 2, 3]
    assert result.remaining_post_ids == [4]
    assert result.has_more is True


@pytest.mark.asyncio
async def test_detail_service_validates_topic_id():
    client = Mock()
    client.get_topic_detail = AsyncMock()

    with pytest.raises(TopicDetailServiceError, match="话题 ID 无效"):
        await TopicDetailService(client).load_detail(0)


@pytest.mark.asyncio
async def test_detail_service_load_more_validates_topic_id():
    client = Mock()
    client.get_topic_posts = AsyncMock()

    with pytest.raises(TopicDetailServiceError, match="话题 ID 无效"):
        await TopicDetailService(client).load_more_posts(0, [1, 2])
