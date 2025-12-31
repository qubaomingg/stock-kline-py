#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eastmoney数据源模块 - A股K线数据
"""

from typing import Dict, List, Optional
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# 导入数据处理函数
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import process_kline_data

def get_kline_data_from_eastmoney_cn(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    从东方财富API获取A股K线数据
    
    Args:
        code: 原始股票代码 (如: '000001')
        formatted_code: 格式化后的股票代码 (如: '000001.SZ')
        market_type: 市场类型 (A)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        包含K线数据的字典
    """
    
    try:
        print(f"[eastmoney_cn] 正在获取A股 {code} K线数据...")
        
        # 确定市场后缀
        if code.startswith(('60', '68', '900')):
            secid = f"1.{code}"  # 上海
        elif code.startswith(('00', '30', '200')):
            secid = f"0.{code}"  # 深圳
        else:
            print(f"[eastmoney_cn] 无法识别的A股代码格式: {code}")
            return None
        
        # 东方财富K线API
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        
        # 计算开始和结束时间戳
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 东方财富API需要倒序时间戳
        klt = 101  # 日K线
        fqt = 1    # 前复权
        
        params = {
            "secid": secid,
            "klt": klt,
            "fqt": fqt,
            "beg": start_date.replace('-', ''),
            "end": end_date.replace('-', ''),
            "fields1": "f1,f2,f3,f4,f5",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "lmt": 10000  # 最大数据量
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('data') is None or data['data'].get('klines') is None:
            print(f"[eastmoney_cn] 获取K线数据失败: {data}")
            return None
        
        klines = data['data']['klines']
        
        if not klines:
            print(f"[eastmoney_cn] 没有获取到K线数据")
            return None
        
        print(f"[eastmoney_cn] 成功获取 {len(klines)} 条K线数据")
        
        # 解析数据
        records = []
        for kline in klines:
            parts = kline.split(',')
            if len(parts) >= 11:
                record = {
                    'date': parts[0],  # 日期
                    'open': float(parts[1]),  # 开盘
                    'close': float(parts[2]),  # 收盘
                    'high': float(parts[3]),  # 最高
                    'low': float(parts[4]),  # 最低
                    'volume': float(parts[5]),  # 成交量
                    'amount': float(parts[6]),  # 成交额
                    'amplitude': float(parts[7]),  # 振幅
                    'pct_change': float(parts[8]),  # 涨跌幅
                    'change': float(parts[9]),  # 涨跌额
                    'turnover': float(parts[10])  # 换手率
                }
                records.append(record)
        
        df = pd.DataFrame(records)
        
        # 处理数据
        processed_data = process_kline_data(df, 'eastmoney_cn')
        
        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "eastmoney_cn",
            "data": processed_data
        }
        
    except Exception as e:
        print(f"[eastmoney_cn] 获取K线数据时发生错误: {e}")
        return None


def is_eastmoney_cn_available() -> bool:
    """
    检查eastmoney_cn数据源是否可用
    
    Returns:
        如果eastmoney_cn数据源可用返回True，否则返回False
    """
    try:
        import requests
        return True
    except ImportError:
        return False


def get_kline_data_from_eastmoney_cn_with_env(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    使用环境变量配置的eastmoney数据源获取A股K线数据
    """
    return get_kline_data_from_eastmoney_cn(code, formatted_code, market_type, start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    result = get_kline_data_from_eastmoney_cn(
        code="000001",
        formatted_code="000001.SZ",
        market_type="A",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    if result:
        print(f"测试成功: 获取到 {len(result['data'])} 条K线数据")
        print(f"数据源: {result['data_source']}")
        if result['data']:
            print(f"第一条数据: {result['data'][0]}")
            print(f"最后一条数据: {result['data'][-1]}")
    else:
        print("测试失败: 获取K线数据失败")