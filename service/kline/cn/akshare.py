#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
akshare数据源模块
用于从akshare获取A股和港股K线数据
{
  "code": "600519",
  "name": "茅台",
  "market": "A",
  "data_source": "akshare",
  "data": [
    {
      "date": "2025-11-21",
      "open": 1446.54,
      "high": 1456.04,
      "low": 1432.04,
      "close": 1442.64,
      "volume": 42607
    }
  ]
}
"""

from typing import Dict, List, Optional
import pandas as pd

# 导入数据处理函数
from ..utils import process_kline_data


def get_kline_data_from_akshare(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    从akshare获取K线数据
    
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
            "data_source": "akshare",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    
    try:
        import akshare as ak
    except ImportError:
        print("akshare未安装，无法使用akshare数据源")
        return None
    
    try:
        # 根据市场类型选择不同的akshare函数
        if market_type == 'A':
            # A股数据
            data = ak.stock_zh_a_hist(
                symbol=code,  # 使用原始代码，如'000001'
                period='daily',
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust='qfq'  # 前复权
            )
        elif market_type == 'HK':
            # 港股数据
            data = ak.stock_hk_hist(
                symbol=code,  # 使用原始代码，如'03690'
                period='daily',
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust='qfq'
            )
        else:
            print(f"akshare不支持 {market_type} 市场")
            return None
        
        if data is None or data.empty:
            print(f"akshare 数据源返回空数据")
            return None
            
        print(f"akshare 数据源成功获取数据，数据形状: {data.shape}")
        
        # 处理数据
        processed_data = process_kline_data(data, 'akshare')
        
        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "akshare",
            "data": processed_data
        }
        
    except Exception as e:
        print(f"akshare 数据源失败: {e}")
        return None


def is_akshare_available() -> bool:
    """检查akshare是否可用"""
    try:
        import akshare
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"akshare可用: {is_akshare_available()}")
    
    # 测试获取A股数据
    result = get_kline_data_from_akshare(
        code="000001",
        formatted_code="000001.SZ",
        market_type="A",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    
    if result:
        print(f"成功获取A股数据: {result['data_source']}, 数据条数: {len(result['data'])}")
    else:
        print("获取A股数据失败")
    
    # 测试获取港股数据
    result = get_kline_data_from_akshare(
        code="03690",
        formatted_code="03690.HK",
        market_type="HK",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    
    if result:
        print(f"成功获取港股数据: {result['data_source']}, 数据条数: {len(result['data'])}")
    else:
        print("获取港股数据失败")