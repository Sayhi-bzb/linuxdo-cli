import linuxdo_cli.config as config_module
from linuxdo_cli.client import LinuxDoClient
from linuxdo_cli.main import show_me


def test_config_module_no_longer_exports_compat_wrappers():
    assert not hasattr(config_module, "load_config")
    assert not hasattr(config_module, "save_config")


def test_linuxdo_client_no_longer_owns_current_user_api():
    assert not hasattr(LinuxDoClient, "get_current_user")


def test_main_me_uses_connect_client():
    names = set(show_me.__code__.co_names)
    assert "ConnectClient" in names
    assert "LinuxDoClient" not in names
