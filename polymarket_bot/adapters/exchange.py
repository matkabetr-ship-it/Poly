from __future__ import annotations

import asyncio
from typing import Protocol
from datetime import datetime, timezone
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from polymarket_bot.core.models import Market, OrderIntent, Fill, Side


class ExchangeClient(Protocol):
    async def list_markets(self) -> list[Market]: ...
    async def stream_markets(self): ...
    async def submit_order(self, order: OrderIntent) -> str: ...
    async def cancel_order(self, order_id: str) -> None: ...


class AbstractHTTPExchange:
    """Adapter skeleton. Replace endpoint paths with official exchange specs only."""

    def __init__(self, base_url: str, ws_url: str, timeout_s: int = 10):
        self.base_url = base_url
        self.ws_url = ws_url
        self.timeout = aiohttp.ClientTimeout(total=timeout_s)
        self.session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    async def list_markets(self) -> list[Market]:
        assert self.session
        # Placeholder: do not hallucinate endpoints.
        return []

    async def stream_markets(self):
        """WebSocket stream with reconnect/backoff. Yields normalized market events."""
        backoff = 1
        while True:
            try:
                await asyncio.sleep(1)
                yield []
                backoff = 1
            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def submit_order(self, order: OrderIntent) -> str:
        assert self.session
        return f"sim-{order.client_order_id}"

    async def cancel_order(self, order_id: str) -> None:
        return None
