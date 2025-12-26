"""
美股列表获取模块
整合多个数据源获取美股列表
参考 kline.py 的配置结构
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from openbb import obb

# 导入各个数据源模块
from .sec_stocks import get_sec_stocks_all

# 数据源配置（参考 kline.py 的 DATA_SOURCES_CONFIG 结构）
US_DATA_SOURCES_CONFIG = {
    'default': ['sec'],  # 默认数据源优先级
    'available': ['sec'],  # 可用数据源
    'exchange_mapping': {  # 交易所代码映射
        'sec': {'N': 'Nasdaq', 'A': 'NYSE', 'P': 'AMEX'},
        'yfinance': {'N': 'nasdaq', 'A': 'nyq', 'P': 'amex'},
    }
}


def get_us_stocks(data_source: str = None) -> Optional[Dict[str, Any]]:
    """
    获取美股列表
    
    Args:
        data_source: 指定数据源（sec, yfinance, fmp），不指定则按优先级尝试
        
    Returns:
        包含美股股票列表的字典
    """
    try:
        print(f"开始获取美股列表，数据源: {data_source if data_source else '按优先级尝试'}")
        
        # 如果指定了数据源，直接使用该数据源
        if data_source:
            if data_source == 'sec':
                return get_sec_stocks_all()
            else:
                print(f"不支持的数据源: {data_source}")
                return None
        
        # 按优先级尝试各个数据源
        for source in US_DATA_SOURCES_CONFIG['default']:
            print(f"尝试使用 {source} 数据源...")
            
            if source == 'sec':
                result = get_sec_stocks_all()
            else:
                continue
            
            if result and result['stocks']:
                print(f"{source} 数据源获取成功，共 {result['count']} 只股票")
                return result
            else:
                print(f"{source} 数据源获取失败，尝试下一个数据源...")
        
        print("所有数据源获取美股列表失败")
        return None
        
    except Exception as e:
        print(f"获取美股列表时发生错误: {e}")
        return None


def get_us_stocks_by_exchange(exchange: str = "N", data_source: str = None) -> Optional[Dict[str, Any]]:
    """
    按交易所获取美股列表
    
    Args:
        exchange: 交易所代码
            - 对于 sec 数据源: N=Nasdaq, A=NYSE, P=AMEX
            - 对于 yfinance 数据源: nasdaq, nyse, amex
        data_source: 指定数据源（sec, yfinance, intrinio），不指定则按优先级尝试
        
    Returns:
        包含美股股票列表的字典
    """
    try:
        print(f"开始获取 {exchange} 交易所的美股列表，数据源: {data_source if data_source else '按优先级尝试'}")
        
        # 如果指定了数据源，直接使用该数据源
        if data_source:
            if data_source == 'sec':
                from .sec_stocks import get_sec_stocks
                return get_sec_stocks(exchange)
            else:
                print(f"不支持的数据源: {data_source}")
                return None
        
        # 按优先级尝试各个数据源
        for source in US_DATA_SOURCES_CONFIG['default']:
            print(f"尝试使用 {source} 数据源...")
            
            if source == 'sec':
                from .sec_stocks import get_sec_stocks
                result = get_sec_stocks(exchange)
            else:
                continue
            
            if result and result['stocks']:
                print(f"{source} 数据源获取成功，共 {result['count']} 只股票")
                return result
            else:
                print(f"{source} 数据源获取失败，尝试下一个数据源...")
        
        print(f"所有数据源获取 {exchange} 交易所股票列表失败")
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
    