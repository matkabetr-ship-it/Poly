from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(slots=True)
class Market:
    market_id: str
    question: str
    category: str
    volume: float
    liquidity: float
    expiry: datetime
    mid_price: float
    best_bid: float
    best_ask: float


@dataclass(slots=True)
class Signal:
    strategy: str
    market_id: str
    side: Side
    ev_pct: float
    confidence: float
    max_hold_seconds: int
    exit_trigger: str
    fair_probability: float


@dataclass(slots=True)
class OrderIntent:
    market_id: str
    side: Side
    price: float
    quantity: float
    client_order_id: str
    is_market: bool = False


@dataclass(slots=True)
class Fill:
    order_id: str
    market_id: str
    side: Side
    avg_price: float
    quantity: float
    fee: float
    ts: datetime


@dataclass(slots=True)
class Position:
    market_id: str
    category: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    updated_at: datetime = field(default_factory=datetime.utcnow)
