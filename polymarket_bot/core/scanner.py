from __future__ import annotations

from datetime import datetime, timezone
from polymarket_bot.core.models import Market


class MarketScanner:
    def __init__(self, scanner_config, exchange):
        self.cfg = scanner_config
        self.exchange = exchange

    async def fetch_filtered_markets(self) -> list[Market]:
        markets = await self.exchange.list_markets()
        now = datetime.now(timezone.utc)
        out = []
        for m in markets:
            days_left = (m.expiry - now).days
            if m.volume < self.cfg.min_volume:
                continue
            if m.liquidity < self.cfg.min_liquidity:
                continue
            if days_left > self.cfg.max_days_to_expiry:
                continue
            if m.category not in self.cfg.categories:
                continue
            out.append(m)
        return out
