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
from polymarket_bot.strategies.engine import StrategyEngine, MeanReversionStrategy
from polymarket_bot.utils.logging import get_logger


async def run_bot(live: bool) -> None:
    cfg = load_settings()
    if live and cfg.app.paper_mode:
        raise RuntimeError("Refusing live mode while config paper_mode=true. Set false and pass --live.")

    log = get_logger()
    exchange = AbstractHTTPExchange(cfg.exchange.rest_base_url, cfg.exchange.ws_url, cfg.execution.request_timeout_seconds)
    await exchange.connect()
    scanner = MarketScanner(cfg.scanner, exchange)
    strategy = StrategyEngine([MeanReversionStrategy()])
    risk = RiskManager(cfg.risk, RiskState(starting_bankroll=10000, equity=10000))
    order_mgr = OrderManager(cfg.risk, exchange)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    while not stop_event.is_set():
        markets = await scanner.fetch_filtered_markets()
        signals = await strategy.generate_signals(markets)
        for s in signals:
            notional = risk.approve_signal(s, portfolio_value=10000)
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
            await order_mgr.submit(intent, mark_price=s.fair_probability)
            log.info("order_submitted", market_id=s.market_id, ev=s.ev_pct, confidence=s.confidence)
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
