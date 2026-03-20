import secrets
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlparse

from ..config_repository import ConfigRepository
from ..connect_client import ConnectClient
from ..models import UserProfile
from ..settings import Config


class AuthServiceError(Exception):
    """Raised when the OAuth login flow cannot be completed."""


class AuthCancelledError(AuthServiceError):
    """Raised when the user aborts the OAuth callback wait."""


class AuthCallbackError(AuthServiceError):
    """Raised when no authorization code is received."""


@dataclass(slots=True)
class AuthLoginSession:
    auth_url: str
    redirect_uri: str


@dataclass(slots=True)
class AuthLoginResult:
    config: Config
    user: UserProfile


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理 Linux Do Connect OAuth2 回调。"""

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h1>授权成功！</h1><p>授权码已成功传输到 CLI，请返回终端。</p>"
                "<script>setTimeout(window.close, 3000);</script>".encode("utf-8")
            )
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(
                "<h1>授权失败</h1><p>未能在回调中找到授权码。</p>".encode("utf-8")
            )

    def log_message(self, format, *args):
        return


class AuthService:
    def __init__(
        self,
        connect_client: ConnectClient,
        config_repository: ConfigRepository,
        redirect_uri: str = "http://localhost:8080",
        browser_opener: Callable[[str], bool] = webbrowser.open,
        server_class: type[HTTPServer] = HTTPServer,
    ) -> None:
        self._connect_client = connect_client
        self._config_repository = config_repository
        self.redirect_uri = redirect_uri
        self._browser_opener = browser_opener
        self._server_class = server_class

    def prepare_login(self, config: Config) -> AuthLoginSession:
        if not config.client_id or not config.client_secret:
            raise AuthServiceError("缺少 OAuth 客户端凭据，请检查配置")

        state = secrets.token_hex(16)
        auth_url = self._connect_client.build_authorize_url(
            config,
            self.redirect_uri,
            state,
        )
        return AuthLoginSession(auth_url=auth_url, redirect_uri=self.redirect_uri)

    def login(
        self,
        config: Config,
        session: AuthLoginSession | None = None,
    ) -> AuthLoginResult:
        active_session = session or self.prepare_login(config)
        code = self._receive_auth_code(active_session.auth_url)

        token = self._connect_client.exchange_code(config, code, active_session.redirect_uri)
        updated_config = config.model_copy(
            update={
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
            }
        )
        user = self._connect_client.get_current_user(updated_config)
        self._config_repository.save(updated_config)
        return AuthLoginResult(config=updated_config, user=user)

    def _receive_auth_code(self, auth_url: str) -> str:
        server = self._server_class(("localhost", 8080), OAuthCallbackHandler)
        server.auth_code = None
        self._browser_opener(auth_url)

        try:
            server.handle_request()
        except KeyboardInterrupt as exc:
            raise AuthCancelledError("已取消登录。") from exc

        code = getattr(server, "auth_code", None)
        if not code:
            raise AuthCallbackError("未能获取授权码。")
        return code
