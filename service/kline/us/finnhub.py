#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finnhub数据源模块
用于从Finnhub API获取股票K线数据
注意：Finnhub API是免费的，但有调用限制只能获取实时数据，历史k线获取不到。，需要升级数据权限。
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

# 导入数据处理函数
from ..utils import process_kline_data


def is_finnhub_available() -> bool:
    """
    检查finnhub是否可用
    """
    try:
        import finnhub
        return True
    except ImportError:
        return False


def get_kline_data_from_finnhub(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    从Finnhub获取K线数据
    
    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型
        start_date: 开始日期
        end_date: 结束日期
        api_key: API密钥
        
    Returns:
        包含K线数据的字典
    """
    try:
        import finnhub
        
        # 初始化客户端
        client = finnhub.Client(api_key=api_key)
        
        # 将日期转换为时间戳
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        # 获取数据
        data = client.stock_candles(formatted_code, 'D', start_timestamp, end_timestamp)
        
        # 检查数据是否有效
        if data['s'] != 'ok':
            print(f"finnhub 数据源返回错误状态: {data['s']}")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(data['t'], unit='s'),
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v']
        })
        
        # 设置日期索引
        df.set_index('date', inplace=True)
        
        if df.empty:
            print(f"finnhub 数据源返回空数据")
            return None
        
        print(f"finnhub 数据源成功获取数据，数据形状: {df.shape}")
        
        # 处理数据
        processed_data = process_kline_data(df, 'finnhub')
        
        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "finnhub",
            "data": processed_data
        }
        
    except Exception as e:
        print(f"finnhub 数据源失败: {e}")
        return None


# 测试代码
if __name__ == "__main__":
    # 测试finnhub数据源
    print("测试finnhub数据源...")
    
    # 检查可用性
    print(f"finnhub可用: {is_finnhub_available()}")
    
    # 注意：需要设置API密钥才能实际测试
    # result = get_kline_data_from_finnhub(
    #     code="AAPL",
    #     formatted_code="AAPL",
    #     market_type="us",
    #     start_date="2024-01-01",
    #     end_date="2024-01-10",
    #     api_key="your_api_key_here"
    # )
    # print(f"测试结果: {result}")