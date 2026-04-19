#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场股票列表服务 - 多数据源入口
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os
import importlib.util

# 添加当前目录到Python路径，以便导入数据源模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 数据源列表（按优先级顺序）
DATA_SOURCES = [
    'extended_hk_stocks',  # 增强版港股数据源（新增，包含真实数据 + 扩展数据）
    'finnhub_stocks',      # finnhub数据源（新增，支持 exchange=HK）
    'openbb_stocks',       # openbb-china数据源（新增，配合 openbb）
    'ak_stocks',           # akshare数据源
    'eastmoney_stocks',    # openbb-china eastmoney数据源
]


def _load_module(filename):
    """ 加载数据源模块"""
    try:
        module_path = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(module_path):
            return None
        spec = importlib.util.spec_from_file_location(filename.replace('.py', ''), module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"加载模块失败: {filename}, 错误: {e}")
        return None


def get_hk_stocks() -> Optional[Dict[str, Any]]:
    """
    获取港股市场所有股票列表（组合真实数据 + 兜底数据去重）

    Returns:
        包含港股股票列表的字典
    """
    # 1. 先获取真实数据
    real_stocks = []
    real_source = ''
    for source_name in DATA_SOURCES:
        try:
            module = None
            result = None
            if source_name == 'extended_hk_stocks':
                module = _load_module('extended_hk_stocks.py')
                if module and hasattr(module, 'get_hk_stocks_by_extended'):
                    result = module.get_hk_stocks_by_extended()
            elif source_name == 'finnhub_stocks':
                module = _load_module('finnhub_stocks.py')
                if module and hasattr(module, 'get_hk_stocks_by_finnhub'):
                    result = module.get_hk_stocks_by_finnhub()
            elif source_name == 'openbb_stocks':
                module = _load_module('openbb_stocks.py')
                if module and hasattr(module, 'get_hk_stocks_by_openbb'):
                    result = module.get_hk_stocks_by_openbb()
            elif source_name == 'ak_stocks':
                module = _load_module('ak_stocks.py')
                if module and hasattr(module, 'get_hk_stocks_by_ak'):
                    result = module.get_hk_stocks_by_ak()
            elif source_name == 'eastmoney_stocks':
                module = _load_module('eastmoney_stocks.py')
                if module and hasattr(module, 'get_hk_stocks_by_eastmoney'):
                    result = module.get_hk_stocks_by_eastmoney()

            if result and result.get('stocks'):
                real_stocks = result['stocks']
                real_source = result.get('source', 'unknown')
                print(f"[hk_stocks] 从数据源 '{source_name}' 获取 {len(real_stocks)} 只真实港股")
                break
        except Exception as e:
            print(f"[hk_stocks] 数据源 '{source_name}' 获取数据失败: {e}")
            continue

    # 2. 获取兜底数据
    fallback_stocks = []
    try:
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_stocks.py')
        if os.path.exists(fallback_path):
            spec = importlib.util.spec_from_file_location('fallback_stocks', fallback_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            fallback = module.get_fallback_hk_stocks()
            if fallback and fallback.get('stocks'):
                fallback_stocks = fallback['stocks']
                print(f"[hk_stocks] 兜底数据有 {len(fallback_stocks)} 只港股")
    except Exception as e:
        print(f"[hk_stocks] 获取兜底数据失败: {e}")

    # 3. 合并去重：真实数据优先 + 兜底补充
    final_stocks = []
    seen_codes = set()

    for stock in real_stocks:
        final_stocks.append(stock)
        seen_codes.add(stock['code'])

    for stock in fallback_stocks:
        if stock['code'] not in seen_codes:
            final_stocks.append(stock)
            seen_codes.add(stock['code'])

    print(f"[hk_stocks] 合并后共 {len(final_stocks)} 只港股（真实 {len(real_stocks)} + 兜底补充 {len(final_stocks)-len(real_stocks)}）")

    if len(final_stocks) > 0:
        return {
            'market': 'hk',
            'count': len(final_stocks),
            'stocks': final_stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': real_source if real_source else 'fallback'
        }
    else:
        print("[hk_stocks] 没有获取到任何港股数据")
        return None


if __name__ == "__main__":
    result = get_hk_stocks()
    if result:
        print(f"测试成功: 获取到 {result['count']} 只港股")
        print(f"数据源: {result.get('source', 'unknown')}")
        print(f"时间戳: {result.get('timestamp', 'unknown')}")
        if result['stocks']:
            print(f"第一只股票: {result['stocks'][0]}")
    else:
        print("测试失败: 获取港股股票列表失败")
