#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票市场数据服务模块
提供按市场获取所有股票列表的功能
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime


# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入各市场实现
from .cn.cn_stocks import get_cn_stocks
from .hk.hk_stocks import get_hk_stocks
from .us.us_stocks import get_us_stocks


def get_stock_by_market(marketcode: str) -> Optional[Dict[str, Any]]:
    """
    获取指定市场的所有股票列表
    
    Args:
        marketcode: 市场代码 ('cn', 'hk', 'us')
        
    Returns:
        包含股票列表的字典，格式为:
        {
            'market': marketcode,
            'count': 股票数量,
            'stocks': [
                {
                    'code': '股票代码',
                    'name': '股票名称',
                    'market': '市场代码',
                    'full_code': '完整代码',
                    'industry': '行业',
                    'list_date': '上市日期'
                },
                ...
            ],
            'timestamp': '数据时间戳'
        }
    """
    marketcode = marketcode.lower()
    
    if marketcode == 'cn':
        return get_cn_stocks()
    elif marketcode == 'hk':
        return get_hk_stocks()
    elif marketcode == 'us':
        return get_us_stocks()
    else:
        print(f"不支持的市场代码: {marketcode}")
        return None


def get_all_markets() -> List[str]:
    """
    获取所有支持的市场列表
    
    Returns:
        支持的市场代码列表
    """
    return ['cn', 'hk', 'us']


if __name__ == "__main__":
    # 测试代码
    for market in get_all_markets():
        print(f"测试市场: {market}")
        result = get_stock_by_market(market)
        if result:
            print(f"  获取到 {result['count']} 只股票")
            if result['stocks']:
                print(f"  第一只股票: {result['stocks'][0]}")
        else:
            print(f"  获取失败")