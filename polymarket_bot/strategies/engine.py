from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Protocol
from polymarket_bot.core.models import Market, Signal, Side


class Strategy(Protocol):
    async def generate(self, markets: list[Market]) -> list[Signal]: ...


@dataclass(slots=True)
class StrategyContext:
    inventory_by_market: dict[str, float]


class MeanReversionStrategy:
    """Exploit overreaction at extreme implied probabilities."""

    async def generate(self, markets: list[Market]) -> list[Signal]:
        signals: list[Signal] = []
        for m in markets:
            if m.mid_price < 0.12:
                signals.append(Signal("mean_reversion", m.market_id, Side.BUY, 3.8, 0.62, 5400, "revert_to_band", 0.20))
            elif m.mid_price > 0.88:
                signals.append(Signal("mean_reversion", m.market_id, Side.SELL, 3.4, 0.60, 5400, "revert_to_band", 0.80))
        return signals


class InventoryAwareMMStrategy:
    """Inventory-aware micro market making signal generator."""

    def __init__(self, context: StrategyContext, base_spread: float = 0.02):
        self.ctx = context
        self.base_spread = base_spread

    async def generate(self, markets: list[Market]) -> list[Signal]:
        out: list[Signal] = []
        for m in markets:
            inv = self.ctx.inventory_by_market.get(m.market_id, 0.0)
            skew = max(min(inv * 0.01, 0.03), -0.03)
            fair = m.mid_price - skew
            edge = (m.best_ask - m.best_bid) - self.base_spread
            if edge <= 0:
                continue
            side = Side.BUY if inv <= 0 else Side.SELL
            ev = max(0.5, edge * 100)
            out.append(Signal("inventory_mm", m.market_id, side, ev, 0.55, 1800, "spread_capture_or_inventory_limit", fair))
        return out


class CorrelationArbStrategy:
    """Simple overlap proxy: identify outlier pricing among same-category contracts."""

    async def generate(self, markets: list[Market]) -> list[Signal]:
        out: list[Signal] = []
        by_cat: dict[str, list[Market]] = {}
        for m in markets:
            by_cat.setdefault(m.category, []).append(m)

        for cat_markets in by_cat.values():
            if len(cat_markets) < 2:
                continue
            avg = mean([m.mid_price for m in cat_markets])
            for m in cat_markets:
                dev = m.mid_price - avg
                if dev > 0.10:
                    out.append(Signal("correlation_arb", m.market_id, Side.SELL, 2.2, 0.57, 7200, "mean_rejoin_cluster", avg))
                elif dev < -0.10:
                    out.append(Signal("correlation_arb", m.market_id, Side.BUY, 2.2, 0.57, 7200, "mean_rejoin_cluster", avg))
        return out


class StrategyEngine:
    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies

    async def generate_signals(self, markets: list[Market]) -> list[Signal]:
        signals: list[Signal] = []
        for s in self.strategies:
            signals.extend(await s.generate(markets))

        dedup: dict[tuple[str, str], Signal] = {}
        for sig in signals:
            if sig.ev_pct <= 0 or not (0 <= sig.confidence <= 1):
                continue
            key = (sig.market_id, sig.side.value)
            prev = dedup.get(key)
            if prev is None or sig.ev_pct > prev.ev_pct:
                dedup[key] = sig
        return list(dedup.values())
