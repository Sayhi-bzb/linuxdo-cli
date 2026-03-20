from unittest.mock import Mock

import pytest

from linuxdo_cli.config import Config
from linuxdo_cli.connect_client import TokenPayload
from linuxdo_cli.models import UserProfile
from linuxdo_cli.services import AuthCallbackError, AuthLoginSession, AuthService


def make_config() -> Config:
    return Config(
        client_id="test-id",
        client_secret="test-secret",
        connect_url="https://connect.linux.do",
    )


def make_user() -> UserProfile:
    return UserProfile(
        id=7,
        username="tester",
        name="Test User",
        trust_level=2,
        active=True,
        silenced=False,
    )


def test_prepare_login_requires_credentials():
    service = AuthService(Mock(), Mock())

    with pytest.raises(Exception, match="缺少 OAuth 客户端凭据"):
        service.prepare_login(Config())


def test_login_exchanges_code_fetches_user_and_saves_config():
    connect_client = Mock()
    connect_client.build_authorize_url.return_value = "https://connect.linux.do/oauth2/authorize?state=1"
    connect_client.exchange_code.return_value = TokenPayload(
        access_token="new-token",
        refresh_token="refresh-token",
    )
    connect_client.get_current_user.return_value = make_user()
    repository = Mock()

    service = AuthService(connect_client, repository)
    service._receive_auth_code = Mock(return_value="code-1")
    config = make_config()
    session = AuthLoginSession(
        auth_url="https://connect.linux.do/oauth2/authorize?state=1",
        redirect_uri="http://localhost:8080",
    )

    result = service.login(config, session=session)

    service._receive_auth_code.assert_called_once_with(session.auth_url)
    connect_client.exchange_code.assert_called_once_with(config, "code-1", session.redirect_uri)
    saved_config = repository.save.call_args.args[0]
    assert saved_config.access_token == "new-token"
    assert saved_config.refresh_token == "refresh-token"
    assert result.user.username == "tester"
    assert result.config.access_token == "new-token"


def test_login_raises_when_callback_has_no_code():
    connect_client = Mock()
    repository = Mock()
    service = AuthService(connect_client, repository)
    service._receive_auth_code = Mock(side_effect=AuthCallbackError("未能获取授权码。"))

    with pytest.raises(AuthCallbackError, match="未能获取授权码"):
        service.login(
            make_config(),
            session=AuthLoginSession(
                auth_url="https://connect.linux.do/oauth2/authorize?state=1",
                redirect_uri="http://localhost:8080",
            ),
        )

    repository.save.assert_not_called()
