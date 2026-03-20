from .app import LinuxDoApp


def run_tui() -> None:
    """启动 TUI 应用"""
    app = LinuxDoApp()
    app.run()


__all__ = ["run_tui", "LinuxDoApp"]
