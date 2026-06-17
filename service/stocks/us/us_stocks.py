"""
美股列表获取模块
整合多个数据源获取美股列表
参考 kline.py 的配置结构

过滤规则：只保留普通股，排除基金/ETF/REIT/信托/优先股/单位/权证等非股票类
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from openbb import obb

# 导入各个数据源模块
from .sec_stocks import get_sec_stocks_all
from .finnhub_stocks import get_finnhub_stocks_all

# 数据源配置（参考 kline.py 的 DATA_SOURCES_CONFIG 结构）
US_DATA_SOURCES_CONFIG = {
    'default': ['sec', 'finnhub'],  # 默认数据源优先级
    'available': ['sec', 'finnhub'],  # 可用数据源
    'exchange_mapping': {  # 交易所代码映射
        'sec': {'N': 'Nasdaq', 'A': 'NYSE', 'P': 'AMEX'},
        'finnhub': {'N': 'US', 'A': 'US', 'P': 'US'},  # Finnhub使用统一的US交易所代码
    }
}

# 名称关键词过滤：名称中包含以下关键词的证券排除（非普通股）
FILTER_NAME_KEYWORDS = [
    " ETF", " ETN", " ETP", " FUND", " REIT", " TRUST",
    "LP", "L.P", "LIMITED PARTNERSHIP",
    "UNIT", "UNITS", " WARRANT", " RIGHTS",
    " PREF", " PREFERRED", "PREFERRED STOCK",
    " CLOSED-END", "CLOSED END",
    " BOND", " NOTE", " NOTES",
    " DEPOSITARY SHARES", " DEPOSITORY SHARES",
    " ADR", " GDR", " NVDR",
    " CERTIFICATE", " SPAC ", " ACQUISITION CO",
    " ACQUISITION CORP",
    " INDEX", " MORTGAGE",
]

# 代码格式过滤：包含以下符号的排除（优先股/权证/单位的特殊后缀）
EXCLUDE_SYMBOL_PATTERNS = [".", "-", "/"]


def _is_common_stock(code: str, name: str) -> bool:
    """判断是否为普通股（通过代码和名称过滤）

    返回 True 表示保留（认为是普通股），False 表示排除
    """
    code_up = str(code).upper()
    name_up = str(name).upper()

    # 1) 代码格式排除：包含 . - / 都是特殊证券
    for pat in EXCLUDE_SYMBOL_PATTERNS:
        if pat in code_up:
            return False

    # 2) 名称关键词排除
    for kw in FILTER_NAME_KEYWORDS:
        if kw in name_up:
            return False

    # 3) 代码长度限制：美股代码通常 1-5 个字符（不含后缀）
    if len(code_up) > 5:
        return False

    # 4) 名称太短的排除（空名称或只有几个字符通常不是真实股票）
    if len(name_up.strip()) < 2:
        return False

    return True


def _filter_us_stocks(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """统一的美股过滤函数：只保留普通股

    Args:
        stocks: 原始股票列表 [{code, name, market, full_code, ...}, ...]

    Returns:
        过滤后的股票列表
    """
    if not stocks:
        return stocks

    before = len(stocks)
    filtered = [s for s in stocks if _is_common_stock(s.get("code", ""), s.get("name", ""))]
    after = len(filtered)

    print(f"美股过滤：{before} → {after}（排除 {before - after} 只非普通股）")
    return filtered


def get_us_stocks(data_source: str = None) -> Optional[Dict[str, Any]]:
    """
    获取美股列表（只包含普通股，排除基金/ETF/REIT/信托/优先股等）

    Args:
        data_source: 指定数据源（sec, yfinance, fmp），不指定则按优先级尝试

    Returns:
        包含美股股票列表的字典（已过滤非普通股）
    """
    try:
        print(f"开始获取美股列表，数据源: {data_source if data_source else '按优先级尝试'}")

        # 如果指定了数据源，直接使用该数据源
        if data_source:
            if data_source == 'sec':
                result = get_sec_stocks_all()
            elif data_source == 'finnhub':
                result = get_finnhub_stocks_all()
            else:
                print(f"不支持的数据源: {data_source}")
                return None
            if result and result.get('stocks'):
                result['stocks'] = _filter_us_stocks(result['stocks'])
                result['count'] = len(result['stocks'])
            return result

        # 按优先级尝试各个数据源
        for source in US_DATA_SOURCES_CONFIG['default']:
            print(f"尝试使用 {source} 数据源...")

            if source == 'sec':
                result = get_sec_stocks_all()
            elif source == 'finnhub':
                result = get_finnhub_stocks_all()
            else:
                continue

            if result and result['stocks']:
                # 统一过滤：只保留普通股
                result['stocks'] = _filter_us_stocks(result['stocks'])
                result['count'] = len(result['stocks'])
                print(f"{source} 数据源获取并过滤后，共 {result['count']} 只股票")
                return result
            else:
                print(f"{source} 数据源获取失败，尝试下一个数据源...")

        print("所有数据源获取美股列表失败")
        
        # 兜底返回200个常见美股
        try:
            import sys
            import os
            module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_stocks.py')
            if os.path.exists(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location('fallback_stocks', module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print("[us_stocks] 使用兜底数据源返回200个常见美股")
                return module.get_fallback_us_stocks()
        except Exception as e:
            print(f"[us_stocks] 获取兜底数据失败: {e}")
            
        return None

    except Exception as e:
        print(f"获取美股列表时发生错误: {e}")
        return None


def get_us_stocks_by_exchange(exchange: str = "N", data_source: str = None) -> Optional[Dict[str, Any]]:
    """
    按交易所获取美股列表（只包含普通股，排除基金/ETF/REIT/信托/优先股等）

    Args:
        exchange: 交易所代码
            - 对于 sec 数据源: N=Nasdaq, A=NYSE, P=AMEX
            - 对于 yfinance 数据源: nasdaq, nyse, amex
            - 对于 finnhub 数据源: US（统一使用US）
        data_source: 指定数据源（sec, finnhub），不指定则按优先级尝试

    Returns:
        包含美股股票列表的字典（已过滤非普通股）
    """
    try:
        print(f"开始获取 {exchange} 交易所的美股列表，数据源: {data_source if data_source else '按优先级尝试'}")

        # 如果指定了数据源，直接使用该数据源
        if data_source:
            if data_source == 'sec':
                from .sec_stocks import get_sec_stocks
                result = get_sec_stocks(exchange)
            elif data_source == 'finnhub':
                from .finnhub_stocks import get_finnhub_stocks
                # Finnhub使用统一的US交易所代码
                result = get_finnhub_stocks("US")
            else:
                print(f"不支持的数据源: {data_source}")
                return None
            if result and result.get('stocks'):
                result['stocks'] = _filter_us_stocks(result['stocks'])
                result['count'] = len(result['stocks'])
            return result

        # 按优先级尝试各个数据源
        for source in US_DATA_SOURCES_CONFIG['default']:
            print(f"尝试使用 {source} 数据源...")

            if source == 'sec':
                from .sec_stocks import get_sec_stocks
                result = get_sec_stocks(exchange)
            elif source == 'finnhub':
                from .finnhub_stocks import get_finnhub_stocks
                # Finnhub使用统一的US交易所代码
                result = get_finnhub_stocks("US")
            else:
                continue

            if result and result['stocks']:
                # 统一过滤：只保留普通股
                result['stocks'] = _filter_us_stocks(result['stocks'])
                result['count'] = len(result['stocks'])
                print(f"{source} 数据源获取并过滤后，共 {result['count']} 只股票")
                return result
            else:
                print(f"{source} 数据源获取失败，尝试下一个数据源...")

        print(f"所有数据源获取 {exchange} 交易所股票列表失败")
        
        # 兜底返回200个常见美股
        try:
            import sys
            import os
            module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fallback_stocks.py')
            if os.path.exists(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location('fallback_stocks', module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print("[us_stocks] 使用兜底数据源返回200个常见美股")
                return module.get_fallback_us_stocks()
        except Exception as e:
            print(f"[us_stocks] 获取兜底数据失败: {e}")
            
        return None

    except Exception as e:
        print(f"按交易所获取美股列表时发生错误: {e}")
        return None


if __name__ == "__main__":
    # 测试获取美股列表
    print("测试获取美股列表:")

    # 测试按优先级获取
    print("\n1. 测试按优先级获取（默认）:")
    result = get_us_stocks()
    if result:
        print(f"获取到 {result['count']} 只股票，数据源: {result.get('source', 'unknown')}")
        if result['stocks']:
            print("前5只股票:")
            for stock in result['stocks'][:5]:
                print(f"  {stock['code']}: {stock['name']}")
    else:
        print("获取失败")

    # 测试finnhub数据源
    print("\n2. 测试finnhub数据源:")
    result = get_us_stocks(data_source="finnhub")
    if result:
        print(f"获取到 {result['count']} 只股票，数据源: {result.get('source', 'unknown')}")
        if result['stocks']:
            print("前5只股票:")
            for stock in result['stocks'][:5]:
                print(f"  {stock['code']}: {stock['name']}")
    else:
        print("获取失败")
