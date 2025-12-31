#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eastmoney港股K线数据源模块
用于从东方财富API获取港股K线数据
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# 导入数据处理函数
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import process_kline_data


def get_kline_data_from_eastmoney_hk(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict[str, Any]]:
    """
    从东方财富API获取港股K线数据
    
    Args:
        code: 原始股票代码（如'00700'）
        formatted_code: 格式化后的股票代码（如'0700.HK'）
        market_type: 市场类型（应为'HK'）
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "eastmoney_hk",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    
    if market_type != 'HK':
        print(f"eastmoney_hk模块仅支持港股市场，不支持{market_type}市场")
        return None
    
    try:
        print(f"[eastmoney_hk] 正在获取港股 {code} K线数据...")
        
        # 东方财富港股K线API
        # 港股代码格式：116.HK -> 00116
        # 需要将代码转换为东方财富格式
        eastmoney_code = code.zfill(5)  # 港股代码补零到5位
        
        # 构建API URL
        url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        
        # 计算开始和结束时间戳（毫秒）
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 转换为YYYYMMDD格式
        beg_date = start_date.replace("-", "")
        end_date_formatted = end_date.replace("-", "")
        
        # API参数
        params = {
            "secid": f"116.{eastmoney_code}",  # 港股市场代码116
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",  # 日K线
            "fqt": "1",    # 前复权
            "beg": beg_date,
            "end": end_date_formatted,
            "lmt": "10000",  # 最大数据量
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rc") != 0:
            print(f"[eastmoney_hk] API返回错误: rc={data.get('rc')}, rt={data.get('rt', '未知错误')}")
            return None
        
        klines = data.get("data", {}).get("klines", [])
        
        if not klines:
            print(f"[eastmoney_hk] 未获取到K线数据")
            return None
        
        # 解析K线数据
        records = []
        for kline in klines:
            parts = kline.split(",")
            if len(parts) >= 11:
                record = {
                    "date": parts[0],  # 日期
                    "open": float(parts[1]),  # 开盘
                    "close": float(parts[2]),  # 收盘
                    "high": float(parts[3]),  # 最高
                    "low": float(parts[4]),  # 最低
                    "volume": float(parts[5]),  # 成交量
                    "amount": float(parts[6]),  # 成交额
                    "amplitude": float(parts[7]),  # 振幅
                    "pct_change": float(parts[8]),  # 涨跌幅
                    "change": float(parts[9]),  # 涨跌额
                    "turnover": float(parts[10])  # 换手率
                }
                records.append(record)
        
        # 转换为DataFrame
        df = pd.DataFrame(records)
        
        # 确保日期格式正确
        df["date"] = pd.to_datetime(df["date"])
        
        # 按日期排序
        df = df.sort_values("date")
        
        # 添加时间过滤：确保数据在请求的时间范围内
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
        
        if df.empty:
            print(f"[eastmoney_hk] 在指定时间范围内未找到数据: {start_date} 到 {end_date}")
            return None
        
        # 处理数据
        processed_data = process_kline_data(df, "eastmoney_hk")
        
        if not processed_data:
            print(f"[eastmoney_hk] 数据处理失败")
            return None
        
        result = {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "eastmoney_hk",
            "data": processed_data
        }
        
        print(f"[eastmoney_hk] 成功获取 {len(processed_data)} 条K线数据")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"[eastmoney_hk] 网络请求失败: {e}")
        return None
    except Exception as e:
        print(f"[eastmoney_hk] 获取K线数据时发生错误: {e}")
        return None


def is_eastmoney_hk_available() -> bool:
    """
    检查eastmoney_hk是否可用
    """
    # eastmoney不需要额外依赖，只需要requests库
    try:
        import requests
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    test_code = "00700"  # 腾讯
    test_formatted = "0700.HK"
    test_start = "2024-01-01"
    test_end = "2024-01-31"
    
    result = get_kline_data_from_eastmoney_hk(
        test_code, test_formatted, "HK", test_start, test_end
    )
    
    if result:
        print(f"测试成功: 获取到 {len(result['data'])} 条K线数据")
        print(f"数据源: {result['data_source']}")
        if result['data']:
            print(f"第一条数据: {result['data'][0]}")
            print(f"最后一条数据: {result['data'][-1]}")
    else:
        print("测试失败: 获取K线数据失败")