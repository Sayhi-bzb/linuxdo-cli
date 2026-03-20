from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from .models import UserProfile
from .settings import Config


class ConnectClientError(Exception):
    """Base error for Linux Do Connect failures."""


class ConnectAuthenticationError(ConnectClientError):
    """Raised when the current Connect token is missing or expired."""


class ConnectRequestError(ConnectClientError):
    """Raised for other Connect HTTP and response parsing failures."""


@dataclass(slots=True)
class TokenPayload:
    access_token: str
    refresh_token: str | None = None


class ConnectClient:
    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    @staticmethod
    def build_authorize_url(config: Config, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "user",
            "state": state,
        }
        return f"{config.connect_url.rstrip('/')}/oauth2/authorize?{urlencode(params)}"

    @staticmethod
    def _format_http_error(response) -> str:
        detail = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = payload.get("message") or payload.get("error") or ""
                if not detail and isinstance(payload.get("errors"), list):
                    detail = "; ".join(str(item) for item in payload["errors"])
        except Exception:
            pass

        if not detail:
            detail = (getattr(response, "text", "") or "").strip()

        return f"请求失败 ({response.status_code})" + (f": {detail}" if detail else "")

    def _request(self, method: str, config: Config, endpoint: str, **kwargs) -> dict:
        base_url = config.connect_url.rstrip("/")
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, f"{base_url}{endpoint}", **kwargs)

        if response.status_code == 401:
            raise ConnectAuthenticationError("登录已过期，请重新执行 linuxdo login")
        if response.status_code >= 400:
            raise ConnectRequestError(self._format_http_error(response))

        try:
            return response.json()
        except Exception as exc:
            raise ConnectRequestError("响应解析失败") from exc

    def exchange_code(self, config: Config, code: str, redirect_uri: str) -> TokenPayload:
        payload = self._request(
            "POST",
            config,
            "/oauth2/token",
            data={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )

        access_token = payload.get("access_token", "")
        if not access_token:
            raise ConnectRequestError("响应缺少 access_token")

        return TokenPayload(
            access_token=access_token,
            refresh_token=payload.get("refresh_token"),
        )

    def get_current_user(self, config: Config) -> UserProfile:
        if not config.access_token:
            raise ConnectAuthenticationError("未登录，请先执行 linuxdo login")

        payload = self._request(
            "GET",
            config,
            "/api/user",
            headers={"Authorization": f"Bearer {config.access_token}"},
        )
        return UserProfile(**payload)
