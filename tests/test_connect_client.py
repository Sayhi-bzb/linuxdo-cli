from unittest.mock import patch

import pytest

from linuxdo_cli.config import Config
from linuxdo_cli.connect_client import (
    ConnectAuthenticationError,
    ConnectClient,
    ConnectRequestError,
)


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeHttpxClient:
    def __init__(self, responses, recorder) -> None:
        self._responses = responses
        self._recorder = recorder

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, **kwargs):
        self._recorder.append((method, url, kwargs))
        return self._responses.pop(0)


def make_config(access_token: str | None = "token") -> Config:
    return Config(
        client_id="test-id",
        client_secret="test-secret",
        access_token=access_token,
        connect_url="https://connect.linux.do",
    )


def test_build_authorize_url_contains_expected_params():
    url = ConnectClient.build_authorize_url(
        make_config(),
        redirect_uri="http://localhost:8080",
        state="abc123",
    )

    assert "oauth2/authorize" in url
    assert "client_id=test-id" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080" in url
    assert "state=abc123" in url
    assert "scope=user" in url


def test_exchange_code_returns_token_payload():
    recorder = []
    responses = [
        FakeResponse(200, payload={"access_token": "new-token", "refresh_token": "refresh"}),
    ]

    with patch(
        "linuxdo_cli.connect_client.httpx.Client",
        side_effect=lambda *args, **kwargs: FakeHttpxClient(responses, recorder),
    ):
        token = ConnectClient().exchange_code(make_config(), "code-1", "http://localhost:8080")

    assert token.access_token == "new-token"
    assert token.refresh_token == "refresh"
    method, url, kwargs = recorder[0]
    assert method == "POST"
    assert url.endswith("/oauth2/token")
    assert kwargs["data"]["code"] == "code-1"


def test_get_current_user_returns_profile():
    recorder = []
    responses = [
        FakeResponse(
            200,
            payload={
                "id": 7,
                "username": "tester",
                "name": "Test User",
                "trust_level": 2,
                "active": True,
                "silenced": False,
            },
        )
    ]

    with patch(
        "linuxdo_cli.connect_client.httpx.Client",
        side_effect=lambda *args, **kwargs: FakeHttpxClient(responses, recorder),
    ):
        user = ConnectClient().get_current_user(make_config())

    assert user.username == "tester"
    assert recorder[0][0] == "GET"
    assert recorder[0][2]["headers"]["Authorization"] == "Bearer token"


def test_get_current_user_requires_token():
    with pytest.raises(ConnectAuthenticationError, match="未登录"):
        ConnectClient().get_current_user(make_config(access_token=None))


def test_get_current_user_raises_authentication_error_on_401():
    recorder = []
    responses = [FakeResponse(401, payload={"message": "unauthorized"})]

    with patch(
        "linuxdo_cli.connect_client.httpx.Client",
        side_effect=lambda *args, **kwargs: FakeHttpxClient(responses, recorder),
    ):
        with pytest.raises(ConnectAuthenticationError):
            ConnectClient().get_current_user(make_config())


def test_exchange_code_raises_request_error_on_server_failure():
    recorder = []
    responses = [FakeResponse(500, payload={"message": "boom"})]

    with patch(
        "linuxdo_cli.connect_client.httpx.Client",
        side_effect=lambda *args, **kwargs: FakeHttpxClient(responses, recorder),
    ):
        with pytest.raises(ConnectRequestError, match="请求失败 \\(500\\): boom"):
            ConnectClient().exchange_code(make_config(), "code-1", "http://localhost:8080")
