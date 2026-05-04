from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class RiskConfig(BaseModel):
    max_daily_loss_pct: float = 0.02
    circuit_breaker_drawdown_pct: float = 0.05
    circuit_breaker_consecutive_losses: int = 3
    kelly_fraction_cap: float = 0.5
    hard_position_cap_pct: float = 0.02
    slippage_tolerance_pct: float = 0.015
    max_open_markets: int = 8
    max_category_exposure_pct: float = 0.25


class ExecutionConfig(BaseModel):
    order_ttl_seconds: int = 45
    poll_interval_seconds: int = 2
    ws_reconnect_max_seconds: int = 30
    request_timeout_seconds: int = 10


class ScannerConfig(BaseModel):
    min_volume: float
    min_liquidity: float
    max_days_to_expiry: int
    categories: list[str]


class StorageConfig(BaseModel):
    url: str


class ExchangeConfig(BaseModel):
    rest_base_url: str
    ws_url: str
    api_key: str = ""
    api_secret: str = ""


class AlertsConfig(BaseModel):
    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_to: str = ""


class AppConfig(BaseModel):
    env: str = "dev"
    paper_mode: bool = True
    base_currency: str = "USD"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POLY__", env_nested_delimiter="__", extra="ignore")
    app: AppConfig = Field(default_factory=AppConfig)
    risk: RiskConfig
    execution: ExecutionConfig
    scanner: ScannerConfig
    alerts: AlertsConfig
    storage: StorageConfig
    exchange: ExchangeConfig


def load_settings(path: str = "config.yaml") -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Settings(**raw)
