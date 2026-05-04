from __future__ import annotations

import aiohttp


class Alerting:
    def __init__(self, cfg):
        self.cfg = cfg

    async def send(self, message: str) -> None:
        if self.cfg.discord_webhook_url:
            async with aiohttp.ClientSession() as s:
                await s.post(self.cfg.discord_webhook_url, json={"content": message})
