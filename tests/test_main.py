from unittest.mock import Mock, patch

from typer.testing import CliRunner

from linuxdo_cli.config import Config
from linuxdo_cli.main import app
from linuxdo_cli.models import UserProfile


runner = CliRunner()


def test_me_requires_login():
    fake_config = Config(
        client_id="test-id",
        client_secret="test-secret",
        access_token=None,
    )

    with patch("linuxdo_cli.main.ConfigRepository.load", return_value=fake_config):
        result = runner.invoke(app, ["me"])

    assert result.exit_code == 1
    assert "未登录" in result.stdout


def test_me_renders_user_info():
    fake_config = Config(
        client_id="test-id",
        client_secret="test-secret",
        access_token="token",
        base_url="https://linux.do",
        connect_url="https://connect.linux.do",
    )
    fake_user = UserProfile(
        id=7,
        username="tester",
        name="Test User",
        trust_level=2,
        active=True,
        silenced=False,
    )

    with patch("linuxdo_cli.main.ConfigRepository.load", return_value=fake_config):
        with patch(
            "linuxdo_cli.main.ConnectClient.get_current_user",
            return_value=fake_user,
        ):
            result = runner.invoke(app, ["me"])

    assert result.exit_code == 0
    assert "tester" in result.stdout
    assert "TL2" in result.stdout


def test_login_loads_config_and_runs_auth_flow():
    fake_config = Config(
        client_id="test-id",
        client_secret="test-secret",
    )
    fake_repo = Mock()
    fake_repo.load.return_value = fake_config

    with patch("linuxdo_cli.main.ConfigRepository", return_value=fake_repo):
        with patch("linuxdo_cli.main.do_login") as do_login:
            result = runner.invoke(app, ["login"])

    assert result.exit_code == 0
    do_login.assert_called_once_with(fake_config, repository=fake_repo)
