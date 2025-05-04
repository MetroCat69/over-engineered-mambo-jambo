import os
import asyncio
from typing import Optional
import httpx
from predicate import Predicate

UPDATE_INTERVAL = 120


class RemotePredicateResource:
    def __init__(self, url: str, client: Optional[httpx.AsyncClient] = None):
        self.url = f"{url}/api/v1/predicate"
        self._predicate: Optional[Predicate] = None
        self._etag: Optional[str] = None
        self._client = client or httpx.AsyncClient()
        self._task: Optional[asyncio.Task] = None

    @classmethod
    async def from_env(cls) -> "RemotePredicateResource":
        url = os.getenv("PREDICATE_SERVICE_URL")
        if not url:
            raise ValueError("PREDICATE_SERVICE_URL not set")
        resource = cls(url)
        await resource._start()
        return resource

    async def _start(self):
        self._task = asyncio.create_task(self._update_loop())

    @property
    def predicate(self) -> Predicate:
        if self._predicate is None:
            raise ValueError("Predicate not loaded yet")
        return self._predicate

    async def _fetch_predicate(self):
        headers = {"If-None-Match": self._etag} if self._etag else {}
        try:
            response = await self._client.get(self.url, headers=headers)
            if response.status_code == 200:
                self._predicate = Predicate.from_json(response.text)
                self._etag = response.headers.get("etag")
        except Exception:
            pass  # silently retry later

    async def _update_loop(self):
        while True:
            await self._fetch_predicate()
            await asyncio.sleep(UPDATE_INTERVAL)

    async def close(self):
        if self._task:
            self._task.cancel()
        await self._client.aclose()
