from curl_cffi.requests import AsyncSession
import asyncio
import random
from typing import List, Optional
from .models import Topic, LatestTopicsResponse, TopicDetail
from .config import Config

class LinuxDoClient:
    def __init__(self, config: Config):
        self.base_url = config.base_url
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

    async def _get(self, endpoint: str, params: Optional[dict] = None, _retry: int = 0) -> dict:
        await asyncio.sleep(random.uniform(0.5, 1.5))

        async with AsyncSession(impersonate="chrome133a") as s:
            response = await s.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 429:
                if _retry >= 3:
                    raise Exception(f"触发限流 (429)，已重试 {_retry} 次，请稍后再试")
                print(f"[!] 触发限流 (429)，正在缓冲... (第 {_retry + 1} 次重试)")
                await asyncio.sleep(5 * (_retry + 1))
                return await self._get(endpoint, params, _retry + 1)

            response.raise_for_status()
            return response.json()

    async def get_latest_topics(self, page: int = 0) -> List[Topic]:
        params = {"page": page} if page > 0 else None
        data = await self._get("/latest.json", params=params)
        return LatestTopicsResponse(**data).topic_list.topics

    async def get_topic_detail(self, topic_id: int) -> TopicDetail:
        data = await self._get(f"/t/{topic_id}.json")
        return TopicDetail(**data)
