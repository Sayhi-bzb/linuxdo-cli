from curl_cffi.requests import AsyncSession
import asyncio
import random
from typing import List, Optional
from .models import Topic, LatestTopicsResponse, TopicDetail, Category
from .settings import Config


class LinuxDoClientError(Exception):
    """Base error for linuxdo client failures."""


class AuthenticationError(LinuxDoClientError):
    """Raised when the current token is missing or expired."""


class RateLimitError(LinuxDoClientError):
    """Raised when the API rate limit persists after retries."""


class RequestError(LinuxDoClientError):
    """Raised for other HTTP and response parsing failures."""


class LinuxDoClient:
    def __init__(self, config: Config):
        self.base_url = config.base_url.rstrip("/")
        self.connect_url = config.connect_url.rstrip("/")
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="133", "Not(A:Brand";v="24", "Google Chrome";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        if config.access_token:
            self.headers["Authorization"] = f"Bearer {config.access_token}"

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

    async def _get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        _retry: int = 0,
        base_url: Optional[str] = None,
    ) -> dict:
        await asyncio.sleep(random.uniform(0.5, 1.5))
        root_url = base_url or self.base_url

        async with AsyncSession(impersonate="chrome133a") as s:
            response = await s.get(
                f"{root_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 429:
                if _retry >= 3:
                    raise RateLimitError(f"触发限流 (429)，已重试 {_retry} 次，请稍后再试")
                print(f"[!] 触发限流 (429)，正在缓冲... (第 {_retry + 1} 次重试)")
                await asyncio.sleep(5 * (_retry + 1))
                return await self._get(endpoint, params, _retry + 1, base_url=root_url)

            if response.status_code == 401:
                raise AuthenticationError("登录已过期，请重新执行 linuxdo login")
            if response.status_code >= 400:
                raise RequestError(self._format_http_error(response))

            try:
                return response.json()
            except Exception as exc:
                raise RequestError("响应解析失败") from exc

    async def get_latest_topics(self, page: int = 0) -> List[Topic]:
        params = {"page": page} if page > 0 else None
        data = await self._get("/latest.json", params=params)
        return LatestTopicsResponse(**data).topic_list.topics

    async def get_hot_topics(self, page: int = 0) -> List[Topic]:
        params = {"page": page} if page > 0 else None
        data = await self._get("/top.json", params=params)
        return LatestTopicsResponse(**data).topic_list.topics

    async def get_topic_detail(self, topic_id: int) -> TopicDetail:
        data = await self._get(f"/t/{topic_id}.json")
        return TopicDetail(**data)

    async def get_topic_posts(self, topic_id: int, post_ids: list[int]) -> list[dict]:
        if not post_ids:
            return []

        data = await self._get(
            f"/t/{topic_id}/posts.json",
            params={"post_ids[]": post_ids},
        )
        post_stream = data.get("post_stream", {})
        if isinstance(post_stream, dict):
            posts = post_stream.get("posts", [])
            if isinstance(posts, list):
                return posts

        posts = data.get("posts", [])
        return posts if isinstance(posts, list) else []

    async def get_categories(self) -> List[Category]:
        data = await self._get("/categories.json")
        cats = data.get("category_list", {}).get("categories", [])
        return [Category(**c) for c in cats]

    async def get_category_topics(self, slug: str, cat_id: int, page: int = 0) -> List[Topic]:
        params = {"page": page} if page > 0 else None
        data = await self._get(f"/c/{slug}/{cat_id}.json", params=params)
        return LatestTopicsResponse(**data).topic_list.topics
