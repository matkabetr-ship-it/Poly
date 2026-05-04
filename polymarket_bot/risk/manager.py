from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from polymarket_bot.core.models import Signal


@dataclass
class RiskState:
    starting_bankroll: float
    equity: float
    day_pnl: float = 0.0
    peak_equity: float = 0.0
    consecutive_losses: int = 0
    open_markets: set[str] = field(default_factory=set)
    category_notional: dict[str, float] = field(default_factory=lambda: defaultdict(float))


class RiskManager:
    def __init__(self, cfg, state: RiskState):
        self.cfg = cfg
        self.state = state
        self.state.peak_equity = max(state.peak_equity, state.equity)

    def circuit_breaker_triggered(self) -> bool:
        drawdown = 1 - (self.state.equity / max(self.state.peak_equity, 1e-9))
        return (
            self.state.consecutive_losses >= self.cfg.circuit_breaker_consecutive_losses
            or drawdown >= self.cfg.circuit_breaker_drawdown_pct
            or -self.state.day_pnl >= self.cfg.max_daily_loss_pct * self.state.starting_bankroll
        )

    def size_fractional_kelly(self, win_prob: float, odds_b: float = 1.0) -> float:
        raw = (win_prob * (odds_b + 1) - 1) / max(odds_b, 1e-9)
        raw = max(0.0, raw)
        return min(raw * self.cfg.kelly_fraction_cap, self.cfg.hard_position_cap_pct)

    def approve_signal(self, signal: Signal, portfolio_value: float, category: str) -> float:
        if self.circuit_breaker_triggered() or signal.ev_pct <= 0:
            return 0.0
        if len(self.state.open_markets) >= self.cfg.max_open_markets and signal.market_id not in self.state.open_markets:
            return 0.0

        frac = self.size_fractional_kelly(win_prob=signal.confidence)
        notional = portfolio_value * frac

        cat_limit = portfolio_value * self.cfg.max_category_exposure_pct
        remaining = cat_limit - self.state.category_notional.get(category, 0.0)
        notional = min(notional, max(0.0, remaining))
        return max(0.0, notional)

    def register_open(self, market_id: str, category: str, notional: float) -> None:
        self.state.open_markets.add(market_id)
        self.state.category_notional[category] += notional
