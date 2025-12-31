#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的eastmoney_hk时间参数功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.kline.hk.eastmoney_hk import get_kline_data_from_eastmoney_hk
from datetime import datetime

# 测试用例
test_cases = [
    {
        'code': '00700',
        'formatted_code': '00700.HK',
        'market_type': 'HK',
        'start_date': '2024-01-01',
        'end_date': '2024-01-10',
        'expected_days': 7  # 2024-01-01到2024-01-10之间的交易日
    },
    {
        'code': '00700',
        'formatted_code': '00700.HK',
        'market_type': 'HK',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'expected_days': 22  # 2024年1月的交易日
    },
    {
        'code': '00700',
        'formatted_code': '00700.HK',
        'market_type': 'HK',
        'start_date': '2023-12-01',
        'end_date': '2024-01-31',
        'expected_days': 44  # 2023年12月到2024年1月的交易日
    },
]

def test_eastmoney_hk_time_params():
    print("=== 测试eastmoney_hk时间参数功能 ===")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['start_date']} 到 {test_case['end_date']}")
        
        result = get_kline_data_from_eastmoney_hk(
            code=test_case['code'],
            formatted_code=test_case['formatted_code'],
            market_type=test_case['market_type'],
            start_date=test_case['start_date'],
            end_date=test_case['end_date']
        )
        
        if result is None:
            print(f"  ❌ 测试失败: 未获取到数据")
            continue
            
        data = result.get('data', [])
        print(f"  获取到 {len(data)} 条数据")
        
        if len(data) > 0:
            # 检查数据日期范围
            dates = [item['date'] for item in data]
            min_date = min(dates)
            max_date = max(dates)
            print(f"  数据日期范围: {min_date} 到 {max_date}")
            
            # 验证是否在请求的时间范围内
            start_dt = datetime.strptime(test_case['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(test_case['end_date'], '%Y-%m-%d')
            
            min_dt = datetime.strptime(min_date, '%Y-%m-%d')
            max_dt = datetime.strptime(max_date, '%Y-%m-%d')
            
            if min_dt >= start_dt and max_dt <= end_dt:
                print(f"  ✅ 数据在请求的时间范围内")
                
                # 检查数据条数是否合理
                if len(data) <= test_case['expected_days']:
                    print(f"  ✅ 数据条数合理 ({len(data)} 条)")
                else:
                    print(f"  ⚠️  数据条数可能过多: {len(data)} 条 (预期最多 {test_case['expected_days']} 条)")
            else:
                print(f"  ❌ 数据超出请求的时间范围")
                print(f"     请求范围: {test_case['start_date']} 到 {test_case['end_date']}")
                print(f"     实际范围: {min_date} 到 {max_date}")
        else:
            print(f"  ⚠️  获取到0条数据")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_eastmoney_hk_time_params()