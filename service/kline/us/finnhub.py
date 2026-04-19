#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finnhub数据源模块
使用finnhub库获取美股K线数据
{
  "code": "AAPL",
  "name": "Apple Inc.",
  "market": "US",
  "data_source": "finnhub",
  "data": [
    {
      "date": "2025-11-17",
      "open": 398.739990234375,
      "high": 423.9599914550781,
      "low": 398.739990234375,
      "close": 408.9200134277344,
      "volume": 102214300
    }
  ]
}
"""

from typing import Dict, List, Optional
import pandas as pd


def process_kline_data(data: pd.DataFrame, source: str) -> List[Dict]:
    """
    处理K线数据，统一格式

    Args:
        data: 原始数据DataFrame
        source: 数据源名称

    Returns:
        处理后的数据列表
    """
    if data.empty:
        return []

    # 确保有日期列
    if 'date' not in data.columns and data.index.name == 'date':
        data = data.reset_index()

    # 统一列名映射
    column_mapping = {
        'open': ['open', 'Open', 'OPEN', 'o'],
        'high': ['high', 'High', 'HIGH', 'h'],
        'low': ['low', 'Low', 'LOW', 'l'],
        'close': ['close', 'Close', 'CLOSE', 'c'],
        'volume': ['volume', 'Volume', 'VOLUME', 'v'],
        'date': ['date', 'Date', 'DATE', 'datetime', 'time', 't']
    }

    # 重命名列
    for target_col, possible_cols in column_mapping.items():
        for col in possible_cols:
            if col in data.columns:
                if col != target_col:
                    data = data.rename(columns={col: target_col})
                break

    # 确保必要的列存在
    required_cols = ['date', 'open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            print(f"警告: {source} 数据源缺少 {col} 列")
            return []

    # 转换日期格式
    data['date'] = pd.to_datetime(data['date'])

    # 转换为字典列表
    result = []
    for _, row in data.iterrows():
        item = {
            'date': row['date'].strftime('%Y-%m-%d'),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        }

        # 添加成交量（如果有）
        if 'volume' in data.columns:
            item['volume'] = int(row['volume']) if pd.notna(row['volume']) else 0

        result.append(item)

    return result


def get_kline_data_from_finnhub(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    api_key: str
) -> Optional[Dict]:
    """
    从finnhub获取K线数据

    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型 (A, HK, US)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        api_key: Finnhub API Key

    Returns:
        包含K线数据的字典
        如果获取失败则返回None
    """

    try:
        import finnhub
        import time
        from datetime import datetime

        # 初始化finnhub客户端
        client = finnhub.Client(api_key=api_key)

        # 转换日期为时间戳（秒）
        def date_to_timestamp(date_str):
            """将日期字符串转换为时间戳"""
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return int(dt.timestamp())

        start_timestamp = date_to_timestamp(start_date)
        end_timestamp = date_to_timestamp(end_date)

        print(f"finnhub 转换日期: {start_date} -> {start_timestamp}, {end_date} -> {end_timestamp}")

        # 获取股票代码（去掉后缀）
        ticker = formatted_code.split('.')[0] if '.' in formatted_code else formatted_code

        # 获取K线数据
        # Finnhub 的 stock_candles 返回格式:
        # {
        #   "c": [close prices],
        #   "h": [high prices],
        #   "l": [low prices],
        #   "o": [open prices],
        #   "s": "ok" or "no_data",
        #   "t": [timestamps],
        #   "v": [volumes]
        # }
        result = client.stock_candles(
            symbol=ticker,
            resolution='D',  # 日线
            _from=start_timestamp,
            to=end_timestamp
        )

        if result.get('s') != 'ok':
            print(f"finnhub 数据源返回状态: {result.get('s')}")
            return None

        # 转换为DataFrame
        data = pd.DataFrame({
            'date': pd.to_datetime(result['t'], unit='s'),
            'open': result['o'],
            'high': result['h'],
            'low': result['l'],
            'close': result['c'],
            'volume': result['v']
        })

        print(f"finnhub 数据源成功获取数据，数据条数: {len(data)}")

        # 处理数据
        processed_data = process_kline_data(data, 'finnhub')

        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "finnhub",
            "data": processed_data
        }

    except Exception as e:
        error_msg = str(e)
        print(f"finnhub 数据源失败: {error_msg}")
        return None


def is_finnhub_available() -> bool:
    """检查finnhub是否可用（检查finnhub库）"""
    try:
        import finnhub
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"finnhub可用: {is_finnhub_available()}")

    # 测试获取数据
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv('FINNHUB_API_KEY', '')

    if api_key:
        result = get_kline_data_from_finnhub(
            code="AAPL",
            formatted_code="AAPL",
            market_type="us",
            start_date="2024-01-01",
            end_date="2024-01-10",
            api_key=api_key
        )

        if result:
            print(f"成功获取数据: {result['data_source']}, 数据条数: {len(result['data'])}")
        else:
            print("获取数据失败")
    else:
        print("未设置 FINNHUB_API_KEY")
