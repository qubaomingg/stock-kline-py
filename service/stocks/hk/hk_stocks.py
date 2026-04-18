#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场股票列表服务 - 多数据源入口
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# 添加当前目录到Python路径，以便导入数据源模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 数据源列表（按优先级顺序）
DATA_SOURCES = [
    'ak_stocks',           # akshare数据源
    'eastmoney_stocks',    # openbb-china eastmoney数据源
    # 未来可以添加更多数据源，如：'finnhub_stocks', 'yahoo_stocks'
]


def get_hk_stocks() -> Optional[Dict[str, Any]]:
    """
    获取港股市场所有股票列表

    Returns:
        包含港股股票列表的字典
    """
    # 首先尝试真实数据源
    for source_name in DATA_SOURCES:
        try:
            if source_name == 'ak_stocks':
                import sys
                import os
                module_path = os.path.join(os.path.dirname(__file__), 'ak_stocks.py')
                if os.path.exists(module_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location('ak_stocks', module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result = module.get_hk_stocks_by_ak()
                else:
                    continue
            elif source_name == 'eastmoney_stocks':
                import sys
                import os
                module_path = os.path.join(os.path.dirname(__file__), 'eastmoney_stocks.py')
                if os.path.exists(module_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location('eastmoney_stocks', module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result = module.get_hk_stocks_by_eastmoney()
                else:
                    continue
            else:
                continue

            if result:
                print(f"[hk_stocks] 使用数据源 '{source_name}' 成功获取 {result['count']} 只港股股票")
                return result

        except Exception as e:
            print(f"[hk_stocks] 数据源 '{source_name}' 获取数据失败: {e}")
            continue

    print("[hk_stocks] 所有真实数据源均失败，使用兜底数据")
    
    # 兜底数据作为最后保障
    try:
        import sys
        import os
        module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_stocks.py')
        if os.path.exists(module_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location('fallback_stocks', module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("[hk_stocks] 使用兜底数据源返回港股数据")
            return module.get_fallback_hk_stocks()
    except Exception as e:
        print(f"[hk_stocks] 获取兜底数据失败: {e}")

    print("[hk_stocks] 所有数据源均失败")
    return None


if __name__ == "__main__":
    result = get_hk_stocks()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只港股")
        print(f"数据源: {result.get('source', 'unknown')}")
        print(f"时间戳: {result.get('timestamp', 'unknown')}")
        print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取港股股票列表失败")
