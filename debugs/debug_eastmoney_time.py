#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试eastmoney_hk时间参数问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.hk.eastmoney_hk import get_kline_data_from_eastmoney_hk
from datetime import datetime

# 测试不同时间范围
test_cases = [
    {
        'code': '00700',
        'formatted_code': '0700.HK',
        'start_date': '2024-01-01',
        'end_date': '2024-01-10',
        'description': '短时间范围（10天）'
    },
    {
        'code': '00700',
        'formatted_code': '0700.HK',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'description': '一个月时间范围'
    },
    {
        'code': '00700',
        'formatted_code': '0700.HK',
        'start_date': '2023-12-01',
        'end_date': '2024-01-31',
        'description': '两个月时间范围'
    },
    {
        'code': '00700',
        'formatted_code': '0700.HK',
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'description': '一年时间范围'
    }
]

print("开始测试eastmoney_hk时间参数...")
print("=" * 60)

for i, test_case in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}: {test_case['description']}")
    print(f"股票代码: {test_case['code']}")
    print(f"时间范围: {test_case['start_date']} 到 {test_case['end_date']}")
    
    result = get_kline_data_from_eastmoney_hk(
        code=test_case['code'],
        formatted_code=test_case['formatted_code'],
        market_type='HK',
        start_date=test_case['start_date'],
        end_date=test_case['end_date']
    )
    
    if result:
        data_count = len(result['data'])
        print(f"✓ 成功获取 {data_count} 条数据")
        
        if data_count > 0:
            # 检查数据日期范围
            dates = [item['date'] for item in result['data']]
            min_date = min(dates)
            max_date = max(dates)
            print(f"  数据日期范围: {min_date} 到 {max_date}")
            
            # 检查是否在请求的时间范围内
            start_dt = datetime.strptime(test_case['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(test_case['end_date'], '%Y-%m-%d')
            
            min_dt = datetime.strptime(min_date, '%Y-%m-%d')
            max_dt = datetime.strptime(max_date, '%Y-%m-%d')
            
            if min_dt < start_dt:
                print(f"  ⚠ 警告: 最早数据日期 {min_date} 早于请求开始日期 {test_case['start_date']}")
            if max_dt > end_dt:
                print(f"  ⚠ 警告: 最晚数据日期 {max_date} 晚于请求结束日期 {test_case['end_date']}")
            
            # 显示前几条数据
            print(f"  前3条数据:")
            for j in range(min(3, data_count)):
                print(f"    {result['data'][j]}")
    else:
        print(f"✗ 获取数据失败")
    
    print("-" * 60)

print("\n测试完成！")