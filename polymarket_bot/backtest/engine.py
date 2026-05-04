from __future__ import annotations

from dataclasses import dataclass
from polymarket_bot.risk.manager import RiskManager


@dataclass
class BacktestResult:
    total_pnl: float
    max_drawdown: float
    trades: int


class Backtester:
    def __init__(self, fee_bps: float = 10, slippage_bps: float = 15):
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps

    def run(self, prices: list[float], signals: list[int]) -> BacktestResult:
        equity, peak, pnl, trades = 10000.0, 10000.0, 0.0, 0
        position = 0
        for p, s in zip(prices, signals):
            if s != 0:
                trades += 1
                fill_price = p * (1 + self.slippage_bps / 10000)
                pnl += s * (1 - fill_price) - abs(s) * self.fee_bps / 10000
                position += s
            equity = 10000 + pnl
            peak = max(peak, equity)
        mdd = 1 - equity / peak if peak else 0
        return BacktestResult(total_pnl=pnl, max_drawdown=mdd, trades=trades)
