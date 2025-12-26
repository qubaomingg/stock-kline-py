#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha Vantage数据源模块
用于从Alpha Vantage API获取股票K线数据
{
  "code": "TSLA",
  "name": "特斯拉",
  "market": "US",
  "data_source": "alpha_vantage",
  "data": [
    {
      "date": "2025-12-15",
      "open": 469.44,
      "high": 481.7694,
      "low": 467.66,
      "close": 475.31,
      "volume": 114542204
    },
    {
      "date": "2025-12-12",
      "open": 448.09,
      "high": 463.01,
      "low": 441.67,
      "close": 458.96,
      "volume": 95656749
    }
  ]
}
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

# 导入数据处理函数
from ..utils import process_kline_data


def is_alpha_vantage_available() -> bool:
    """
    检查alpha_vantage是否可用
    """
    try:
        from alpha_vantage.timeseries import TimeSeries
        return True
    except ImportError:
        return False


def get_kline_data_from_alpha_vantage(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    从Alpha Vantage获取K线数据
    
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
        from alpha_vantage.timeseries import TimeSeries
        
        # 初始化客户端
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # 获取数据
        data, meta_data = ts.get_daily(symbol=formatted_code, outputsize='compact')
        
        # 重命名列
        data = data.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        })
        
        # 筛选日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        data = data[(data.index >= start_dt) & (data.index <= end_dt)]
        
        if data.empty:
            print(f"alpha_vantage 数据源返回空数据")
            return None
        
        print(f"alpha_vantage 数据源成功获取数据，数据形状: {data.shape}")
        
        # 处理数据
        processed_data = process_kline_data(data, 'alpha_vantage')
        
        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "alpha_vantage",
            "data": processed_data
        }
        
    except Exception as e:
        print(f"alpha_vantage 数据源失败: {e}")
        return None


# 测试代码
if __name__ == "__main__":
    # 测试alpha_vantage数据源
    print("测试alpha_vantage数据源...")
    
    # 检查可用性
    print(f"alpha_vantage可用: {is_alpha_vantage_available()}")
    
    # 注意：需要设置API密钥才能实际测试
    # result = get_kline_data_from_alpha_vantage(
    #     code="AAPL",
    #     formatted_code="AAPL",
    #     market_type="us",
    #     start_date="2024-01-01",
    #     end_date="2024-01-10",
    #     api_key="your_api_key_here"
    # )
    # print(f"测试结果: {result}")