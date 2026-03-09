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
        # 注意：免费版API限制了outputsize='full'，使用'compact'只能获取最近100条数据
        # 如果需要获取更多数据，可能需要使用其他数据源或升级API Key
        try:
            # 优先尝试 compact 模式，因为 full 模式需要付费且更容易触发限流
            data, meta_data = ts.get_daily(symbol=formatted_code, outputsize='compact')
        except ValueError as e:
            raise e
        
        # 重命名列
        data = data.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        })
        
        # 转换索引为日期类型
        data.index = pd.to_datetime(data.index)
        
        # 尝试多种日期格式解析start_date和end_date
        date_formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        start_dt = None
        end_dt = None

        for date_format in date_formats:
            try:
                if start_dt is None:
                    start_dt = datetime.strptime(start_date, date_format)
                if end_dt is None:
                    end_dt = datetime.strptime(end_date, date_format)
            except ValueError:
                continue

        # 如果无法解析日期，使用默认值
        if start_dt is None:
            print(f"警告: 无法解析开始日期 {start_date}，使用默认值")
            start_dt = datetime.strptime('2000-01-01', '%Y-%m-%d')
        if end_dt is None:
            print(f"警告: 无法解析结束日期 {end_date}，使用默认值")
            end_dt = datetime.now()

        # 确保end_dt在start_dt之后
        if end_dt < start_dt:
            print(f"警告: 结束日期 {end_dt.strftime('%Y-%m-%d')} 早于开始日期 {start_dt.strftime('%Y-%m-%d')}，交换日期")
            start_dt, end_dt = end_dt, start_dt

        # 筛选日期范围
        # 注意：Alpha Vantage 返回的数据索引是 DatetimeIndex
        mask = (data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))
        data = data.loc[mask]

        if data.empty:
            print(f"alpha_vantage 数据源返回空数据 (日期范围: {start_date} - {end_date})")
            return None

        # 确保数据按日期升序排列
        data = data.sort_index(ascending=True)

        print(f"alpha_vantage 数据源成功获取数据，数据形状: {data.shape}")

        # 处理数据
        processed_data = []
        for date, row in data.iterrows():
            item = {
                "date": date.strftime('%Y-%m-%d'),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            }
            processed_data.append(item)

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
