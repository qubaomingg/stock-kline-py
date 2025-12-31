#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试港股K线时间参数是否生效
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.kline import get_kline_data

print("=== 测试港股K线时间参数 ===")

# 测试港股股票 - 腾讯 (00700.HK)
print("\n1. 测试港股腾讯 (00700.HK) 时间参数")
print("   请求时间范围: 2025-10-01 到 2025-12-20")

result = get_kline_data(
    code="00700",
    start_date="2025-10-01",
    end_date="2025-12-20",
    data_sources=["eastmoney_hk", "akshare_hk"]
)

if result and "data" in result:
    data = result["data"]
    print(f"   成功获取 {len(data)} 条K线数据")
    if data:
        print(f"   第一条数据日期: {data[0]['date']}")
        print(f"   最后一条数据日期: {data[-1]['date']}")
        
        # 检查数据是否在请求的时间范围内
        import pandas as pd
        dates = [pd.to_datetime(d['date']) for d in data]
        min_date = min(dates)
        max_date = max(dates)
        
        print(f"   数据实际范围: {min_date.strftime('%Y-%m-%d')} 到 {max_date.strftime('%Y-%m-%d')}")
        
        # 检查是否有超出请求范围的数据
        request_start = pd.to_datetime("2025-10-01")
        request_end = pd.to_datetime("2025-12-20")
        
        if min_date < request_start:
            print(f"   ⚠️  警告: 有数据早于请求开始日期 ({min_date.strftime('%Y-%m-%d')} < {request_start.strftime('%Y-%m-%d')})")
        if max_date > request_end:
            print(f"   ⚠️  警告: 有数据晚于请求结束日期 ({max_date.strftime('%Y-%m-%d')} > {request_end.strftime('%Y-%m-%d')})")
        
        # 检查数据源
        print(f"   数据源: {result.get('data_source', 'unknown')}")
    else:
        print("   获取的数据为空")
else:
    print(f"   获取数据失败: {result}")

# 测试更短的时间范围
print("\n2. 测试港股腾讯 (00700.HK) 短时间范围")
print("   请求时间范围: 2025-12-01 到 2025-12-10")

result2 = get_kline_data(
    code="00700",
    start_date="2025-12-01",
    end_date="2025-12-10",
    data_sources=["eastmoney_hk", "akshare_hk"]
)

if result2 and "data" in result2:
    data2 = result2["data"]
    print(f"   成功获取 {len(data2)} 条K线数据")
    if data2:
        print(f"   第一条数据日期: {data2[0]['date']}")
        print(f"   最后一条数据日期: {data2[-1]['date']}")
        
        # 打印所有数据日期
        print("   所有数据日期:")
        for d in data2:
            print(f"     - {d['date']}")
    else:
        print("   获取的数据为空")
else:
    print(f"   获取数据失败: {result2}")

print("\n=== 测试完成 ===")