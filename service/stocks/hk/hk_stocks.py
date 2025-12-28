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
    支持多数据源，按优先级顺序尝试，直到成功获取数据
    
    Returns:
        包含港股股票列表的字典
    """
    for source_name in DATA_SOURCES:
        try:
            # 动态导入数据源模块
            if source_name == 'eastmoney_stocks':
                # 使用绝对导入路径
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
                    raise ImportError(f"模块文件不存在: {module_path}")
            elif source_name == 'ak_stocks':
                # 使用绝对导入路径
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
                    raise ImportError(f"模块文件不存在: {module_path}")
            else:
                # 未来其他数据源的调用方式
                continue
            
            if result:
                print(f"[hk_stocks] 使用数据源 '{source_name}' 成功获取 {result['count']} 只港股")
                return result
            
        except ImportError as e:
            print(f"[hk_stocks] 无法导入数据源模块 '{source_name}': {e}")
            continue
        except Exception as e:
            print(f"[hk_stocks] 数据源 '{source_name}' 获取数据失败: {e}")
            continue
    
    print("[hk_stocks] 所有数据源均失败，无法获取港股股票列表")
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