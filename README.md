# Polymarket Institutional Bot (Safety-First)

## Disclaimer
Prediction markets carry inherent risk. This bot is for educational/development use. Always run in paper mode first. Past performance ≠ future results.

## Architecture
- `MarketScanner`: WebSocket-first (adapter), REST fallback filtering by volume/liquidity/expiry/category.
- `StrategyEngine`: Pluggable strategy modules output EV%, confidence, max hold, and exit trigger.
- `OrderManager`: Slippage guard (<=1.5%), stale-order cancels, idempotent client order ids.
- `RiskManager`: 2% daily loss cap, 3-loss or 5% DD circuit breaker, fractional Kelly <=0.5x, hard cap sizing.
- `PortfolioTracker`: fill tracking and CSV export.
- `Backtester`: fee/slippage-aware replay primitives.
- `Alerting`: webhook notifications.

## Setup
1. `cp .env.example .env`
2. Fill API keys and official exchange endpoints in `config.yaml`.
3. `pip install -r requirements.txt`
4. Paper mode (default): `python main.py`
5. Live mode (explicit): set `app.paper_mode: false`, then run `python main.py --live` and type `LIVE`.

## Rate Limits & API Notes
- Exchange adapter intentionally uses abstract placeholders to avoid incorrect endpoint assumptions.
- Implement official REST/CLOB routes and WS channels with strict timeout/retry and idempotency keys.
- Respect venue rate limits with bounded concurrency and exponential backoff.

## Testing
- `pytest -q`
