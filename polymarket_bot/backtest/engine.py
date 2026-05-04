from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BacktestResult:
    total_pnl: float
    max_drawdown: float
    trades: int
    win_rate: float
    sharpe_like: float


class Backtester:
    def __init__(self, fee_bps: float = 10, slippage_bps: float = 15):
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps

    def run(self, prices: list[float], signals: list[int]) -> BacktestResult:
        equity, peak, pnl, trades, wins = 10000.0, 10000.0, 0.0, 0, 0
        rets: list[float] = []
        for p, s in zip(prices, signals):
            if s == 0:
                continue
            trades += 1
            fill_price = p * (1 + self.slippage_bps / 10000)
            trade_pnl = s * (1 - fill_price) - abs(s) * self.fee_bps / 10000
            wins += int(trade_pnl > 0)
            pnl += trade_pnl
            prev_eq = equity
            equity = 10000 + pnl
            peak = max(peak, equity)
            rets.append((equity - prev_eq) / max(prev_eq, 1e-9))
        mdd = 1 - (equity / peak if peak else 1)
        win_rate = wins / trades if trades else 0.0
        avg = sum(rets) / len(rets) if rets else 0.0
        vol = (sum((x - avg) ** 2 for x in rets) / len(rets)) ** 0.5 if rets else 1.0
        sharpe_like = avg / vol if vol > 0 else 0.0
        return BacktestResult(total_pnl=pnl, max_drawdown=mdd, trades=trades, win_rate=win_rate, sharpe_like=sharpe_like)
