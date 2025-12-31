#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试港股数据格式
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak
import pandas as pd

print("=== 调试akshare港股数据格式 ===")

# 测试stock_hk_hist函数
print("\n1. 测试stock_hk_hist函数:")
try:
    data_hist = ak.stock_hk_hist(
        symbol="00700",
        period='daily',
        start_date='20251201',  # 2025-12-01
        end_date='20251210',    # 2025-12-10
        adjust='qfq'
    )
    print(f"   数据形状: {data_hist.shape}")
    print(f"   数据类型: {type(data_hist)}")
    if not data_hist.empty:
        print(f"   索引类型: {type(data_hist.index)}")
        print(f"   索引示例: {data_hist.index[:3] if len(data_hist) >= 3 else data_hist.index}")
        print(f"   列名: {data_hist.columns.tolist()}")
        print(f"   前3行数据:")
        print(data_hist.head(3))
    else:
        print("   数据为空")
except Exception as e:
    print(f"   调用失败: {e}")

# 测试stock_hk_daily函数
print("\n2. 测试stock_hk_daily函数:")
try:
    data_daily = ak.stock_hk_daily(
        symbol="00700",
        adjust='qfq'
    )
    print(f"   数据形状: {data_daily.shape}")
    print(f"   数据类型: {type(data_daily)}")
    if not data_daily.empty:
        print(f"   索引类型: {type(data_daily.index)}")
        print(f"   索引示例: {data_daily.index[:3] if len(data_daily) >= 3 else data_daily.index}")
        print(f"   列名: {data_daily.columns.tolist()}")
        print(f"   数据时间范围: {data_daily.index.min()} 到 {data_daily.index.max()}")
        
        # 测试过滤
        start_date = "2025-12-01"
        end_date = "2025-12-10"
        print(f"\n   测试过滤: {start_date} 到 {end_date}")
        print(f"   过滤前数据形状: {data_daily.shape}")
        
        # 尝试不同的过滤方法
        try:
            # 方法1: 直接字符串比较
            filtered1 = data_daily[(data_daily.index >= start_date) & (data_daily.index <= end_date)]
            print(f"   方法1过滤后形状: {filtered1.shape}")
        except Exception as e:
            print(f"   方法1过滤失败: {e}")
            
        try:
            # 方法2: 转换为datetime后比较
            data_daily.index = pd.to_datetime(data_daily.index)
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            filtered2 = data_daily[(data_daily.index >= start_dt) & (data_daily.index <= end_dt)]
            print(f"   方法2过滤后形状: {filtered2.shape}")
        except Exception as e:
            print(f"   方法2过滤失败: {e}")
            
    else:
        print("   数据为空")
except Exception as e:
    print(f"   调用失败: {e}")

print("\n=== 调试完成 ===")