from polymarket_bot.risk.manager import RiskManager, RiskState
from polymarket_bot.core.models import Signal, Side


class Cfg:
    max_daily_loss_pct = 0.02
    circuit_breaker_drawdown_pct = 0.05
    circuit_breaker_consecutive_losses = 3
    kelly_fraction_cap = 0.5
    hard_position_cap_pct = 0.02
    max_open_markets = 2
    max_category_exposure_pct = 0.25


def test_risk_reject_on_losses():
    r = RiskManager(Cfg(), RiskState(starting_bankroll=10000, equity=9000, day_pnl=-300, peak_equity=10000, consecutive_losses=3))
    assert r.circuit_breaker_triggered() is True


def test_category_cap_enforced():
    r = RiskManager(Cfg(), RiskState(starting_bankroll=10000, equity=10000, day_pnl=0, peak_equity=10000, consecutive_losses=0))
    sig = Signal("s", "m1", Side.BUY, 2.0, 0.7, 60, "x", 0.6)
    r.register_open("m0", "politics", 2500)
    size = r.approve_signal(sig, 10000, "politics")
    assert size == 0.0
