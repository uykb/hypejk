import yaml
import os
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class MonitorConfig:
    addresses: List[str]

@dataclass
class FeishuConfig:
    webhook_url: str

@dataclass
class HyperliquidConfig:
    api_url: str
    ws_url: str
    reconnect_delay: int

@dataclass
class Config:
    monitor: MonitorConfig
    feishu: FeishuConfig
    hyperliquid: HyperliquidConfig

def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(
        monitor=MonitorConfig(
            addresses=[addr.lower() for addr in data["monitor"]["addresses"]]
        ),
        feishu=FeishuConfig(
            webhook_url=data["feishu"].get("webhook_url", "")
        ),
        hyperliquid=HyperliquidConfig(
            api_url=data["hyperliquid"].get("api_url", "https://api.hyperliquid.xyz"),
            ws_url=data["hyperliquid"].get("ws_url", "wss://api.hyperliquid.xyz/ws"),
            reconnect_delay=data["hyperliquid"].get("reconnect_delay", 5)
        )
    )
