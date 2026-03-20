from unittest.mock import AsyncMock, patch

import pytest

from linuxdo_cli.client import LinuxDoClient, RateLimitError, RequestError
from linuxdo_cli.config import Config


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeAsyncSession:
    def __init__(self, responses) -> None:
        self._responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return self._responses.pop(0)


def make_client(access_token: str | None = "token") -> LinuxDoClient:
    return LinuxDoClient(
        Config(
            client_id="test-id",
            client_secret="test-secret",
            access_token=access_token,
            base_url="https://linux.do",
            connect_url="https://connect.linux.do",
        )
    )


@pytest.mark.asyncio
async def test_get_hot_topics_parses_topics():
    from tests.conftest import FAKE_TOPICS, FAKE_TOP_JSON

    client = make_client()

    with patch.object(client, "_get", new=AsyncMock(return_value=FAKE_TOP_JSON)):
        topics = await client.get_hot_topics(page=1)

    assert [topic.id for topic in topics] == [topic.id for topic in FAKE_TOPICS]


@pytest.mark.asyncio
async def test_get_retries_on_429_then_succeeds():
    from tests.conftest import FAKE_TOP_JSON

    responses = [
        FakeResponse(429, payload={}),
        FakeResponse(200, payload=FAKE_TOP_JSON),
    ]
    client = make_client()

    with patch("linuxdo_cli.client.AsyncSession", side_effect=lambda *args, **kwargs: FakeAsyncSession(responses)):
        with patch("linuxdo_cli.client.asyncio.sleep", new=AsyncMock()):
            with patch("linuxdo_cli.client.random.uniform", return_value=0):
                topics = await client.get_latest_topics()

    assert len(topics) == 2


@pytest.mark.asyncio
async def test_get_raises_request_error_on_server_failure():
    client = make_client()
    responses = [FakeResponse(500, payload={"message": "boom"})]

    with patch("linuxdo_cli.client.AsyncSession", side_effect=lambda *args, **kwargs: FakeAsyncSession(responses)):
        with patch("linuxdo_cli.client.asyncio.sleep", new=AsyncMock()):
            with patch("linuxdo_cli.client.random.uniform", return_value=0):
                with pytest.raises(RequestError, match="请求失败 \\(500\\): boom"):
                    await client.get_latest_topics()


@pytest.mark.asyncio
async def test_get_raises_rate_limit_error_after_exhausting_retries():
    responses = [
        FakeResponse(429, payload={}),
        FakeResponse(429, payload={}),
        FakeResponse(429, payload={}),
        FakeResponse(429, payload={}),
    ]
    client = make_client()

    with patch("linuxdo_cli.client.AsyncSession", side_effect=lambda *args, **kwargs: FakeAsyncSession(responses)):
        with patch("linuxdo_cli.client.asyncio.sleep", new=AsyncMock()):
            with patch("linuxdo_cli.client.random.uniform", return_value=0):
                with pytest.raises(RateLimitError):
                    await client.get_latest_topics()
