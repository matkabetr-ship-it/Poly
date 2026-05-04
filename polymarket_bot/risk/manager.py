from __future__ import annotations

from dataclasses import dataclass
from polymarket_bot.core.models import Signal


@dataclass
class RiskState:
    starting_bankroll: float
    equity: float
    day_pnl: float = 0.0
    peak_equity: float = 0.0
    consecutive_losses: int = 0


class RiskManager:
    def __init__(self, cfg, state: RiskState):
        self.cfg = cfg
        self.state = state
        self.state.peak_equity = max(state.peak_equity, state.equity)

    def circuit_breaker_triggered(self) -> bool:
        drawdown = 1 - (self.state.equity / max(self.state.peak_equity, 1e-9))
        if self.state.consecutive_losses >= self.cfg.circuit_breaker_consecutive_losses:
            return True
        if drawdown >= self.cfg.circuit_breaker_drawdown_pct:
            return True
        if -self.state.day_pnl >= self.cfg.max_daily_loss_pct * self.state.starting_bankroll:
            return True
        return False

    def size_fractional_kelly(self, edge: float, win_prob: float, odds_b: float) -> float:
        raw = (win_prob * (odds_b + 1) - 1) / max(odds_b, 1e-9)
        raw = max(0.0, raw)
        return min(raw * self.cfg.kelly_fraction_cap, self.cfg.hard_position_cap_pct)

    def approve_signal(self, signal: Signal, portfolio_value: float) -> float:
        if self.circuit_breaker_triggered() or signal.ev_pct <= 0:
            return 0.0
        edge = signal.ev_pct / 100
        frac = self.size_fractional_kelly(edge=edge, win_prob=signal.confidence, odds_b=1.0)
        return portfolio_value * frac
