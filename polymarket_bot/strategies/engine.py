from __future__ import annotations

from typing import Protocol
from polymarket_bot.core.models import Market, Signal, Side


class Strategy(Protocol):
    async def generate(self, markets: list[Market]) -> list[Signal]: ...


class MeanReversionStrategy:
    async def generate(self, markets: list[Market]) -> list[Signal]:
        signals: list[Signal] = []
        for m in markets:
            if m.mid_price < 0.15:
                signals.append(Signal("mean_reversion", m.market_id, Side.BUY, 3.0, 0.58, 7200, "revert_to_mean", 0.22))
            elif m.mid_price > 0.85:
                signals.append(Signal("mean_reversion", m.market_id, Side.SELL, 2.5, 0.56, 7200, "revert_to_mean", 0.78))
        return signals


class StrategyEngine:
    def __init__(self, strategies: list[Strategy]):
        self.strategies = strategies

    async def generate_signals(self, markets: list[Market]) -> list[Signal]:
        signals: list[Signal] = []
        for s in self.strategies:
            signals.extend(await s.generate(markets))
        return [x for x in signals if x.ev_pct > 0 and 0 <= x.confidence <= 1]
