#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yfinance数据源模块，注意需要vpn网络
使用openbb-yfinance库获取股票K线数据
{
  "code": "TSLA",
  "name": "特斯拉",
  "market": "US",
  "data_source": "yfinance",
  "data": [
    {
      "date": "2025-11-17",
      "open": 398.739990234375,
      "high": 423.9599914550781,
      "low": 398.739990234375,
      "close": 408.9200134277344,
      "volume": 102214300
    },
    {
      "date": "2025-11-18",
      "open": 405.3800048828125,
      "high": 408.8999938964844,
      "low": 393.7099914550781,
      "close": 401.25,
      "volume": 80688600
    }
  ]
}
"""

import asyncio
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
        'open': ['open', 'Open', 'OPEN', '开盘'],
        'high': ['high', 'High', 'HIGH', '最高'],
        'low': ['low', 'Low', 'LOW', '最低'],
        'close': ['close', 'Close', 'CLOSE', 'last', '收盘'],
        'volume': ['volume', 'Volume', 'VOLUME', 'vol', '成交量'],
        'date': ['date', 'Date', 'DATE', 'datetime', 'time', '日期']
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


def get_kline_data_from_yfinance(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    从yfinance获取K线数据（直接使用yfinance库）
    
    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型 (A, HK, US)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "yfinance",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    
    import time
    
    for attempt in range(5):  # 最多重试5次
        try:
            # 导入yfinance
            import yfinance as yf
            
            # 使用download方法获取数据
            data = yf.download(
                tickers=formatted_code,
                start=start_date,
                end=end_date,
                interval="1d",
                actions=False,
                auto_adjust=False,
                progress=False
            )
            
            if data is None or data.empty:
                print(f"yfinance 数据源返回空数据")
                return None
            
            print(f"yfinance 数据源成功获取数据，数据形状: {data.shape}")
            
            # 处理yfinance返回的多级列索引数据
            # yfinance返回的DataFrame列是元组形式，如('Close', 'AAPL')
            # 我们需要将其转换为单级列索引
            if isinstance(data.columns, pd.MultiIndex):
                # 提取第一级列名（价格类型）
                data = data.droplevel(level=1, axis=1)
                
            # 重命名列以匹配process_kline_data的期望
            column_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            # 只重命名存在的列
            data = data.rename(columns={col: column_mapping[col] for col in data.columns if col in column_mapping})
            
            # 重置索引，将日期列转换为普通列
            if data.index.name == 'Date':
                data = data.reset_index()
                # 重命名日期列
                data = data.rename(columns={'Date': 'date'})
            
            print(f"处理后的数据列: {data.columns.tolist()}")
            
            # 处理数据
            processed_data = process_kline_data(data, 'yfinance')
            
            return {
                "code": code,
                "formatted_code": formatted_code,
                "market": market_type,
                "data_source": "yfinance",
                "data": processed_data
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"yfinance 数据源失败 (尝试 {attempt + 1}/3): {error_msg}")
            
            # 如果是速率限制错误，等待一段时间后重试
            if "Too Many Requests" in error_msg or "Rate limited" in error_msg:
                wait_time = (attempt + 1) * 5  # 指数退避：5, 10, 15, 20, 25秒
                print(f"yfinance 速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            elif "No data found" in error_msg or "symbol may be delisted" in error_msg:
                # 股票代码错误或已退市，直接返回None
                print(f"yfinance 未找到数据，股票代码可能错误或已退市: {formatted_code}")
                return None
            else:
                # 其他错误，直接返回None
                return None
    
    # 所有重试都失败
    print(f"yfinance 数据源所有重试均失败")
    return None


def is_yfinance_available() -> bool:
    """检查yfinance是否可用（检查yfinance库）"""
    try:
        import yfinance
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"yfinance可用: {is_yfinance_available()}")
    
    # 测试获取数据
    result = get_kline_data_from_yfinance(
        code="TSLA",
        formatted_code="TSLA",
        market_type="US",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    
    if result:
        print(f"成功获取数据: {result['data_source']}, 数据条数: {len(result['data'])}")
    else:
        print("获取数据失败")