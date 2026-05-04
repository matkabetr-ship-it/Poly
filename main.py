from __future__ import annotations

import argparse
import asyncio
import signal
import uuid

from polymarket_bot.adapters.exchange import AbstractHTTPExchange
from polymarket_bot.core.config import load_settings
from polymarket_bot.core.order_manager import OrderManager
from polymarket_bot.core.scanner import MarketScanner
from polymarket_bot.core.models import OrderIntent
from polymarket_bot.risk.manager import RiskManager, RiskState
from polymarket_bot.strategies.engine import (
    CorrelationArbStrategy,
    InventoryAwareMMStrategy,
    MeanReversionStrategy,
    StrategyContext,
    StrategyEngine,
)
from polymarket_bot.utils.logging import get_logger


async def run_bot(live: bool) -> None:
    cfg = load_settings()
    if live and cfg.app.paper_mode:
        raise RuntimeError("Refusing live mode while config paper_mode=true. Set false and pass --live.")

    log = get_logger()
    exchange = AbstractHTTPExchange(cfg.exchange.rest_base_url, cfg.exchange.ws_url, cfg.execution.request_timeout_seconds)
    await exchange.connect()
    scanner = MarketScanner(cfg.scanner, exchange)
    strategy_context = StrategyContext(inventory_by_market={})
    strategy = StrategyEngine([MeanReversionStrategy(), CorrelationArbStrategy(), InventoryAwareMMStrategy(strategy_context)])
    risk = RiskManager(cfg.risk, RiskState(starting_bankroll=10000, equity=10000))
    order_mgr = OrderManager(cfg.risk, exchange)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    while not stop_event.is_set():
        markets = await scanner.fetch_filtered_markets()
        market_lookup = {m.market_id: m for m in markets}
        signals = sorted(await strategy.generate_signals(markets), key=lambda s: s.ev_pct * s.confidence, reverse=True)

        for s in signals:
            market = market_lookup.get(s.market_id)
            if not market:
                continue
            notional = risk.approve_signal(s, portfolio_value=risk.state.equity, category=market.category)
            if notional <= 0:
                log.info("risk_reject", market_id=s.market_id, strategy=s.strategy)
                continue
            intent = OrderIntent(
                market_id=s.market_id,
                side=s.side,
                price=s.fair_probability,
                quantity=max(notional, 1) / max(s.fair_probability, 0.01),
                client_order_id=str(uuid.uuid4()),
                is_market=False,
            )
            oid = await order_mgr.submit(intent, mark_price=market.mid_price, category=market.category)
            if oid:
                risk.register_open(s.market_id, market.category, notional)
                log.info("order_submitted", order_id=oid, market_id=s.market_id, ev=s.ev_pct, confidence=s.confidence)

        await order_mgr.cancel_stale()
        await asyncio.sleep(cfg.execution.poll_interval_seconds)

    await exchange.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Enable live mode. Requires explicit config change.")
    args = parser.parse_args()
    if args.live:
        confirm = input("Type LIVE to confirm real trading: ")
        if confirm.strip() != "LIVE":
            raise SystemExit("Live confirmation failed.")
    asyncio.run(run_bot(args.live))
