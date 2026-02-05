from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SignalDetector:
    def __init__(self):
        pass

    def analyze(self, fill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        分析 fill 事件并返回信号
        Fill 结构示例:
        {
            "coin": "ETH",
            "px": "2150.50",
            "sz": "1.5",
            "time": 1704067200000,
            "startPosition": "0.0",
            "dir": "Open Long",
            "closedPnl": "0.0",
            "user": "0x..."
        }
        """
        try:
            raw_dir = fill.get("dir", "")
            if not raw_dir:
                return None

            start_pos_str = fill.get("startPosition", "0.0")
            sz_str = fill.get("sz", "0.0")
            
            start_pos = float(start_pos_str)
            sz = float(sz_str)
            
            # 解析方向
            # dir 可能是: "Open Long", "Close Short", "Open Short", "Close Long"
            # 以及可能存在的 "Increase Long" 等变体，视API版本而定。
            # 但根据 fill 的性质，关键是看 start_pos 和 sz 以及 dir 的组合。
            
            # 标准化基础方向
            is_long_oper = "Long" in raw_dir
            is_open_oper = "Open" in raw_dir
            
            # 计算结束仓位 (近似值，用于辅助判断)
            # 注意：hyperliquid的sz通常是正数，dir决定方向
            # Long: position > 0, Short: position < 0
            
            signal_type = "UNKNOWN"
            final_direction = "LONG" if is_long_oper else "SHORT"
            
            # 逻辑判定表
            # 1. OPEN: start_pos == 0
            if start_pos == 0:
                signal_type = "OPEN"
                
            # 2. CLOSE: 平仓操作导致仓位归零
            # Hyperliquid API如果是全平仓，通常 dir="Close Long/Short" 且 sz == abs(start_pos)
            # 这里简单判断：如果 start_pos != 0 且 dir 是 Close 且 sz >= abs(start_pos) - epsilon
            elif "Close" in raw_dir:
                if abs(sz - abs(start_pos)) < 1e-6: # 浮点数比较
                    signal_type = "CLOSE"
                else:
                    signal_type = "DECREASE" # 部分平仓
            
            # 3. INCREASE/DECREASE/REVERSE
            else:
                # 此时 start_pos != 0
                current_is_long = start_pos > 0
                oper_is_long = is_long_oper
                
                # 同向操作
                if current_is_long == oper_is_long:
                     # 既然不是 Open (start!=0)，如果是同向，通常是加仓
                     # 但要注意 Open Long 也可能用于加仓吗？API通常区分 Open 和 Close
                     # 如果是 Open Long 且已有 Long 仓位 -> Increase
                     if "Open" in raw_dir:
                         signal_type = "INCREASE"
                else:
                    # 反向操作
                    # 已经在 Close 中处理了平仓和减仓
                    # 如果这里出现 Open (如持有 Long 时 Open Short)，则是反手 REVERSE
                    if "Open" in raw_dir:
                        signal_type = "REVERSE"
                        final_direction = "SHORT" if oper_is_long else "LONG" # 反手后的方向（修正：其实是新开仓的方向）
                        # 修正: Reverse意味着从多变空，或空变多。
                        # 操作方向就是新的方向。
                        final_direction = "LONG" if is_long_oper else "SHORT"

            # 二次确认和修正
            # 如果 dir 明确包含 "Open"，且 start_pos != 0 且同向 -> INCREASE
            if "Open" in raw_dir and start_pos != 0:
                 if ("Long" in raw_dir and start_pos > 0) or ("Short" in raw_dir and start_pos < 0):
                     signal_type = "INCREASE"
            
            # 如果是反手，通常 start position 会从正变负或负变正，但 fill 事件可能只反映了一部分。
            # Hyperliquid 的 fill 事件如果导致反手，可能会拆分成两个 fills (一个平仓，一个开仓) 
            # 或者一个 fill。如果是一个 fill，dir 通常会体现。
            # 如果我们只收到一个 fill，且 start_pos * end_pos < 0，则是反手。
            # 但这里我们主要依赖 dir 字符串和 start_pos。
            
            # 简单化处理：
            # Open Long + start=0 -> OPEN
            # Close Long + sz=start -> CLOSE
            # Close Long + sz<start -> DECREASE
            # Open Long + start>0 (Long) -> INCREASE
            # Open Short + start>0 (Long) -> REVERSE (假设是直接反手)
            
            return {
                "type": signal_type,
                "coin": fill.get("coin"),
                "direction": final_direction,
                "address": fill.get("user"),
                "size": sz,
                "price": fill.get("px"),
                "time": fill.get("time")
            }

        except Exception as e:
            logger.error(f"Error detecting signal: {e}")
            return None
