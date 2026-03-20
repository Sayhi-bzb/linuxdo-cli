import json
from pathlib import Path
from unittest.mock import mock_open, patch

from linuxdo_cli.config import Config, ConfigRepository


def test_repository_load_returns_defaults_when_file_missing():
    repo = ConfigRepository(Path("config.json"))

    with patch.object(Path, "exists", return_value=False):
        config = repo.load()

    assert isinstance(config, Config)
    assert config.base_url == "https://linux.do"


def test_repository_load_falls_back_when_file_is_invalid():
    repo = ConfigRepository(Path("config.json"))

    with patch.object(Path, "exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="{invalid-json")):
            config = repo.load()

    assert config.base_url == "https://linux.do"


def test_repository_save_and_load_round_trip():
    config_path = Path("config.json")
    repo = ConfigRepository(config_path)
    config = Config(
        client_id="test-id",
        client_secret="test-secret",
        access_token="token",
        theme="linuxdo",
        layout_density="compact",
    )

    read_buffer = {}

    def fake_write(data):
        read_buffer["data"] = data
        return len(data)

    mocked_write = mock_open()
    mocked_write.return_value.write.side_effect = fake_write

    with patch.object(Path, "mkdir") as mkdir:
        with patch("builtins.open", mocked_write):
            repo.save(config)

    with patch.object(Path, "exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=read_buffer["data"])):
            reloaded = repo.load()

    raw = json.loads(read_buffer["data"])
    mkdir.assert_called_once()
    assert raw["access_token"] == "token"
    assert reloaded.theme == "linuxdo"
    assert reloaded.layout_density == "compact"
