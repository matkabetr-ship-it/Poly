from polymarket_bot.risk.manager import RiskManager, RiskState


class Cfg:
    max_daily_loss_pct = 0.02
    circuit_breaker_drawdown_pct = 0.05
    circuit_breaker_consecutive_losses = 3
    kelly_fraction_cap = 0.5
    hard_position_cap_pct = 0.02


def test_risk_reject_on_losses():
    r = RiskManager(Cfg(), RiskState(starting_bankroll=10000, equity=9000, day_pnl=-300, peak_equity=10000, consecutive_losses=3))
    assert r.circuit_breaker_triggered() is True
