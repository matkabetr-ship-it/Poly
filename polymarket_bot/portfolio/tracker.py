from __future__ import annotations

import csv
from pathlib import Path
from polymarket_bot.core.models import Fill


class PortfolioTracker:
    def __init__(self) -> None:
        self.realized_pnl = 0.0
        self.fills: list[Fill] = []

    def on_fill(self, fill: Fill) -> None:
        self.fills.append(fill)

    def export_csv(self, path: str = "trades.csv") -> None:
        p = Path(path)
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["order_id", "market_id", "side", "price", "qty", "fee", "ts"])
            for x in self.fills:
                w.writerow([x.order_id, x.market_id, x.side.value, x.avg_price, x.quantity, x.fee, x.ts.isoformat()])
