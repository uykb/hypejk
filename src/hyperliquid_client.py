import asyncio
import logging
from typing import List, Callable, Any
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)

class HyperliquidClient:
    def __init__(self, addresses: List[str], api_url: str = "", ws_url: str = ""):
        self.addresses = addresses
        # SDK 自动处理 URL，这里主要是传递给 SDK
        # 注意：SDK 的 Info 类初始化可能不需要显式 ws_url，它通常内置了。
        # 如果需要自定义，需查看 SDK 源码，但通常使用 constants.MAINNET_API_URL
        
        base_url = constants.MAINNET_API_URL
        if api_url and "testnet" in api_url:
            base_url = constants.TESTNET_API_URL
            
        self.info = Info(base_url=base_url, skip_ws=False)
        self.callbacks = []

    def add_callback(self, callback: Callable[[Any], None]):
        self.callbacks.append(callback)

    def _handle_event(self, event: Any):
        # 分发事件给所有回调
        for cb in self.callbacks:
            try:
                # 确保回调是异步安全的，虽然 SDK 回调通常在独立线程运行
                # 我们这里直接调用，如果 callback 是 async 的，需要用 run_coroutine_threadsafe
                # 为了简化，我们在主程序中统一处理
                cb(event)
            except Exception as e:
                logger.error(f"Error in callback: {e}")

    def start(self):
        """
        启动监听
        注意：SDK 的 subscribe 是非阻塞的（启动后台线程）还是阻塞的？
        根据搜索结果，info.subscribe 似乎只是发送订阅请求，SDK 内部有 ws 线程处理消息并调用 callback。
        """
        logger.info(f"Starting Hyperliquid monitor for {len(self.addresses)} addresses...")
        
        for address in self.addresses:
            logger.info(f"Subscribing to userFills for {address}")
            # 订阅 userFills
            # SDK用法: info.subscribe({"type": "userFills", "user": address}, callback)
            self.info.subscribe(
                {"type": "userFills", "user": address}, 
                self._handle_event
            )
            
        # 保持主线程运行
        # 由于 SDK 使用后台线程，我们需要在这里挂起
        # 但我们在 main.py 中会运行 asyncio loop，所以这里只需启动订阅即可

    def stop(self):
        # SDK 可能没有显式的 stop 方法用于关闭 ws，但程序退出时会释放
        pass
