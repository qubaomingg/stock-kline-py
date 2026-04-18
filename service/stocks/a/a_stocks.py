#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国A股市场股票列表服务 - 多数据源入口
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# 添加当前目录到Python路径，以便导入数据源模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 数据源列表（按优先级顺序）
DATA_SOURCES = [
    'eastmoney_stocks',  # 东方财富数据源（无需API密钥，数据完整）
    'ak_stocks',         # akshare数据源
    'bs_stocks',         # baostock数据源
    # 未来可以添加更多数据源，如：'finnhub_stocks', 'yahoo_stocks'
]


def get_a_stocks() -> Optional[Dict[str, Any]]:
    """
    获取中国A股市场所有股票列表
    优先使用兜底数据，因为真实数据源暂时不可用

    Returns:
        包含A股股票列表的字典
    """
    # 优先使用兜底数据，因为东方财富和akshare现在都不可用
    try:
        import sys
        import os
        module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_stocks.py')
        if os.path.exists(module_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location('fallback_stocks', module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("[a_stocks] 使用兜底数据源返回A股数据")
            return module.get_fallback_a_stocks()
    except Exception as e:
        print(f"[a_stocks] 获取兜底数据失败: {e}")

    # 如果兜底数据也失败，尝试真实数据源（但暂时应该都不可用）
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
                    result = module.get_a_stocks_by_ak()
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
                    result = module.get_a_stocks_by_eastmoney()
                else:
                    continue
            elif source_name == 'bs_stocks':
                import sys
                import os
                module_path = os.path.join(os.path.dirname(__file__), 'bs_stocks.py')
                if os.path.exists(module_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location('bs_stocks', module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result = module.get_a_stocks_by_baostock()
                else:
                    continue
            else:
                continue

            if result:
                print(f"[a_stocks] 使用数据源 '{source_name}' 成功获取 {result['count']} 只A股股票")
                return result

        except Exception as e:
            print(f"[a_stocks] 数据源 '{source_name}' 获取数据失败: {e}")
            continue

    print("[a_stocks] 所有数据源均失败")
    return None


if __name__ == "__main__":
    result = get_a_stocks()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只A股股票")
        print(f"数据源: {result.get('source', 'unknown')}")
        print(f"时间戳: {result.get('timestamp', 'unknown')}")
        print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取A股股票列表失败")
