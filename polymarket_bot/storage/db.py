from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, future=True)
