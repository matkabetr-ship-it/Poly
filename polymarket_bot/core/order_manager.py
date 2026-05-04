from __future__ import annotations

import time
from polymarket_bot.core.models import OrderIntent


class OrderManager:
    def __init__(self, cfg, exchange):
        self.cfg = cfg
        self.exchange = exchange
        self.open_orders: dict[str, tuple[str, float, str]] = {}
        self.idempotency_keys: set[str] = set()

    async def submit(self, intent: OrderIntent, mark_price: float, category: str) -> str | None:
        if intent.client_order_id in self.idempotency_keys:
            return None
        slippage = abs(intent.price - mark_price) / max(mark_price, 1e-9)
        if slippage > self.cfg.slippage_tolerance_pct:
            return None
        self.idempotency_keys.add(intent.client_order_id)
        oid = await self.exchange.submit_order(intent)
        self.open_orders[oid] = (intent.market_id, time.time(), category)
        return oid

    async def cancel_stale(self) -> None:
        now = time.time()
        stale = [oid for oid, (_, ts, _) in self.open_orders.items() if now - ts > self.cfg.order_ttl_seconds]
        for oid in stale:
            await self.exchange.cancel_order(oid)
            self.open_orders.pop(oid, None)
