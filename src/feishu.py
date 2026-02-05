import httpx
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FeishuSender:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send(self, signal_data: Dict[str, Any]):
        """
        发送飞书卡片消息
        signal_data结构:
        {
            "type": "OPEN" | "CLOSE" | "INCREASE" | "DECREASE" | "REVERSE",
            "coin": "BTC",
            "direction": "LONG" | "SHORT",
            "address": "0x...",
            "size": 1.5,
            "price": 42000.50,
            "time": 1700000000000
        }
        """
        if not self.webhook_url:
            logger.warning("No Feishu webhook URL provided, skipping notification")
            return

        card = self._build_card(signal_data)
        
        try:
            resp = await self.client.post(
                self.webhook_url,
                json={"msg_type": "interactive", "card": card}
            )
            resp.raise_for_status()
            logger.info(f"Feishu notification sent for {signal_data.get('type')} on {signal_data.get('coin')}")
        except Exception as e:
            logger.error(f"Failed to send Feishu notification: {e}")

    def _build_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
        signal_type = data.get("type", "UNKNOWN")
        coin = data.get("coin", "UNKNOWN")
        direction = data.get("direction", "UNKNOWN")
        
        # 颜色和标题配置
        color_map = {
            "OPEN": "green",      # 绿色
            "CLOSE": "red",       # 红色
            "INCREASE": "yellow", # 黄色
            "DECREASE": "blue",   # 蓝色
            "REVERSE": "purple"   # 紫色
        }
        color = color_map.get(signal_type, "grey")
        
        # 格式化数值
        price = f"${float(data.get('price', 0)):,.4f}"
        size = f"{float(data.get('size', 0)):,.4f}"
        
        # 处理时间
        import datetime
        ts = data.get("time", 0) / 1000  # ms to s
        time_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        title = f"[{signal_type}] {coin} {direction}"
        if signal_type == "REVERSE":
             title = f"[{signal_type}] {coin} 🔄"

        return {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**地址**\n{data.get('address')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**数量**\n{size}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**价格**\n{price}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**方向**\n{direction}"
                            }
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"时间: {time_str}"
                        }
                    ]
                }
            ]
        }

    async def close(self):
        await self.client.aclose()
