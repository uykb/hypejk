import asyncio
import logging
import signal
import sys
from src.config import load_config
from src.hyperliquid_client import HyperliquidClient
from src.detector import SignalDetector
from src.feishu import FeishuSender

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("monitor.log")
    ]
)
logger = logging.getLogger(__name__)

async def process_fill(fill: dict, detector: SignalDetector, feishu: FeishuSender):
    """异步处理单个 fill 事件"""
    try:
        # SDK 返回的数据结构可能略有不同，需要打印调试
        logger.debug(f"Received fill: {fill}")
        
        # 兼容 SDK 可能返回的包装结构
        # 假设 fill 是 raw dict
        
        signal = detector.analyze(fill)
        if signal and signal["type"] != "UNKNOWN":
            logger.info(f"Detected signal: {signal}")
            await feishu.send(signal)
            
    except Exception as e:
        logger.error(f"Error processing fill: {e}")

def sdk_callback(event, loop, detector, feishu):
    """SDK 回调函数 (运行在 SDK 线程)"""
    # 过滤事件类型
    # userFills 事件结构:
    # {
    #   "channel": "userFills",
    #   "data": {
    #     "isSnapshot": true/false,
    #     "user": "...",
    #     "fills": [...]
    #   }
    # }
    try:
        data = event.get("data", {})
        if not data:
            return

        # 忽略快照，只处理实时更新？
        # 第一次订阅会收到 snapshot，包含历史 fills。
        # 如果我们需要实时信号，应该忽略 snapshot 或者是处理它来初始化状态（如果我们有状态管理）
        # 本项目中无持久化状态，如果处理 snapshot 可能会导致旧信号刷屏。
        # 建议：如果是 isSnapshot=True，则忽略，或者只记录不推送。
        
        is_snapshot = data.get("isSnapshot", False)
        if is_snapshot:
            logger.info("Received snapshot data, skipping notification...")
            return

        fills = data.get("fills", [])
        for fill in fills:
            # 注入 user 字段，因为 fill 对象本身可能不包含 user (它在外层 data 中)
            fill_with_user = fill.copy()
            if "user" not in fill_with_user:
                fill_with_user["user"] = data.get("user")
            
            # 调度到 asyncio 循环
            asyncio.run_coroutine_threadsafe(
                process_fill(fill_with_user, detector, feishu), 
                loop
            )
            
    except Exception as e:
        logger.error(f"Error in SDK callback: {e}")

async def main():
    # 加载配置
    config = load_config("config.yaml")
    
    # 初始化组件
    detector = SignalDetector()
    feishu = FeishuSender(config.feishu.webhook_url)
    client = HyperliquidClient(
        addresses=config.monitor.addresses, 
        api_url=config.hyperliquid.api_url
    )
    
    # 获取当前循环
    loop = asyncio.get_running_loop()
    
    # 注册回调
    # 使用偏函数或 lambda 将 loop 和其他组件传递给回调
    client.add_callback(lambda event: sdk_callback(event, loop, detector, feishu))
    
    # 启动监听
    client.start()
    
    logger.info("Monitor started. Press Ctrl+C to exit.")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Stopping...")
    finally:
        await feishu.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
