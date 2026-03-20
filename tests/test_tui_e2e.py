"""E2E tests for linuxdo-cli TUI core interactions."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from linuxdo_cli.config import Config
from linuxdo_cli.services import FetchTopicsResult, TopicDetailResult, TopicPostsPageResult
from linuxdo_cli.tui.app import LinuxDoApp
from linuxdo_cli.tui.screens.browse import BrowseScreen
from linuxdo_cli.tui.screens.category_select import CategorySelectScreen
from linuxdo_cli.tui.screens.detail import DetailScreen
from linuxdo_cli.tui.screens.help import HelpScreen
from linuxdo_cli.tui.widgets.category_tabs import CategoryTabs
from linuxdo_cli.tui.widgets.posts_container import PostsContainer
from linuxdo_cli.tui.widgets.status_bar import StatusBar
from linuxdo_cli.tui.widgets.topic_list import TopicList
from linuxdo_cli.tui.widgets.topic_item import TopicItem
from tests.conftest import FAKE_DETAIL, make_topic


async def _wait_for(pilot, condition, timeout=5.0):
    """Poll until condition() is True or raise TimeoutError."""
    deadline = asyncio.get_running_loop().time() + timeout
    while not condition():
        if asyncio.get_running_loop().time() > deadline:
            raise TimeoutError("Condition not met within timeout")
        await pilot.pause(0.1)


async def _wait_browse_ready(pilot):
    """Wait until BrowseScreen is active and topics are loaded."""
    await _wait_for(pilot, lambda: isinstance(pilot.app.screen, BrowseScreen))
    topic_list = pilot.app.screen.query_one(TopicList)
    await _wait_for(pilot, lambda: len(topic_list._nodes) > 0)
    await _wait_for(pilot, lambda: topic_list.index is not None)
    return topic_list


# ── T1: Browse screen loads topics ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_browse_screen_loads_topics(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        topic_list = await _wait_browse_ready(pilot)
        assert len(topic_list._nodes) > 0


# ── T2: Enter opens DetailScreen exactly once ────────────────────────────────

@pytest.mark.asyncio
async def test_enter_opens_detail_once(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        await pilot.press("enter")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        assert isinstance(pilot.app.screen, DetailScreen)
        # stack: _default_css_screen + BrowseScreen + DetailScreen = 3, not 4
        assert len(pilot.app.screen_stack) == 3


# ── T3: Click topic opens DetailScreen exactly once ─────────────────────────

@pytest.mark.asyncio
async def test_click_topic_opens_detail_once(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        first_item = pilot.app.screen.query(TopicItem).first()
        await pilot.click(first_item)
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        assert isinstance(pilot.app.screen, DetailScreen)
        assert len(pilot.app.screen_stack) == 3


# ── T4: DetailScreen shows the correct title ────────────────────────────────

@pytest.mark.asyncio
async def test_detail_screen_shows_title(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        await pilot.press("enter")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        title_label = pilot.app.screen.query_one("#detail-title")
        assert "Hello World" in str(title_label.content)


# ── T5: Esc returns from detail to browse ───────────────────────────────────

@pytest.mark.asyncio
async def test_esc_returns_from_detail(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        await pilot.press("enter")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        await pilot.press("escape")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, BrowseScreen))
        assert isinstance(pilot.app.screen, BrowseScreen)


# ── T6: Back button returns from detail to browse ────────────────────────────

@pytest.mark.asyncio
async def test_back_button_returns_from_detail(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        await pilot.press("enter")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        back_btn = pilot.app.screen.query_one("#detail-back-btn")
        await pilot.click(back_btn)
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, BrowseScreen))
        assert isinstance(pilot.app.screen, BrowseScreen)


# ── T7: Tab key cycles category forward ─────────────────────────────────────

@pytest.mark.asyncio
async def test_tab_key_switches_category(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        tabs = pilot.app.screen.query_one(CategoryTabs)
        assert tabs.active_category == "latest"

        await pilot.press("tab")
        await _wait_for(pilot, lambda: tabs.active_category == "hot")
        assert tabs.active_category == "hot"


# ── T8: Mouse click on hot tab switches category ────────────────────────────

@pytest.mark.asyncio
async def test_click_tab_switches_category(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        tabs = pilot.app.screen.query_one(CategoryTabs)
        assert tabs.active_category == "latest"

        hot_tab = pilot.app.screen.query_one("#tab-hot")
        await pilot.click(hot_tab)
        await _wait_for(pilot, lambda: tabs.active_category == "hot")
        assert tabs.active_category == "hot"


# ── T9: Help screen opens and closes ────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_screen_open_close(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, BrowseScreen))

        await pilot.press("question_mark")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, HelpScreen))
        assert isinstance(pilot.app.screen, HelpScreen)

        await pilot.press("escape")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, BrowseScreen))
        assert isinstance(pilot.app.screen, BrowseScreen)


# ── T10: Refresh re-triggers fetch ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_refetches(mock_client):
    from linuxdo_cli.services.topics import TopicService

    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)

        call_count_before = TopicService.fetch_topics.call_count
        await pilot.press("r")
        await pilot.pause(1.0)
        assert TopicService.fetch_topics.call_count > call_count_before


# ── T11: Infinite scroll loads next page at the bottom, then stops ──────────

@pytest.mark.asyncio
async def test_infinite_scroll_stops_after_last_page(mock_client):
    from linuxdo_cli.services.topics import TopicService

    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        topic_list = await _wait_browse_ready(pilot)
        status_bar = pilot.app.screen.query_one(StatusBar)

        call_count_before = TopicService.fetch_topics.call_count
        await pilot.press("down")
        await _wait_for(pilot, lambda: "已加载全部话题" in status_bar.status_message)

        assert TopicService.fetch_topics.call_count == call_count_before + 1
        assert len(topic_list._nodes) == 2

        await pilot.press("n")
        await pilot.pause(0.5)
        assert TopicService.fetch_topics.call_count == call_count_before + 1


# ── T12: Scrolling viewport to bottom also triggers infinite scroll ─────────

@pytest.mark.asyncio
async def test_scroll_viewport_to_bottom_triggers_infinite_scroll():
    fake_config = Config(
        client_id="test",
        client_secret="test",
        base_url="https://linux.do",
        connect_url="https://connect.linux.do",
    )
    many_topics = [make_topic(i, f"Topic {i}", f"topic-{i}") for i in range(1, 31)]

    async def fetch_topics(query):
        topics = many_topics if query.page == 0 else []
        return FetchTopicsResult(
            topics=topics,
            page=query.page,
            category_key=query.category_key,
            category_name=query.category_name,
            has_more=bool(topics),
        )

    detail_result = TopicDetailResult(
        detail=FAKE_DETAIL,
        posts=FAKE_DETAIL.post_stream["posts"],
        post_count=1,
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
                side_effect=fetch_topics,
            ) as fetch_mock:
                with patch(
                    "linuxdo_cli.services.detail.TopicDetailService.load_detail",
                    new_callable=AsyncMock,
                    return_value=detail_result,
                ):
                    async with LinuxDoApp().run_test(size=(120, 12)) as pilot:
                        topic_list = await _wait_browse_ready(pilot)
                        status_bar = pilot.app.screen.query_one(StatusBar)

                        call_count_before = fetch_mock.call_count
                        topic_list.scroll_end(animate=False)
                        await _wait_for(
                            pilot,
                            lambda: "已加载全部话题" in status_bar.status_message,
                        )

                        assert fetch_mock.call_count == call_count_before + 1
                        assert len(topic_list._nodes) == len(many_topics)


# ── T13: Detail viewport reaching bottom triggers more replies ──────────────

@pytest.mark.asyncio
async def test_detail_scroll_bottom_triggers_more_replies():
    fake_config = Config(
        client_id="test",
        client_secret="test",
        base_url="https://linux.do",
        connect_url="https://connect.linux.do",
    )

    long_html = "<p>" + ("Hello world " * 120) + "</p>"
    initial_posts = [
        {
            "id": 1,
            "username": "user1",
            "created_at": "2024-01-01T00:00:00Z",
            "cooked": long_html,
        }
    ]
    appended_posts = [
        {
            "id": 2,
            "username": "user2",
            "created_at": "2024-01-01T00:10:00Z",
            "cooked": long_html,
        }
    ]

    initial_result = TopicDetailResult(
        detail=FAKE_DETAIL.model_copy(
            update={
                "posts_count": 2,
                "post_stream": {
                    "stream": [1, 2],
                    "posts": initial_posts,
                },
            }
        ),
        posts=initial_posts,
        post_count=1,
        total_post_count=2,
        loaded_post_ids=[1],
        remaining_post_ids=[2],
        has_more=True,
    )
    appended_result = TopicPostsPageResult(
        posts=appended_posts,
        loaded_post_ids=[1, 2],
        remaining_post_ids=[],
        has_more=False,
    )

    async def fetch_topics(query):
        return FetchTopicsResult(
            topics=[make_topic(1, "Hello World", "hello-world")],
            page=query.page,
            category_key=query.category_key,
            category_name=query.category_name,
            has_more=False,
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
                side_effect=fetch_topics,
            ):
                with patch(
                    "linuxdo_cli.services.detail.TopicDetailService.load_detail",
                    new_callable=AsyncMock,
                    return_value=initial_result,
                ):
                    with patch(
                        "linuxdo_cli.services.detail.TopicDetailService.load_more_posts",
                        new_callable=AsyncMock,
                        return_value=appended_result,
                    ) as append_mock:
                        async with LinuxDoApp().run_test(size=(120, 12)) as pilot:
                            await _wait_browse_ready(pilot)
                            await pilot.press("enter")
                            await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

                            detail_screen = pilot.app.screen
                            status_bar = detail_screen.query_one(StatusBar)
                            container = detail_screen.query_one(PostsContainer)
                            await _wait_for(pilot, lambda: container.max_scroll_y > 0)

                            call_count_before = append_mock.call_count
                            container.scroll_end(animate=False)
                            await _wait_for(
                                pilot,
                                lambda: "已追加 1 个回复" in status_bar.status_message,
                            )

                            assert append_mock.call_count == call_count_before + 1


# ── T14: Resize applies responsive viewport classes and compact tab labels ──

@pytest.mark.asyncio
async def test_resize_applies_responsive_classes(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)
        tabs = pilot.app.screen.query_one(CategoryTabs)
        latest_tab = tabs.query_one("#tab-latest")

        assert pilot.app.has_class("-viewport-wide")
        assert "● 最新" in str(latest_tab.content)

        await pilot.resize_terminal(68, 40)
        await _wait_for(pilot, lambda: pilot.app.has_class("-viewport-narrow"))

        latest_tab = tabs.query_one("#tab-latest")
        assert "最新" == str(latest_tab.content)
        assert not pilot.app.has_class("-viewport-wide")


# ── T15: Detail header compacts when viewport becomes narrow ────────────────

@pytest.mark.asyncio
async def test_detail_header_compacts_on_narrow_resize(mock_client):
    async with LinuxDoApp().run_test(size=(120, 40)) as pilot:
        await _wait_browse_ready(pilot)
        await pilot.press("enter")
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, DetailScreen))

        back_button = pilot.app.screen.query_one("#detail-back-btn")
        assert str(back_button.label) == "← 返回"

        await pilot.resize_terminal(68, 30)
        await _wait_for(pilot, lambda: pilot.app.has_class("-viewport-narrow"))
        await _wait_for(pilot, lambda: str(back_button.label) == "←")

        assert str(back_button.label) == "←"


# ── T16: Category modal width shrinks on narrow viewport ────────────────────

@pytest.mark.asyncio
async def test_category_modal_shrinks_on_narrow_viewport(mock_client):
    async with LinuxDoApp().run_test(size=(60, 24)) as pilot:
        await _wait_browse_ready(pilot)
        await pilot.click(pilot.app.screen.query_one("#tab-category"))
        await _wait_for(pilot, lambda: isinstance(pilot.app.screen, CategorySelectScreen))

        panel = pilot.app.screen.query_one("#cat-card-panel")
        assert panel.size.width <= 56
